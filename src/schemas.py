from __future__ import annotations

from typing import List, Optional, Set, Dict, Any
from pydantic import BaseModel, Field


class ExtractedPreferences(BaseModel):
    """Structured extraction of user preferences from a conversational turn."""
    new_interests: list[str] = Field(default_factory=list, description="Extracted tourist interests")
    target_city: str | None = Field(default=None, description="Explicitly mentioned city, or None")
    budget_or_style: str | None = Field(default=None, description="Trip vibe (family, solo, exploration)")


class UserSession:
    """Stateful user session manager accumulating preferences across dialogue turns."""
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.chat_history: list[dict] = []
        self.profile: dict[str, Any] = {
            "accumulated_interests": set(),
            "target_city": None,
            "budget_or_style": None,
        }
        self.recommended_landmarks: list[str] = []

    def update_profile(self, new_data: dict | ExtractedPreferences):
        """Merges new extracted preferences into the profile state."""
        if isinstance(new_data, ExtractedPreferences):
            data_dict = new_data.model_dump()
        else:
            data_dict = new_data

        if data_dict.get("new_interests"):
            # Normalize and merge interests
            for item in data_dict["new_interests"]:
                if item and isinstance(item, str) and item.strip():
                    self.profile["accumulated_interests"].add(item.strip().lower())

        if data_dict.get("target_city"):
            self.profile["target_city"] = data_dict["target_city"].strip()

        if data_dict.get("budget_or_style"):
            self.profile["budget_or_style"] = data_dict["budget_or_style"].strip()

    def to_dict(self) -> dict:
        """Returns serializable dictionary of the user's active profile."""
        return {
            "interests": list(self.profile["accumulated_interests"]),
            "target_city": self.profile["target_city"],
            "budget_or_style": self.profile["budget_or_style"],
        }

    def add_message(self, role: str, content: str):
        """Appends a turn to chat history."""
        self.chat_history.append({"role": role, "content": content})

    def record_recommendation(self, landmark_name: str):
        """Tracks already recommended landmarks to avoid immediate duplication."""
        if landmark_name not in self.recommended_landmarks:
            self.recommended_landmarks.append(landmark_name)

    # Backward compatibility alias
    update_with_preferences = update_profile


# Compatibility alias for earlier code
UserSessionState = UserSession


class MatchedLandmark(BaseModel):
    """A matched Egyptian landmark with explainable rationale."""
    landmark_name: str
    city: str
    category: str
    match_score: float = 1.0
    why_matched: str = Field(description="Explanation connecting landmark description to user preferences")
    highlight_tip: str = Field(default="", description="Practical insider travel tip")


class AgentRecommendationResponse(BaseModel):
    """Structured response from the Egyptian Travel Assistant."""
    conversational_reply: str = Field(description="Conversational response from travel guide persona")
    extracted_summary: str = Field(description="Brief summary of understood preferences")
    recommendations: list[MatchedLandmark] = Field(default_factory=list)
    suggested_follow_up: str = Field(description="Follow-up question to probe for more preferences")
