from __future__ import annotations

import io
import os
import json
from typing import Optional, List, Dict, Any
from PIL import Image
from google import genai
from google.genai import types

from src.config import get_gemini_client, DEFAULT_MODEL
from src.schemas import (
    ExtractedPreferences,
    MatchedLandmark,
    AgentRecommendationResponse,
    UserSession,
)
from src.dataset import EgyptianLandmarksDataset


def prepare_image_part(image: Any) -> Optional[types.Part]:
    """Serializes various image formats into a google-genai types.Part object."""
    if image is None:
        return None
    if isinstance(image, types.Part):
        return image
    if hasattr(image, "read"):
        # UploadedFile or file-like
        data = image.read()
        if hasattr(image, "seek"):
            image.seek(0)
        mime_type = getattr(image, "type", "image/jpeg") or "image/jpeg"
        return types.Part.from_bytes(data=data, mime_type=mime_type)
    if isinstance(image, bytes):
        return types.Part.from_bytes(data=image, mime_type="image/jpeg")
    if isinstance(image, str) and os.path.exists(image):
        with open(image, "rb") as f:
            data = f.read()
        mime = "image/png" if image.lower().endswith(".png") else "image/jpeg"
        return types.Part.from_bytes(data=data, mime_type=mime)
    if isinstance(image, Image.Image):
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")
    return None


