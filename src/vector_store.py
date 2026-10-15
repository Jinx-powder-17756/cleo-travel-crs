from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import faiss
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer

EMBEDDING_MODEL = "text-embedding-004"

# Canonical city aliases in Egyptian tourism
CITY_ALIASES = {
    "cairo": ["cairo", "giza"],
    "giza": ["giza", "cairo"],
    "luxor": ["luxor", "qena", "upper egypt"],
    "qena": ["qena", "luxor", "upper egypt"],
    "sohag": ["sohag", "upper egypt"],
    "aswan": ["aswan", "kom ombo", "edfu", "upper egypt"],
    "kom ombo": ["kom ombo", "aswan", "upper egypt"],
    "edfu": ["edfu", "aswan", "upper egypt"],
    "alexandria": ["alexandria", "mediterranean coast"],
    "north coast": ["north coast", "el alamein", "marsa matrouh", "alexandria"],
    "el alamein": ["el alamein", "north coast"],
    "marsa matrouh": ["marsa matrouh", "north coast", "mediterranean coast"],
    "sharm el-sheikh": ["sharm el-sheikh"],
    "sharm": ["sharm el-sheikh"],
    "dahab": ["dahab"],
    "nuweiba": ["nuweiba", "sinai peninsula"],
    "st. catherine": ["st. catherine", "sinai peninsula"],
    "taba": ["taba", "sinai peninsula"],
    "sinai": ["sharm el-sheikh", "dahab", "nuweiba", "st. catherine", "taba", "sinai peninsula"],
    "hurghada": ["hurghada", "el gouna", "red sea coast"],
    "el gouna": ["el gouna", "hurghada", "red sea coast"],
    "marsa alam": ["marsa alam", "red sea coast"],
    "safaga": ["safaga", "red sea coast"],
    "red sea": ["hurghada", "el gouna", "marsa alam", "safaga", "sharm el-sheikh", "dahab", "red sea coast"],
    "siwa": ["siwa", "western desert"],
    "farafra": ["farafra", "western desert"],
    "white desert": ["farafra", "western desert"],
    "bahariya": ["bahariya", "western desert"],
    "dakhla": ["dakhla", "western desert"],
    "fayoum": ["fayoum", "western desert"],
    "western desert": ["siwa", "farafra", "bahariya", "dakhla", "fayoum", "western desert"],
    "port said": ["port Said", "suez canal"],
    "rosetta": ["rosetta", "delta coast", "delta"],
    "sharkia": ["sharkia", "delta"]
}


