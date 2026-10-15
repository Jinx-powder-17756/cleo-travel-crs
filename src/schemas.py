from __future__ import annotations

from typing import List, Optional, Set, Dict, Any
from pydantic import BaseModel, Field


class ExtractedPreferences(BaseModel):
    """Structured extraction of user preferences from a conversational turn."""
    new_interests: list[str] = Field(default_factory=list, description="Extracted tourist interests")
    target_city: str | None = Field(default=None, description="Explicitly mentioned city, or None")
    budget_or_style: str | None = Field(default=None, description="Trip vibe (family, solo, exploration)")
    negative_constraints: list[str] = Field(
        default_factory=list,
        description="Explicitly excluded categories, tags, or counter-indicated items (e.g. 'no museums', 'avoid crowds')"
    )
    price_preference: str | None = Field(
        default=None,
        description="Price tier preference ('$', '$$', '$$$', '$$$$', or budget keywords like 'budget', 'luxury')"
    )


class UserSession:
    """Stateful user session manager accumulating preferences across dialogue turns."""
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.chat_history: list[dict] = []
        self.profile: dict[str, Any] = {
            "accumulated_interests": set(),
            "target_city": None,
            "budget_or_style": None,
            "negative_constraints": set(),
            "price_preference": None,
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

        if data_dict.get("negative_constraints"):
            # Normalize and merge negative constraints
            for item in data_dict["negative_constraints"]:
                if item and isinstance(item, str) and item.strip():
                    self.profile["negative_constraints"].add(item.strip().lower())

        if data_dict.get("target_city"):
            self.profile["target_city"] = data_dict["target_city"].strip()

        if data_dict.get("budget_or_style"):
            self.profile["budget_or_style"] = data_dict["budget_or_style"].strip()

        if data_dict.get("price_preference"):
            self.profile["price_preference"] = data_dict["price_preference"].strip()

    def to_dict(self) -> dict:
        """Returns serializable dictionary of the user's active profile."""
        return {
            "interests": list(self.profile["accumulated_interests"]),
            "target_city": self.profile["target_city"],
            "budget_or_style": self.profile["budget_or_style"],
            "negative_constraints": list(self.profile["negative_constraints"]),
            "price_preference": self.profile["price_preference"],
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
    district: Optional[str] = Field(default=None, description="Neighborhood or sub-district")
    price_tier: Optional[str] = Field(default="$$", description="Estimated price tier: $, $$, $$$, $$$$")


class AgentRecommendationResponse(BaseModel):
    """Structured response from the Egyptian Travel Assistant."""
    conversational_reply: str = Field(description="Conversational response from travel guide persona")
    extracted_summary: str = Field(description="Brief summary of understood preferences")
    recommendations: list[MatchedLandmark] = Field(default_factory=list)
    suggested_follow_up: str = Field(description="Follow-up question to probe for more preferences")


class TimeSlot(str):
    """Time of day slots for itinerary planning."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class ItineraryStop(BaseModel):
    """An individual scheduled stop in a daily travel itinerary."""
    time_slot: str = Field(description="morning, afternoon, or evening")
    landmark_name: str = Field(description="Name of landmark")
    category: Optional[str] = Field(default=None, description="Category of landmark")
    district: Optional[str] = Field(default=None, description="Geographic district / neighborhood")
    duration_hours: float = Field(default=2.0, description="Estimated duration in hours")
    insider_tip: str = Field(default="", description="Practical tip for visiting")
    transport_advice: str = Field(default="", description="How to reach this stop from the previous one")
    price_tier: Optional[str] = Field(default="$$", description="Estimated expense tier: $, $$, $$$, $$$$")
    matched_landmark: Optional[MatchedLandmark] = Field(default=None, description="Optional full matched landmark reference")


class DayPlan(BaseModel):
    """A full day's geographically clustered travel plan."""
    day_number: int = Field(description="1-indexed day sequence number")
    theme_or_district: str = Field(description="Regional or thematic focus (e.g. 'Giza Pyramids & Antiquities')")
    stops: list[ItineraryStop] = Field(default_factory=list, description="Chronologically ordered stops")
    route_rationale: str = Field(default="", description="Explanation of geographic clustering and travel flow")


class ItineraryPlan(BaseModel):
    """Complete multi-day travel itinerary."""
    city: str = Field(description="Primary destination city or region")
    total_days: int = Field(default=3, description="Number of days planned")
    pace: str = Field(default="moderate", description="Pacing: relaxed, moderate, or packed")
    summary: str = Field(default="", description="Executive overview of the curated journey")
    days: list[DayPlan] = Field(default_factory=list, description="Day-by-day plans")

    def to_markdown(self) -> str:
        """Renders the itinerary as a clean, publication-ready markdown guide."""
        lines = [
            f"# 🧭 Cleo Custom Itinerary: {self.city} ({self.total_days} Days)",
            f"**Pacing:** {self.pace.capitalize()} | **Destination:** {self.city}",
            "",
            f"*{self.summary}*",
            "",
            "---",
        ]
        for day in self.days:
            lines.append(f"## 📅 Day {day.day_number}: {day.theme_or_district}")
            if day.route_rationale:
                lines.append(f"> **Route Strategy:** {day.route_rationale}\n")
            
            for stop in day.stops:
                slot_emoji = {
                    "morning": "🌅 Morning",
                    "afternoon": "☀️ Afternoon",
                    "evening": "🌙 Evening"
                }.get(stop.time_slot.lower(), f"⏰ {stop.time_slot.title()}")
                
                district_str = f" • *{stop.district}*" if stop.district else ""
                cost_str = f" • Cost: `{stop.price_tier}`" if stop.price_tier else ""
                lines.append(f"### {slot_emoji}: {stop.landmark_name}{district_str}{cost_str}")
                lines.append(f"- **Suggested Duration:** ~{stop.duration_hours:.1f} hours")
                if stop.insider_tip:
                    lines.append(f"- **Insider Tip:** {stop.insider_tip}")
                if stop.transport_advice:
                    lines.append(f"- **Transit Advice:** {stop.transport_advice}")
                lines.append("")
            lines.append("---")
        return "\n".join(lines)
