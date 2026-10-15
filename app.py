import os
import io
import json
import base64
import requests
import streamlit as st
import pandas as pd
from PIL import Image

from src.config import get_api_key, get_gemini_client, DEFAULT_MODEL
from src.schemas import UserSession, ItineraryPlan, MatchedLandmark
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent
from src.itinerary_planner import SpatialItineraryPlanner

# Page Configuration
st.set_page_config(
    page_title="Cleo — Egyptian Travel CRS",
    page_icon="🏺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Gold & Midnight theme with clean glassmorphic touches)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #d4af37;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.0rem;
        color: #8892b0;
        margin-bottom: 1.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .status-online {
        background-color: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
        border: 1px solid #2ecc71;
    }
    .status-offline {
        background-color: rgba(241, 196, 15, 0.2);
        color: #f1c40f;
        border: 1px solid #f1c40f;
    }
    .landmark-card {
        background: #112240;
        border: 1px solid #233554;
        border-left: 4px solid #d4af37;
        border-radius: 8px;
        padding: 14px 16px;
        margin-top: 12px;
        margin-bottom: 12px;
    }
    .landmark-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #ffffff;
    }
    .landmark-meta {
        font-size: 0.85rem;
        color: #64ffda;
        margin-bottom: 8px;
    }
    .landmark-why {
        font-size: 0.92rem;
        color: #ccd6f6;
        line-height: 1.45;
        margin-bottom: 8px;
    }
    .landmark-tip {
        font-size: 0.85rem;
        color: #ffd166;
        background: rgba(255, 209, 102, 0.1);
        padding: 6px 10px;
        border-radius: 4px;
    }
    .interest-chip {
        display: inline-block;
        background: #1f4068;
        color: #e0f2fe;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #3b82f6;
    }
    .neg-chip {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #ef4444;
    }
    .itinerary-day-box {
        background: #112240;
        border: 1px solid #233554;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .stop-card {
        background: #0a192f;
        border-left: 3px solid #64ffda;
        border-radius: 6px;
        padding: 12px 14px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "dataset" not in st.session_state:
    st.session_state.dataset = EgyptianLandmarksDataset()

if "user_session" not in st.session_state:
    st.session_state.user_session = UserSession(user_id="web_traveler_01")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ahlan wa Sahlan! 🇪🇬 I am **Cleo**, your personal Egyptian travel concierge. Tell me about your dream trip to Egypt, or upload a photo of a landmark or vibe you love!",
            "recommendations": [],
            "extracted": None,
            "image": None
        }
    ]

