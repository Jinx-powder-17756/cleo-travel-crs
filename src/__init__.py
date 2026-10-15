"""
Conversational AI Travel Assistant with Dynamic Preference Extraction & Landmark Recommendations
Specialized in Egyptian Tourism.
"""

from src.schemas import (
    ExtractedPreferences,
    MatchedLandmark,
    AgentRecommendationResponse,
    UserSession,
    UserSessionState,
    TimeSlot,
    ItineraryStop,
    DayPlan,
    ItineraryPlan,
)
from src.vector_store import LandmarkVectorStore
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent
from src.itinerary_planner import SpatialItineraryPlanner
from src.config import get_gemini_client, DEFAULT_MODEL

__all__ = [
    "ExtractedPreferences",
    "MatchedLandmark",
    "AgentRecommendationResponse",
    "UserSession",
    "UserSessionState",
    "TimeSlot",
    "ItineraryStop",
    "DayPlan",
    "ItineraryPlan",
    "LandmarkVectorStore",
    "EgyptianLandmarksDataset",
    "EgyptianTravelAgent",
    "SpatialItineraryPlanner",
    "get_gemini_client",
    "DEFAULT_MODEL",
]