class LandmarkVectorStore:
    """
    Dense Vector Search & FAISS Index for Egyptian Landmarks.
    Embeds landmark descriptions & metadata, indexes via FAISS (Cosine Similarity),
    and supports both Gemini text-embedding-004 and an offline fallback embedder.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        client: Optional[genai.Client] = None,
        cache_path: Optional[str] = None,
    ):
        self.df = df
        self.client = client
        if cache_path is None:
            cache_path = str(Path(__file__).resolve().parent.parent / "data" / "landmark_embeddings.npz")
        self.cache_path = cache_path

        self.documents: List[Dict[str, Any]] = []
        self._build_documents()

        self.embeddings: np.ndarray = np.array([])
        self.index: Optional[faiss.IndexFlatIP] = None
        self.dimension: int = 0
        self.is_gemini_embedded: bool = False

        self._initialize_index()

    def _build_documents(self) -> None:
        """Prepares metadata and rich semantic text representation for each landmark."""
        self.documents = []
        for _, row in self.df.iterrows():
            rich_text = (
                f"{row['landmark_name']} in {row['city']}, {row['region']}. "
                f"Category: {row['category']}. "
                f"Description: {row['description']} "
                f"Tags: {row['tags']}. Ideal for: {row['ideal_for']}."
            )
            price_tier = str(row.get("price_tier", "$$")) if pd.notna(row.get("price_tier")) else "$$"
            district = str(row.get("district", row["city"])) if pd.notna(row.get("district")) else str(row["city"])
            self.documents.append({
                "id": row["id"],
                "landmark_name": str(row["landmark_name"]),
                "city": str(row["city"]),
                "region": str(row["region"]),
                "district": district,
                "category": str(row["category"]),
                "description": str(row["description"]),
                "tags": str(row["tags"]),
                "ideal_for": str(row["ideal_for"]),
                "typical_duration_hours": float(row.get("typical_duration_hours", 2.0)) if pd.notna(row.get("typical_duration_hours")) else 2.0,
                "price_tier": price_tier,
                "rich_text": rich_text,
            })

    def _initialize_index(self) -> None:
        """Loads cached embeddings or computes them and builds the FAISS index."""
        # Check cache on disk
        if os.path.exists(self.cache_path):
            try:
                data = np.load(self.cache_path, allow_pickle=True)
                cached_embeddings = data["embeddings"]
                if len(cached_embeddings) == len(self.documents):
                    self.embeddings = cached_embeddings.astype("float32")
                    self.dimension = self.embeddings.shape[1]
                    self.is_gemini_embedded = bool(data.get("is_gemini", False))
                    self._create_faiss_index()
                    return
            except Exception:
                pass

        # Compute embeddings
        if self.client:
            try:
                self._compute_gemini_embeddings()
                return
            except Exception:
                pass

        # Fallback to dense normalized TF-IDF representations
        self._compute_offline_dense_embeddings()

    def _create_faiss_index(self) -> None:
        """Builds a normalized FAISS Inner Product (Cosine Similarity) index."""
        # Normalize vectors for cosine similarity via IndexFlatIP
        faiss.normalize_L2(self.embeddings)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(self.embeddings)

    def _compute_gemini_embeddings(self) -> None:
        """Generates dense vector embeddings using Gemini text-embedding-004."""
        texts = [doc["rich_text"] for doc in self.documents]
        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
        )
        vectors = [emb.values for emb in response.embeddings]
        self.embeddings = np.array(vectors, dtype="float32")
        self.dimension = self.embeddings.shape[1]
        self.is_gemini_embedded = True

        self._create_faiss_index()
        self._save_cache()

    def _compute_offline_dense_embeddings(self) -> None:
        """Fallback deterministic dense semantic representations (zero API dependency)."""
        texts = [doc["rich_text"] for doc in self.documents]
        self.offline_vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2500)
        sparse_mat = self.offline_vectorizer.fit_transform(texts)
        self.embeddings = sparse_mat.toarray().astype("float32")
        self.dimension = self.embeddings.shape[1]
        self.is_gemini_embedded = False

        self._create_faiss_index()

    def _save_cache(self) -> None:
        """Saves embeddings to disk."""
        try:
            np.savez_compressed(
                self.cache_path,
                embeddings=self.embeddings,
                is_gemini=self.is_gemini_embedded
            )
        except Exception:
            pass

    def embed_query(self, query_text: str) -> np.ndarray:
        """Embeds a user search query into vector space."""
        if self.client and self.is_gemini_embedded:
            try:
                response = self.client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=query_text,
                )
                q_vec = np.array([response.embeddings[0].values], dtype="float32")
                faiss.normalize_L2(q_vec)
                return q_vec
            except Exception:
                pass

        # Offline fallback
        if hasattr(self, "offline_vectorizer"):
            q_vec = self.offline_vectorizer.transform([query_text]).toarray().astype("float32")
            faiss.normalize_L2(q_vec)
            return q_vec
        else:
            # If loaded from cache but no client, re-run offline fallback
            self._compute_offline_dense_embeddings()
            return self.embed_query(query_text)

    def _extract_negative_keywords(self, constraints: List[str]) -> List[str]:
        """Cleans and extracts actionable exclusion keywords from user negative constraints."""
        stop_words = {"no", "not", "avoid", "dont", "don't", "without", "spots", "places", "things", "any", "i", "want", "more", "too", "spot", "place"}
        terms = []
        for c in constraints:
            words = c.lower().replace("-", " ").replace("/", " ").split()
            filtered = [w.strip(".,!?\"'") for w in words if w.strip(".,!?\"'") not in stop_words and len(w.strip(".,!?\"'")) > 2]
            if filtered:
                terms.extend(filtered)
            elif c.strip():
                terms.append(c.lower().strip())
        return list(set(terms))

    def _matches_negative_constraints(self, doc: Dict[str, Any], negative_terms: List[str]) -> bool:
        """Checks if a landmark contains counter-indicated keywords in name, category, tags, or description."""
        if not negative_terms:
            return False
        content = f"{doc['landmark_name']} {doc['category']} {doc['tags']} {doc['description']} {doc['ideal_for']}".lower()
        for term in negative_terms:
            # Match singular/plural and root occurrences
            if term in content:
                return True
            # Also check if term ends with 's' or vice versa
            if term.endswith("s") and len(term) > 3 and term[:-1] in content:
                return True
        return False

    def search(
        self,
        query_text: str,
        top_k: int = 4,
        target_city: Optional[str] = None,
        exclude_names: Optional[List[str]] = None,
        negative_constraints: Optional[List[str]] = None,
        price_preference: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes Dense Vector Similarity Search using FAISS with metadata filtering:
        - City & regional alias filtering
        - Dynamic negative constraint exclusion (counter-indication filtering)
        - Price tier budget matching
        """
        exclude_set = set(exclude_names or [])
        neg_terms = self._extract_negative_keywords(negative_constraints or [])
        q_vec = self.embed_query(query_text)

        # Retrieve all candidates ranked by dense cosine similarity
        k_search = len(self.documents)
        scores, indices = self.index.search(q_vec, k_search)
        scores = scores[0]
        indices = indices[0]

        valid_cities = None
        if target_city:
            c_low = target_city.lower().strip()
            valid_cities = CITY_ALIASES.get(c_low, [c_low])

        matched_candidates = []
        soft_penalized_candidates = []

        price_ranks = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
        is_budget_preferred = False
        is_luxury_preferred = False
        if price_preference:
            p_low = price_preference.lower()
            if any(w in p_low for w in ["$", "budget", "cheap", "backpacker", "economic", "free"]):
                is_budget_preferred = True
            elif any(w in p_low for w in ["$$$$", "luxury", "upscale", "vip", "exclusive"]):
                is_luxury_preferred = True

        for rank, doc_idx in enumerate(indices):
            doc = self.documents[doc_idx]
            landmark_name = doc["landmark_name"]
            landmark_city = doc["city"].lower()
            landmark_region = doc["region"].lower()
            sim_score = float(scores[rank])

            # Exclusion filter
            if landmark_name in exclude_set and len(self.documents) > len(exclude_set) + top_k:
                continue

            # City match check
            if valid_cities:
                is_city_match = any(vc in landmark_city or vc in landmark_region for vc in valid_cities if vc)
                if not is_city_match:
                    continue

            # Check negative constraints (counter-indications)
            violates_negative = self._matches_negative_constraints(doc, neg_terms)

            # Price tier check
            doc_tier = doc.get("price_tier", "$$")
            doc_price_rank = price_ranks.get(doc_tier, 2)
            violates_price = False
            if is_budget_preferred and doc_price_rank >= 4:
                violates_price = True
            elif is_luxury_preferred and doc_price_rank <= 1:
                violates_price = True

            cand = dict(doc)
            cand["score"] = round(max(sim_score, 0.0), 3)

            if violates_negative:
                # Save as soft penalized backup in case all items in a small city match
                cand["score"] = max(0.0, cand["score"] - 0.5)
                soft_penalized_candidates.append(cand)
                continue

            if violates_price:
                cand["score"] = max(0.0, cand["score"] - 0.2)
                soft_penalized_candidates.append(cand)
                continue

            matched_candidates.append(cand)
            if len(matched_candidates) >= top_k:
                break

        # If strict filtering left fewer than requested results, fill with soft penalized candidates
        if len(matched_candidates) < top_k and soft_penalized_candidates:
            needed = top_k - len(matched_candidates)
            matched_candidates.extend(soft_penalized_candidates[:needed])

        return matched_candidates