# Manage API Client in session
api_key_env = get_api_key()
if "api_key" not in st.session_state:
    st.session_state.api_key = api_key_env or ""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/egypt-pyramid.png", width=64)
    st.title("Settings & Controls")

    # API Key Input
    user_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get a free key from Google AI Studio (https://aistudio.google.com/)"
    )
    if user_key != st.session_state.api_key:
        st.session_state.api_key = user_key
        os.environ["GEMINI_API_KEY"] = user_key
        st.rerun()

    has_active_key = bool(st.session_state.api_key)

    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-3.8-flash"],
        index=0
    )

    st.markdown("---")
    st.subheader("⚙️ Backend Architecture")
    backend_choice = st.radio(
        "Execution Mode",
        options=["Local Engine (In-Memory)", "FastAPI REST API (Port 8000)"],
        index=0,
        help="Decoupled REST API backend mode allows consuming Cleo via HTTP endpoints"
    )
    use_rest_backend = "FastAPI" in backend_choice
    api_base_url = "http://localhost:8000"
    is_api_live = False

    if use_rest_backend:
        try:
            h_resp = requests.get(f"{api_base_url}/api/v1/health", timeout=1.0)
            if h_resp.status_code == 200:
                is_api_live = True
                st.success("🟢 FastAPI Service Online (v2.0.0)")
            else:
                st.warning("⚠️ FastAPI error, fallback to Local")
        except Exception:
            st.warning("⚠️ FastAPI server offline, using Local")

    st.markdown("---")
    st.subheader("📸 Multimodal Sample Tests")
    st.caption("Test image recognition & visual vibe extraction:")

    col_s1, col_s2, col_s3 = st.columns(3)
    sample_img_choice = None
    with col_s1:
        if st.button("🏰 Qaitbay", width="stretch", help="Alexandria Coastal Fortress"):
            sample_img_choice = "data/sample_images/qaitbay_citadel.jpg"
            st.session_state.pending_prompt = "Where is this fortress in Egypt, and what should I visit nearby?"
            st.session_state.pending_image = sample_img_choice
            st.rerun()
    with col_s2:
        if st.button("🏛️ Karnak", width="stretch", help="Luxor Ancient Columns"):
            sample_img_choice = "data/sample_images/karnak_temple.jpg"
            st.session_state.pending_prompt = "I want to visit ancient temple complexes with towering columns like this."
            st.session_state.pending_image = sample_img_choice
            st.rerun()
    with col_s3:
        if st.button("🐠 Reef", width="stretch", help="Sinai Red Sea Diving"):
            sample_img_choice = "data/sample_images/coral_reef_diving.jpg"
            st.session_state.pending_prompt = "What are the best snorkeling and scuba diving spots with this vibrant marine life?"
            st.session_state.pending_image = sample_img_choice
            st.rerun()

    st.markdown("---")
    st.subheader("💬 Quick Text & Critiquing Prompts")
    sample_prompts = [
        ("🏛️ Luxor Pharaonic (Solo)", "I love ancient history and pharaonic monuments, where should I go in Luxor as a solo traveler?"),
        ("🚫 Alexandria (No Museums)", "I want to visit Alexandria for coastal sights and seafood, but absolutely no museums."),
        ("💰 Cairo Budget ($)", "Show me budget-friendly sights in Cairo with $ price tier and avoid crowded spots."),
        ("🤿 Sinai Diving & Reefs", "We are looking for world-class scuba diving and beautiful coral reefs in Sinai."),
        ("🛍️ Cairo Souqs & Street Food", "Where can I find vibrant historic bazaars, handmade crafts, and street food in Cairo?"),
        ("🏜️ Siwa Oasis Eco-escape", "I want an off-the-beaten-path desert oasis with salt lakes and peaceful stargazing.")
    ]

    for label, prompt_text in sample_prompts:
        if st.button(label, width="stretch"):
            st.session_state.pending_prompt = prompt_text
            st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset Traveler Session", width="stretch", type="secondary"):
        st.session_state.user_session = UserSession(user_id="web_traveler_01")
        st.session_state.itinerary_plan = None
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ahlan wa Sahlan! 🇪🇬 Session memory has been reset. What kind of Egyptian adventure can I plan for you?",
                "recommendations": [],
                "extracted": None,
                "image": None
            }
        ]
        if use_rest_backend and is_api_live:
            try:
                requests.delete(f"{api_base_url}/api/v1/session/web_traveler_01", timeout=1.0)
            except Exception:
                pass
        st.rerun()

    # Landmark Database Explorer Expander
    total_sites = len(st.session_state.dataset.get_all_landmarks())
    with st.expander(f"📚 Explore Landmark Catalog ({total_sites} sites across Egypt)"):
        all_df = st.session_state.dataset.get_all_landmarks()
        st.dataframe(
            all_df[["landmark_name", "city", "district", "category", "price_tier", "ideal_for"]],
            hide_index=True,
            width="stretch"
        )

# Initialize Agent & Vector Store Client
gemini_client = get_gemini_client(st.session_state.api_key) if st.session_state.api_key else None
if gemini_client:
    st.session_state.dataset.set_client(gemini_client)

