from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from google import genai

from src.vector_store import LandmarkVectorStore, CITY_ALIASES


class EgyptianLandmarksDataset:
    """
    Manages the Egyptian landmark catalogue and provides FAISS dense vector RAG retrieval.
    """

    def __init__(
        self,
        csv_path: Optional[str] = None,
        client: Optional[genai.Client] = None,
        cache_path: Optional[str] = None,
    ):
        if csv_path is None:
            csv_path = str(Path(__file__).resolve().parent.parent / "data" / "egyptian_landmarks.csv")
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.client = client

        # Initialize FAISS Dense Vector Store
        self.vector_store = LandmarkVectorStore(
            df=self.df,
            client=self.client,
            cache_path=cache_path,
        )

    def set_client(self, client: genai.Client) -> None:
        """Updates Gemini client and re-indexes embeddings if needed."""
        self.client = client
        self.vector_store.client = client
        if not self.vector_store.is_gemini_embedded:
            self.vector_store._initialize_index()

    def get_all_landmarks(self) -> pd.DataFrame:
        """Returns the complete landmark dataset."""
        return self.df

    def retrieve_candidates(
        self,
        session_state: Any,
        top_k: int = 4,
        exclude_recommended: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant landmark candidates using Dense Vector Search (FAISS)
        over landmark descriptions and tags, conditioned on target city constraints,
        negative constraints, and price tier preferences.
        """
        negative_constraints: List[str] = []
        price_pref: Optional[str] = None

        if hasattr(session_state, "to_dict"):
            data = session_state.to_dict()
            interests = list(data.get("interests", []))
            target_city_val = data.get("target_city")
            budget_val = data.get("budget_or_style")
            negative_constraints = list(data.get("negative_constraints", []))
            price_pref = data.get("price_preference")
            recommended = getattr(session_state, "recommended_landmarks", [])
        elif isinstance(session_state, dict):
            interests = list(session_state.get("interests", session_state.get("accumulated_interests", [])))
            target_city_val = session_state.get("target_city")
            budget_val = session_state.get("budget_or_style")
            negative_constraints = list(session_state.get("negative_constraints", []))
            price_pref = session_state.get("price_preference")
            recommended = session_state.get("recommended_landmarks", [])
        else:
            interests = list(getattr(session_state, "accumulated_interests", []))
            target_city_val = getattr(session_state, "target_city", None)
            budget_val = getattr(session_state, "budget_or_style", None)
            negative_constraints = list(getattr(session_state, "negative_constraints", []))
            price_pref = getattr(session_state, "price_preference", None)
            recommended = getattr(session_state, "recommended_landmarks", [])

        # Construct dense semantic query
        query_parts = [str(i) for i in interests if str(i).strip()]
        if budget_val:
            query_parts.append(str(budget_val))

        search_query = " ".join(query_parts).strip()
        if not search_query:
            search_query = "historical landmarks monuments culture nature"

        exclude_list = recommended if exclude_recommended else []

        # Execute FAISS vector search with negative constraint and price tier filtering
        return self.vector_store.search(
            query_text=search_query,
            top_k=top_k,
            target_city=target_city_val,
            exclude_names=exclude_list,
            negative_constraints=negative_constraints,
            price_preference=price_pref,
        )

    def format_candidates_as_context(self, candidates: List[Dict[str, Any]]) -> str:
        """Formats candidate landmarks into a clean prompt context block."""
        if not candidates:
            return "No matching landmarks found in catalog."

        lines = []
        for i, c in enumerate(candidates, 1):
            score_info = f" (Similarity: {c.get('score', 1.0):.2f})" if 'score' in c else ""
            lines.append(
                f"[{i}] {c['landmark_name']} ({c['city']}, {c['region']}){score_info}\n"
                f"    Category: {c['category']}\n"
                f"    Tags: {c['tags']}\n"
                f"    Ideal for: {c['ideal_for']}\n"
                f"    Detailed Description: {c['description']}\n"
            )
        return "\n".join(lines)
