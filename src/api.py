from __future__ import annotations

import base64
import io
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

from src.schemas import (
    UserSession,
    MatchedLandmark,
    AgentRecommendationResponse,
    ItineraryPlan,
)
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent
from src.itinerary_planner import SpatialItineraryPlanner

app = FastAPI(
    title="Cleo - Egyptian Tourism Conversational Recommender System (CRS) API",
    description="REST API backend for multimodal recommendation, critiquing, and spatial itinerary planning.",
    version="2.0.0",
)

# Enable CORS for external web/mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
dataset = EgyptianLandmarksDataset()
agent = EgyptianTravelAgent(dataset=dataset)
planner = SpatialItineraryPlanner(dataset=dataset)

# In-memory session store
sessions: Dict[str, UserSession] = {}


def get_or_create_session(session_id: Optional[str] = None) -> UserSession:
    """Retrieves an existing UserSession or instantiates a new one."""
    if not session_id or not session_id.strip():
        session_id = str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = UserSession(user_id=session_id)
    return sessions[session_id]


# --- Request and Response Models ---

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_user", description="Unique session ID")
    message: str = Field(..., description="Tourist natural query or feedback")
    image_base64: Optional[str] = Field(default=None, description="Optional base64-encoded landmark image")


class ChatResponse(BaseModel):
    session_id: str
    conversational_reply: str
    extracted_summary: str
    user_profile: Dict[str, Any]
    recommendations: List[MatchedLandmark]
    suggested_follow_up: str


class ItineraryRequest(BaseModel):
    session_id: Optional[str] = Field(default="default_user", description="Active session ID")
    days_count: int = Field(default=3, ge=1, le=7, description="Number of days to plan (1-7)")
    pace: str = Field(default="moderate", description="Pacing: relaxed, moderate, or packed")


class SessionResponse(BaseModel):
    session_id: str
    profile: Dict[str, Any]
    chat_history: List[Dict[str, str]]
    recommended_landmarks: List[str]


class DeleteSessionResponse(BaseModel):
    session_id: str
    message: str


# --- Endpoints ---

@app.get("/api/v1/health")
@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint returning system status and landmark catalog size."""
    return {
        "status": "healthy",
        "service": "Cleo Egyptian Tourism CRS",
        "total_landmarks": len(dataset.get_all_landmarks()),
        "vector_store_dimension": dataset.vector_store.dimension,
        "is_gemini_embedded": dataset.vector_store.is_gemini_embedded,
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_turn(request: ChatRequest) -> ChatResponse:
    """
    Executes a multimodal conversational turn:
    - Extracts preferences and negative constraints
    - Updates session state
    - Performs FAISS dense vector retrieval with critiquing
    - Returns explainable recommendations
    """
    session = get_or_create_session(request.session_id)

    # Process image if provided in base64
    image_obj = None
    if request.image_base64:
        try:
            image_bytes = base64.b64decode(request.image_base64)
            image_obj = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 image data: {str(e)}",
            )

    rec_response: AgentRecommendationResponse = agent.process_turn(
        user_message=request.message,
        session=session,
        image=image_obj,
    )

    return ChatResponse(
        session_id=session.user_id,
        conversational_reply=rec_response.conversational_reply,
        extracted_summary=rec_response.extracted_summary,
        user_profile=session.to_dict(),
        recommendations=rec_response.recommendations,
        suggested_follow_up=rec_response.suggested_follow_up,
    )


@app.post("/api/v1/itinerary", response_model=ItineraryPlan)
def generate_itinerary(request: ItineraryRequest) -> ItineraryPlan:
    """
    Generates a geographically clustered, sequenced multi-day itinerary
    based on the tourist's accumulated profile in the session.
    """
    session = get_or_create_session(request.session_id)
    itinerary = planner.plan_itinerary(
        session=session,
        days_count=request.days_count,
        pace=request.pace,
    )
    return itinerary


@app.get("/api/v1/session/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    """Retrieves the current state of a tourist's session profile."""
    if session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found.",
        )
    session = sessions[session_id]
    return SessionResponse(
        session_id=session.user_id,
        profile=session.to_dict(),
        chat_history=session.chat_history,
        recommended_landmarks=session.recommended_landmarks,
    )


@app.delete("/api/v1/session/{session_id}", response_model=DeleteSessionResponse)
def delete_session(session_id: str) -> DeleteSessionResponse:
    """Resets or deletes a session."""
    if session_id in sessions:
        del sessions[session_id]
        return DeleteSessionResponse(
            session_id=session_id,
            message=f"Session '{session_id}' successfully deleted and reset.",
        )
    return DeleteSessionResponse(
        session_id=session_id,
        message=f"Session '{session_id}' was not active; ready for new dialogue.",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