agent = EgyptianTravelAgent(
    client=gemini_client,
    model_name=model_choice,
    dataset=st.session_state.dataset
)
planner = SpatialItineraryPlanner(
    client=gemini_client,
    model_name=model_choice,
    dataset=st.session_state.dataset
)

# ----------------- MAIN LAYOUT -----------------
st.markdown('<div class="main-title">🏺 Cleo — Egyptian Tourism Recommender & Operating System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multimodal RAG • Conversational Critiquing • Spatial Day-by-Day Itineraries • REST API Backend</div>', unsafe_allow_html=True)

if is_api_live and use_rest_backend:
    st.markdown('<span class="status-badge status-online">● FASTAPI REST BACKEND CONNECTED (Port 8000)</span>', unsafe_allow_html=True)
elif has_active_key:
    st.markdown('<span class="status-badge status-online">● LOCAL ONLINE (Gemini Flash & text-embedding-004 Connected)</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="status-badge status-offline">● OFFLINE SIMULATION (Enter API key in sidebar to enable Gemini)</span>', unsafe_allow_html=True)

col_chat, col_state = st.columns([1.25, 0.75], gap="large")

# ----------------- LEFT: TABS FOR CHAT & ITINERARY -----------------
with col_chat:
    tab_chat, tab_itinerary = st.tabs(["💬 Conversational Discovery", "🗺️ Spatial Itinerary Planner"])

    with tab_chat:
        st.subheader("💬 Travel Conversation & Critiquing")

        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🏺" if msg["role"] == "assistant" else "👤"):
                if msg.get("image"):
                    st.image(msg["image"], width=280, caption="Attached Reference Photo")

                st.markdown(msg["content"])

                # Extracted badge preview
                if msg.get("extracted"):
                    ext = msg["extracted"]
                    with st.expander("🔍 Preferences extracted in this turn", expanded=False):
                        st.write(f"• **New Interests**: {', '.join(ext.new_interests) if ext.new_interests else 'None'}")
                        st.write(f"• **City Identified**: {ext.target_city or 'None'}")
                        st.write(f"• **Style / Vibe**: {ext.budget_or_style or 'None'}")
                        st.write(f"• **Negative Constraints**: {', '.join(ext.negative_constraints) if ext.negative_constraints else 'None'}")
                        st.write(f"• **Price Preference**: {ext.price_preference or 'None'}")

                # Grounded Landmark Cards
                if msg.get("recommendations"):
                    for rec in msg["recommendations"]:
                        district_badge = f" | Sub-district: {rec.district}" if getattr(rec, "district", None) else ""
                        price_badge = f" | Price: {rec.price_tier}" if getattr(rec, "price_tier", None) else ""
                        card_html = f"""
                        <div class="landmark-card">
                            <div class="landmark-title">🏛️ {rec.landmark_name}</div>
                            <div class="landmark-meta">📍 {rec.city}{district_badge}{price_badge} | Category: {rec.category} | Match Score: {rec.match_score:.2f}</div>
                            <div class="landmark-why"><strong>Why Matched:</strong> {rec.why_matched}</div>
                            <div class="landmark-tip">💡 <strong>Insider Tip:</strong> {rec.highlight_tip}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)

        # Image upload option in chat area
        with st.expander("📸 Attach a Landmark or Inspiration Photo", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload travel photo (JPEG/PNG/WebP)",
                type=["jpg", "jpeg", "png", "webp"],
                key="chat_file_uploader",
                label_visibility="collapsed"
            )
            if uploaded_file:
                st.image(uploaded_file, width=180, caption="Ready to analyze with next message")

        # Handle Input from Chat or Sidebar Quick Prompt
        prompt_to_process = None
        image_to_process = None

        if "pending_prompt" in st.session_state:
            prompt_to_process = st.session_state.pop("pending_prompt")
            image_to_process = st.session_state.pop("pending_image", None)
        else:
            user_input = st.chat_input("Ask about sights or critique recommendations (e.g. 'No museums', 'Something cheaper')...")
            if user_input:
                prompt_to_process = user_input
                image_to_process = uploaded_file

        if prompt_to_process:
            # Append User Message with optional image
            st.session_state.messages.append({
                "role": "user",
                "content": prompt_to_process,
                "image": image_to_process
            })
            with st.chat_message("user", avatar="👤"):
                if image_to_process:
                    st.image(image_to_process, width=280, caption="Attached Reference Photo")
                st.markdown(prompt_to_process)

            # Process Turn
            with st.chat_message("assistant", avatar="🏺"):
                spinner_msg = "Analyzing photo & query..." if image_to_process else "Filtering constraints & querying FAISS..."
                with st.spinner(spinner_msg):
                    if use_rest_backend and is_api_live:
                        # REST API Backend Call
                        try:
                            img_b64 = None
                            if image_to_process:
                                if hasattr(image_to_process, "read"):
                                    img_b64 = base64.b64encode(image_to_process.read()).decode("utf-8")
                                    if hasattr(image_to_process, "seek"):
                                        image_to_process.seek(0)
                                elif isinstance(image_to_process, str) and os.path.exists(image_to_process):
                                    with open(image_to_process, "rb") as f:
                                        img_b64 = base64.b64encode(f.read()).decode("utf-8")

                            payload = {
                                "session_id": st.session_state.user_session.user_id,
                                "message": prompt_to_process,
                                "image_base64": img_b64,
                            }
                            resp = requests.post(f"{api_base_url}/api/v1/chat", json=payload, timeout=25.0)
                            if resp.status_code == 200:
                                api_data = resp.json()
                                st.session_state.user_session.update_profile(api_data["user_profile"])
                                st.session_state.user_session.add_message("user", prompt_to_process)
                                st.session_state.user_session.add_message("assistant", api_data["conversational_reply"])

                                recs = [MatchedLandmark.model_validate(r) for r in api_data["recommendations"]]
                                for r in recs:
                                    st.session_state.user_session.record_recommendation(r.landmark_name)

                                full_reply = f"{api_data['conversational_reply']}\n\n**💬 Next Step:** {api_data['suggested_follow_up']}"
                                st.markdown(full_reply)
                                for rec in recs:
                                    d_badge = f" | Sub-district: {rec.district}" if getattr(rec, "district", None) else ""
                                    p_badge = f" | Price: {rec.price_tier}" if getattr(rec, "price_tier", None) else ""
                                    card_html = f"""
                                    <div class="landmark-card">
                                        <div class="landmark-title">🏛️ {rec.landmark_name}</div>
                                        <div class="landmark-meta">📍 {rec.city}{d_badge}{p_badge} | Category: {rec.category} | Match Score: {rec.match_score:.2f}</div>
                                        <div class="landmark-why"><strong>Why Matched:</strong> {rec.why_matched}</div>
                                        <div class="landmark-tip">💡 <strong>Insider Tip:</strong> {rec.highlight_tip}</div>
                                    </div>
                                    """
                                    st.markdown(card_html, unsafe_allow_html=True)

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": full_reply,
                                    "recommendations": recs,
                                    "extracted": None,
                                    "image": None
                                })
                                st.rerun()
                        except Exception as e:
                            st.error(f"API Error ({str(e)}), falling back to local engine.")

                    # Local Engine Execution
                    extracted = agent.extract_preferences(prompt_to_process, st.session_state.user_session, image=image_to_process)
                    st.session_state.user_session.update_profile(extracted)
                    st.session_state.user_session.add_message("user", prompt_to_process)

                    candidates = st.session_state.dataset.retrieve_candidates(st.session_state.user_session, top_k=3)
                    agent_resp = agent.generate_recommendations(
                        prompt_to_process,
                        st.session_state.user_session,
                        candidates,
                        extracted,
                        has_image=bool(image_to_process)
                    )

                    for rec in agent_resp.recommendations:
                        st.session_state.user_session.record_recommendation(rec.landmark_name)
                    st.session_state.user_session.add_message("assistant", agent_resp.conversational_reply)

                    full_reply = f"{agent_resp.conversational_reply}\n\n**💬 Next Step:** {agent_resp.suggested_follow_up}"
                    st.markdown(full_reply)

                    for rec in agent_resp.recommendations:
                        d_badge = f" | Sub-district: {rec.district}" if getattr(rec, "district", None) else ""
                        p_badge = f" | Price: {rec.price_tier}" if getattr(rec, "price_tier", None) else ""
                        card_html = f"""
                        <div class="landmark-card">
                            <div class="landmark-title">🏛️ {rec.landmark_name}</div>
                            <div class="landmark-meta">📍 {rec.city}{d_badge}{p_badge} | Category: {rec.category} | Match Score: {rec.match_score:.2f}</div>
                            <div class="landmark-why"><strong>Why Matched:</strong> {rec.why_matched}</div>
                            <div class="landmark-tip">💡 <strong>Insider Tip:</strong> {rec.highlight_tip}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_reply,
                        "recommendations": agent_resp.recommendations,
                        "extracted": extracted,
                        "image": None
                    })
                    st.rerun()

    # --- TAB 2: SPATIAL ITINERARY PLANNER ---
    with tab_itinerary:
        st.subheader("🗺️ Spatial Day-by-Day Itinerary Planner")
        st.caption("Geographically clustered daily sequences without zigzagging across metropolis or river banks.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            itin_days = st.slider("Trip Duration (Days)", min_value=1, max_value=7, value=3)
        with col_p2:
            itin_pace = st.select_slider("Travel Rhythm / Pace", options=["relaxed", "moderate", "packed"], value="moderate")

        gen_clicked = st.button("🧭 Generate Geographically Clustered Itinerary", width="stretch", type="primary")

        if gen_clicked:
            with st.spinner("Clustering landmarks by sub-district & computing daily transit flow..."):
                if use_rest_backend and is_api_live:
                    try:
                        resp = requests.post(
                            f"{api_base_url}/api/v1/itinerary",
                            json={
                                "session_id": st.session_state.user_session.user_id,
                                "days_count": itin_days,
                                "pace": itin_pace,
                            },
                            timeout=25.0
                        )
                        if resp.status_code == 200:
                            st.session_state.itinerary_plan = ItineraryPlan.model_validate(resp.json())
                    except Exception as e:
                        st.warning(f"API fallback to local planner: {e}")
                        st.session_state.itinerary_plan = planner.plan_itinerary(
                            session=st.session_state.user_session,
                            days_count=itin_days,
                            pace=itin_pace
                        )
                else:
                    st.session_state.itinerary_plan = planner.plan_itinerary(
                        session=st.session_state.user_session,
                        days_count=itin_days,
                        pace=itin_pace
                    )
            st.rerun()

        # Display Itinerary
        plan: Optional[ItineraryPlan] = st.session_state.get("itinerary_plan")
        if plan:
            st.markdown(f"### 📍 {plan.city} • {plan.total_days}-Day Journey ({plan.pace.capitalize()} Pace)")
            st.info(f"*{plan.summary}*")

            # Export Buttons
            exp_c1, exp_c2 = st.columns(2)
            with exp_c1:
                st.download_button(
                    "📥 Export Itinerary (Markdown)",
                    data=plan.to_markdown(),
                    file_name=f"cleo_{plan.city.lower()}_{plan.total_days}day_itinerary.md",
                    mime="text/markdown",
                    width="stretch"
                )
            with exp_c2:
                st.download_button(
                    "📥 Export Itinerary (JSON)",
                    data=plan.model_dump_json(indent=2),
                    file_name=f"cleo_{plan.city.lower()}_{plan.total_days}day_itinerary.json",
                    mime="application/json",
                    width="stretch"
                )

            st.markdown("---")
            for day in plan.days:
                st.markdown(f"#### 📅 Day {day.day_number}: {day.theme_or_district}")
                if day.route_rationale:
                    st.caption(f"🧭 **Route Strategy:** {day.route_rationale}")

                for stop in day.stops:
                    slot_badge = {
                        "morning": "🌅 Morning",
                        "afternoon": "☀️ Afternoon",
                        "evening": "🌙 Evening"
                    }.get(stop.time_slot.lower(), f"⏰ {stop.time_slot.title()}")

                    dist_txt = f"📍 *{stop.district}*" if stop.district else ""
                    cost_txt = f" • Cost: `{stop.price_tier}`" if stop.price_tier else ""
                    dur_txt = f" • ~{stop.duration_hours:.1f} hrs"

                    st.markdown(f"""
                    <div class="stop-card">
                        <strong style="color: #64ffda;">{slot_badge}: {stop.landmark_name}</strong> {dist_txt}{cost_txt}{dur_txt}<br/>
                        <span style="font-size: 0.88rem; color: #ccd6f6;">💡 <em>Tip:</em> {stop.insider_tip}</span><br/>
                        <span style="font-size: 0.82rem; color: #8892b0;">🚗 <em>Transit:</em> {stop.transport_advice}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info("No itinerary generated yet. Select your preferred trip duration and click **Generate Geographically Clustered Itinerary**.")

# ----------------- RIGHT: LIVE SESSION PROFILE INSPECTOR -----------------
with col_state:
    st.subheader("🧭 Stateful Session Inspector")
    st.caption("Live synchronization with `UserSession.to_dict()`")

    profile_dict = st.session_state.user_session.to_dict()
    target_city = profile_dict.get("target_city")
    style = profile_dict.get("budget_or_style")
    interests = profile_dict.get("interests", [])
    negatives = profile_dict.get("negative_constraints", [])
    price_pref = profile_dict.get("price_preference")

    # Metrics
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Destination City", target_city if target_city else "Flexible / Any")
    with m2:
        st.metric("Price / Budget Tier", price_pref if price_pref else "Flexible")

    if style:
        st.caption(f"**Travel Vibe:** {style}")

    st.markdown("#### 🏷️ Accumulated Interests")
    if interests:
        chips_html = "".join([f'<span class="interest-chip">✨ {item}</span>' for item in interests])
        st.markdown(chips_html, unsafe_allow_html=True)
    else:
        st.info("No interests accumulated yet. Mention an activity or passion in chat!")

    st.markdown("#### 🚫 Excluded / Negative Constraints")
    if negatives:
        neg_chips_html = "".join([f'<span class="neg-chip">🚫 {item}</span>' for item in negatives])
        st.markdown(neg_chips_html, unsafe_allow_html=True)
    else:
        st.caption("No active exclusions (e.g. 'No museums', 'Avoid crowds').")

    st.markdown("#### 📋 Live `UserSession` Profile JSON")
    st.json(profile_dict)

    st.markdown("#### 🏛️ Previously Recommended Sites")
    recs_history = st.session_state.user_session.recommended_landmarks
    if recs_history:
        for idx, item in enumerate(recs_history, 1):
            st.markdown(f"**{idx}.** {item}")
    else:
        st.caption("No recommendations delivered yet.")

    # Live Candidate Retrieval RAG Debugger
    with st.expander("🔎 Current Top RAG Candidates (FAISS Dense Vector Match)", expanded=False):
        current_candidates = st.session_state.dataset.retrieve_candidates(st.session_state.user_session, top_k=4)
        if current_candidates:
            for c in current_candidates:
                dist = c.get("district", c.get("city"))
                st.markdown(f"**{c['landmark_name']}** ({c['city']}, {dist}) `[{c.get('price_tier', '$$')}]` — Score: `{c['score']:.3f}`")
                st.caption(f"_{c['description'][:100]}..._")
        else:
            st.write("No matching candidates.")