class EgyptianTravelAgent:
    """
    Two-step Conversational Recommender System (CRS) Agent for Egyptian Tourism:
    1. Dynamic fine-grained multimodal preference extraction (text + image) with Pydantic JSON schema.
    2. Stateful UserSession memory accumulation & FAISS candidate retrieval.
    3. Grounded, explainable recommendation generation using landmark descriptions.
    """

    def __init__(
        self,
        client: Optional[genai.Client] = None,
        model_name: str = DEFAULT_MODEL,
        dataset: Optional[EgyptianLandmarksDataset] = None,
    ):
        self.client = client or get_gemini_client()
        self.model_name = model_name
        self.dataset = dataset or EgyptianLandmarksDataset(client=self.client)

    def process_turn(
        self,
        user_message: str,
        session: UserSession,
        image: Optional[Any] = None,
    ) -> AgentRecommendationResponse:
        """
        Executes an end-to-end multimodal conversational turn:
        1. Extract preferences from user query and optional image.
        2. Update stateful user profile in session.
        3. Retrieve grounded landmark candidates using dense vector search.
        4. Generate explainable recommendations and conversational reply.
        """
        # Step 1: Multimodal Preference Extraction
        extracted = self.extract_preferences(user_message, session, image=image)

        # Step 2: Accumulate into UserSession State
        session.update_profile(extracted)
        session.add_message("user", user_message)

        # Step 3: Grounded Landmark Retrieval (FAISS RAG)
        candidates = self.dataset.retrieve_candidates(session, top_k=3)

        # Step 4: Explainable Recommendation Generation
        response = self.generate_recommendations(user_message, session, candidates, extracted, has_image=bool(image))

        # Record recommended landmark names to prevent repetitive loops
        for rec in response.recommendations:
            session.record_recommendation(rec.landmark_name)
        session.add_message("assistant", response.conversational_reply)

        return response

    def extract_preferences(
        self,
        user_message: str,
        session: UserSession,
        image: Optional[Any] = None,
    ) -> ExtractedPreferences:
        """
        Extracts fine-grained user preferences into the Pydantic schema using Gemini structured outputs.
        Supports multimodal image input (identifying Egyptian landmarks or aesthetic preferences).
        """
        image_part = prepare_image_part(image)

        if not self.client:
            return self._heuristic_extract_preferences(user_message, image=image)

        profile = session.to_dict()
        interests_str = ", ".join(profile.get("interests", [])) or "None"
        city_str = profile.get("target_city") or "Unspecified"
        style_str = profile.get("budget_or_style") or "Unspecified"

        text_prompt = (
            f"Active Session Context:\n"
            f"- Accumulated Interests: {interests_str}\n"
            f"- Current Destination City: {city_str}\n"
            f"- Travel Style/Vibe: {style_str}\n\n"
            f"User Latest Message: \"{user_message}\"\n\n"
        )

        if image_part:
            text_prompt += (
                "An image has been attached by the user.\n"
                "1. If this image clearly depicts or resembles a specific Egyptian landmark or destination (e.g. Citadel, Pyramids, Luxor temples, Red Sea corals, Siwa salt lake), "
                "identify it and set `target_city` accordingly.\n"
                "2. Extract visual aesthetic vibes and activities visible in the photo into `new_interests` (e.g. 'coastal fortress', 'coral reef diving', 'ancient columns', 'desert safari', 'bazaar shopping').\n"
                "3. Extract travel style into `budget_or_style` if implied.\n"
            )
        else:
            text_prompt += "Extract any newly stated tourist interests, destination cities (in Egypt), or travel style."

        system_instruction = (
            "You are an expert tourist intent and visual analyzer for an Egyptian tourism recommender system. "
            "Analyze the user's text and any provided photo. Extract fine-grained travel preferences into structured JSON. "
            "Normalize interests (e.g., 'pharaonic', 'diving', 'snorkeling', 'ancient history', 'food', 'markets', 'relaxation', 'desert', 'coastal'). "
            "Detect negative constraints or counter-indications when user wants to exclude, avoid, or dislikes something "
            "(e.g., 'no museums' -> ['museum'], 'avoid crowded spots' -> ['crowded'], 'no hiking' -> ['hiking']). "
            "Detect price preferences ('$', '$$', '$$$', '$$$$', or keywords like 'budget', 'luxury'). "
            "Only identify target_city if an Egyptian city or region is mentioned or visually recognized (e.g., Cairo, Luxor, Alexandria, Sharm El-Sheikh, Aswan, Giza, Dahab, Siwa, Hurghada). "
            "Do not hallucinate cities not in Egypt."
        )

        contents: List[Any] = []
        if image_part:
            contents.append(image_part)
        contents.append(text_prompt)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ExtractedPreferences,
                    temperature=0.1,
                ),
            )
            data = json.loads(response.text)
            return ExtractedPreferences.model_validate(data)
        except Exception:
            return self._heuristic_extract_preferences(user_message, image=image)

    def generate_recommendations(
        self,
        user_message: str,
        session: UserSession,
        candidates: List[Dict[str, Any]],
        extracted: ExtractedPreferences,
        has_image: bool = False,
    ) -> AgentRecommendationResponse:
        """
        Generates grounded, explainable recommendations referencing the landmark catalog.
        """
        if not self.client:
            return self._heuristic_generate_response(session, candidates, extracted, has_image=has_image)

        candidate_context = self.dataset.format_candidates_as_context(candidates)
        profile = session.to_dict()
        interests_str = ", ".join(profile.get("interests", [])) or "None"
        city_str = profile.get("target_city") or "Flexible / Unspecified"
        style_str = profile.get("budget_or_style") or "Unspecified"

        image_note = "Note: The user provided a reference photo alongside their query. Acknowledge this photo and connect the recommended sites with the visual vibe." if has_image else ""

        prompt = (
            f"=== CURRENT USER SESSION STATE ===\n"
            f"• Target Destination: {city_str}\n"
            f"• Interests: {interests_str}\n"
            f"• Travel Style/Vibe: {style_str}\n\n"
            f"=== USER LATEST INPUT ===\n"
            f"User said: \"{user_message}\"\n"
            f"{image_note}\n"
            f"Extracted in this turn: {extracted.model_dump_json()}\n\n"
            f"=== RETRIEVED GROUNDED LANDMARK CANDIDATES FROM CATALOG ===\n"
            f"{candidate_context}\n\n"
            f"=== INSTRUCTIONS ===\n"
            f"1. Generate a warm, hospitable conversational reply welcoming the traveler to Egypt ('Ahlan wa Sahlan').\n"
            f"2. Select the most relevant landmark(s) from the RETRIEVED CANDIDATES ONLY.\n"
            f"3. For each recommended landmark, provide an EXPLAINABLE rationale in `why_matched` directly referencing "
            f"how its specific historical details, architecture, or activities in its description match the user's preferences.\n"
            f"4. Provide practical insider advice in `highlight_tip`.\n"
            f"5. Formulate an engaging `suggested_follow_up` question to keep the conversational discovery flow active."
        )

        system_instruction = (
            "You are 'Cleo', an elite, warm, and highly knowledgeable Egyptian travel concierge and licensed guide. "
            "Your recommendations must be strictly grounded in the provided landmark descriptions. "
            "Always explain WHY each landmark specifically fits the traveler's stated interests, visual aesthetics, or travel vibe. "
            "Maintain an authentic, welcoming Egyptian persona with occasional cultural flair (e.g. 'Ahlan wa Sahlan', 'Yalla')."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=AgentRecommendationResponse,
                    temperature=0.3,
                ),
            )
            data = json.loads(response.text)
            return AgentRecommendationResponse.model_validate(data)
        except Exception:
            return self._heuristic_generate_response(session, candidates, extracted, has_image=has_image)

    def _heuristic_extract_preferences(
        self, user_message: str, image: Optional[Any] = None
    ) -> ExtractedPreferences:
        """Rule-based extractor for instant offline testing and zero-downtime fallback."""
        msg = user_message.lower()
        interests: List[str] = []

        # Interest keyword mapping
        keyword_map = {
            "pharaonic": ["pharaoh", "pharaonic", "pyramid", "tomb", "temple", "hieroglyph", "mummy", "king tut", "ramses"],
            "ancient history": ["ancient", "history", "archaeology", "ruins", "monument", "historic"],
            "diving & snorkeling": ["diving", "dive", "snorkel", "snorkeling", "reef", "coral", "marine", "sea"],
            "markets & shopping": ["market", "souk", "shopping", "bazaar", "khan", "spices", "souvenirs"],
            "nature & desert": ["desert", "oasis", "safari", "hiking", "mountain", "stargazing", "sand", "salt lake"],
            "coastal & beaches": ["beach", "sea", "coastal", "swimming", "island", "mediterranean", "red sea", "fortress"],
            "culture & architecture": ["culture", "cultural", "mosque", "library", "citadel", "architecture", "nubian"],
            "relaxation": ["relax", "chill", "peaceful", "quiet", "resort", "sunset", "spa", "gardens"],
            "street food & dining": ["food", "culinary", "dining", "dishes", "koshary", "tea", "cafe"]
        }

        for category, keywords in keyword_map.items():
            if any(kw in msg for kw in keywords):
                interests.append(category)

        # Image heuristic detection if filename is passed
        detected_city = None
        if isinstance(image, str):
            img_low = image.lower()
            if "citadel" in img_low or "qaitbay" in img_low:
                detected_city = "Alexandria"
                if "coastal & beaches" not in interests:
                    interests.append("coastal & beaches")
            elif "karnak" in img_low or "luxor" in img_low:
                detected_city = "Luxor"
                if "pharaonic" not in interests:
                    interests.append("pharaonic")
            elif "coral" in img_low or "diving" in img_low or "sinai" in img_low:
                detected_city = "Sharm El-Sheikh"
                if "diving & snorkeling" not in interests:
                    interests.append("diving & snorkeling")

        # City detection from message
        if not detected_city:
            cities = [
                "sharm el-sheikh", "sharm", "marsa alam", "marsa matrouh", "el alamein",
                "el gouna", "st. catherine", "cairo", "giza", "luxor", "alexandria",
                "aswan", "dahab", "siwa", "fayoum", "hurghada", "nuweiba", "taba",
                "kom ombo", "edfu", "qena", "sohag", "bahariya", "dakhla", "farafra",
                "safaga", "port said", "rosetta", "sharkia"
            ]
            for c in cities:
                if c in msg:
                    if c == "sharm":
                        detected_city = "Sharm El-Sheikh"
                    elif c == "st. catherine":
                        detected_city = "St. Catherine"
                    else:
                        detected_city = c.title()
                    break

        # Style detection
        style = None
        if any(w in msg for w in ["family", "kids", "children"]):
            style = "family-friendly"
        elif any(w in msg for w in ["solo", "alone", "myself"]):
            style = "solo exploration"
        elif any(w in msg for w in ["luxury", "resort", "upscale"]):
            style = "luxury relaxation"
        elif any(w in msg for w in ["budget", "backpack", "hostel"]):
            style = "backpacker / budget"
        elif any(w in msg for w in ["couple", "romantic", "honeymoon"]):
            style = "romantic getaway"

        # Negative constraint detection
        negative_constraints: List[str] = []
        neg_patterns = [
            ("museum", ["no museum", "no museums", "avoid museum", "avoid museums", "don't want museum", "dont want museum", "not museum", "not museums", "skip museum", "without museum", "without museums"]),
            ("crowded", ["no crowd", "no crowds", "avoid crowd", "avoid crowds", "avoid crowded", "not crowded", "no crowded spots", "no crowded", "less crowded", "without crowd", "without crowds"]),
            ("hiking", ["no hiking", "avoid hiking", "not hiking", "no mountain climbing", "without hiking"]),
            ("diving", ["no diving", "avoid diving", "not diving", "no snorkeling", "without diving", "without snorkeling"]),
            ("desert", ["no desert", "avoid desert", "not desert", "without desert"]),
            ("tomb", ["no tomb", "no tombs", "avoid tomb", "avoid tombs", "without tomb", "without tombs"]),
            ("church", ["no church", "no churches", "avoid church", "avoid churches", "without church"]),
            ("temple", ["no temple", "no temples", "avoid temple", "avoid temples", "without temple"]),
        ]
        for term, phrases in neg_patterns:
            if any(p in msg for p in phrases):
                negative_constraints.append(term)

        # Price preference detection
        price_pref = None
        if any(w in msg for w in ["cheaper", "cheap", "budget", "affordable", "economic", "low cost", "not expensive"]):
            price_pref = "$"
        elif any(w in msg for w in ["luxury", "upscale", "exclusive", "5 star", "$$$$", "high end", "five star"]):
            price_pref = "$$$$"
        elif any(w in msg for w in ["mid-range", "moderate", "$$"]):
            price_pref = "$$"
        elif "$" in msg:
            if "$$$$" in msg:
                price_pref = "$$$$"
            elif "$$$" in msg:
                price_pref = "$$$"
            elif "$$" in msg:
                price_pref = "$$"
            else:
                price_pref = "$"

        return ExtractedPreferences(
            new_interests=interests,
            target_city=detected_city,
            budget_or_style=style,
            negative_constraints=negative_constraints,
            price_preference=price_pref,
        )

    def _heuristic_generate_response(
        self,
        session: UserSession,
        candidates: List[Dict[str, Any]],
        extracted: ExtractedPreferences,
        has_image: bool = False,
    ) -> AgentRecommendationResponse:
        """Grounded fallback response generator when API client is offline or keyless."""
        recs: List[MatchedLandmark] = []
        profile = session.to_dict()
        interests_list = profile.get("interests", [])
        interests_str = ", ".join(interests_list) if interests_list else "classic Egyptian highlights"
        city = profile.get("target_city")

        for cand in candidates[:2]:
            visual_clause = " Matching the visual aesthetics of your photo, " if has_image else " "
            why = (
                f"Selected because it features {cand['category']} situated in {cand['city']}.{visual_clause}"
                f"Its rich offerings ({cand['tags']}) directly align with your interest in {interests_str}. "
                f"{cand['description'][:140]}..."
            )
            recs.append(
                MatchedLandmark(
                    landmark_name=cand["landmark_name"],
                    city=cand["city"],
                    category=cand["category"],
                    match_score=cand["score"],
                    why_matched=why,
                    highlight_tip=f"Ideal for {cand['ideal_for']}. Allow around {cand.get('typical_duration_hours', 2)} hours to immerse fully.",
                    district=cand.get("district", cand["city"]),
                    price_tier=cand.get("price_tier", "$$")
                )
            )

        city_mention = f" in {city}" if city else " across Egypt"
        photo_greeting = " I've analyzed your reference photo and " if has_image else " "
        conversational_reply = (
            f"Ahlan wa Sahlan!{photo_greeting}Based on your interest in {interests_str}{city_mention}, "
            f"I have hand-picked standout landmarks that provide rich historical and cultural experiences."
        )

        summary = f"Identified preferences: {interests_str} | City: {city or 'Any'}"
        if has_image:
            summary += " (Visual features incorporated)"
        follow_up = "Would you like more options for nearby traditional dining, or should we refine the pacing of your itinerary?"

        return AgentRecommendationResponse(
            conversational_reply=conversational_reply,
            extracted_summary=summary,
            recommendations=recs,
            suggested_follow_up=follow_up
        )
