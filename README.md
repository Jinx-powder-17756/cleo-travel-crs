# 🏺 Cleo: Egyptian Tourism Conversational Recommender System (CRS)

An intelligent conversational travel assistant specialized in Egyptian tourism. Cleo takes natural, unstructured tourist queries, extracts fine-grained user preferences into a structured schema (JSON via Pydantic), maintains stateful session memory across dialogue turns, and matches queries against an Egyptian landmarks dataset utilizing rich landmark descriptions for explainable recommendations.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([User Natural Query + Optional Photo]) --> Extractor[Step 1: Multimodal Preference Extraction<br/>Gemini Flash + Pydantic Schema]
    Extractor --> ExtractedPrefs[ExtractedPreferences<br/>Interests, City, Style]
    ExtractedPrefs --> Session[Step 2: Stateful Session Memory<br/>UserSession Accumulation]
    Session --> VectorSearch[Step 3: FAISS Dense Vector Retrieval<br/>text-embedding-004 + City Filters]
    Dataset[(Egyptian Landmarks Dataset<br/>23 Curated Sites & Descriptions)] --> VectorSearch
    VectorSearch --> InContextPrompt[Grounded Context Injection<br/>Top K Candidates + Descriptions]
    InContextPrompt --> Recommender[Step 4: Explainable Recommendation<br/>Gemini Structured Output]
    Recommender --> AgentResponse[AgentRecommendationResponse<br/>Personalized Explanation + Insider Tip + Reply]
    AgentResponse --> User
```

---

## 🚀 Features (Phase 1 & Phase 2)

1. **Multimodal Preference & Landmark Extraction (LMM)**:
   - Users can provide unstructured natural text **and/or landmark photos** (e.g., coastal fortresses, desert oases, underwater coral reefs).
   - Identifies landmarks from photos, extracts visual aesthetic vibes into `new_interests`, and updates `target_city`.

2. **Conversational Critiquing & Negative Constraint Filtering**:
   - Understands negative preferences (e.g. *"no museums"*, *"avoid crowded spots"*, *"no hiking"*, *"without tombs"*).
   - Dynamically tracks `negative_constraints` and `price_preference` (`$`, `$$`, `$$$`, `$$$$`) in `UserSession`.
   - FAISS dense retrieval pipeline filters out counter-indicated landmarks and matches price tiers.

3. **Spatial Day-by-Day Itinerary Planner**:
   - Transforms isolated recommendation cards into logically sequenced, geographically clustered daily timelines.
   - Groups landmarks by sub-district (e.g. Islamic Cairo vs. Giza Pyramids vs. Downtown Tahrir vs. Luxor East/West Bank) to eliminate metropolis crisscrossing.
   - Assigns morning, afternoon, and evening time slots factoring in travel rhythm (`relaxed`, `moderate`, `packed`), providing transit advice, insider tips, and export to Markdown/JSON.

4. **Independent REST API Layer (FastAPI)**:
   - Decoupled backend architecture in `src/api.py` exposing:
     - `POST /api/v1/chat`: Conversational multimodal turn with session memory & critique filtering.
     - `POST /api/v1/itinerary`: Multi-day spatial itinerary generation.
     - `GET /api/v1/session/{session_id}`: Stateful session inspector.
     - `DELETE /api/v1/session/{session_id}`: Session reset.

5. **Interactive Split-Screen UI (Streamlit)**:
   - **Left Screen**: Tabbed interface featuring **Conversational Discovery & Critiquing** alongside the **Spatial Itinerary Planner & Exporter**.
   - **Right Screen**: Real-time `UserSession` profile JSON inspector, accumulated interest tags, negative constraint chips, and live FAISS similarity scores.

---

## 📂 Project Structure

```
Project/
├── data/
│   ├── egyptian_landmarks.csv     # 60 curated landmarks across all Egyptian regions with districts & price tiers
│   ├── landmark_embeddings.npz    # Cached precomputed dense vector embeddings
│   └── sample_images/             # Reference photos for multimodal testing
├── src/
│   ├── __init__.py                # Package exports
│   ├── schemas.py                 # Pydantic models (UserSession, ItineraryPlan, DayPlan, ItineraryStop)
│   ├── vector_store.py            # FAISS dense vector index with negative constraint & price filtering
│   ├── dataset.py                 # Dataset manager & vector retrieval coordinator
│   ├── agent.py                   # Multimodal extraction, critiquing & grounded recommendation engine
│   ├── itinerary_planner.py       # Spatial day-by-day itinerary planner & sub-district clustering
│   ├── api.py                     # FastAPI REST API backend service
│   └── config.py                  # API key & Gemini client loader
├── tests/
│   └── test_pipeline.py           # Unit and integration test suite (16 comprehensive tests)
├── main.py                        # Interactive Rich CLI with visual panels & session commands
├── app.py                         # Split-Screen Streamlit Web App (Chat + Itinerary Planner + State Inspector)
├── requirements.txt               # Dependencies (fastapi, streamlit, google-genai, pydantic, etc.)
├── .env.example                   # Environment configuration template
└── README.md
```

---

## ⚡ Quick Start

### 1. Launch the FastAPI REST Backend
```powershell
uvicorn src.api:app --reload --port 8000
```
Interactive Swagger docs: **`http://localhost:8000/docs`**

---

### 2. Launch the Interactive Web App
```powershell
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.
* **Left Screen**:
  * **Tab 1: Conversational Discovery**: Chat with Cleo, attach photos, and critique recommendations.
  * **Tab 2: Spatial Itinerary Planner**: Choose 1-7 days & travel rhythm, generate clustered daily itineraries, and export to Markdown or JSON.
* **Right Screen**: Real-time `UserSession` inspector, interest chips, negative constraint tags (`🚫`), and FAISS search scores.
* **Sidebar**: Toggle between **Local Engine** and **FastAPI REST API**, enter API key, or test 1-click prompts.

---

### 3. Run Automated Tests
```powershell
python -m unittest tests/test_pipeline.py
```
