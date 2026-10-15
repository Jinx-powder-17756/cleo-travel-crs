import unittest
from fastapi.testclient import TestClient
from src.schemas import (
    ExtractedPreferences,
    MatchedLandmark,
    AgentRecommendationResponse,
    UserSession,
    ItineraryPlan,
    DayPlan,
    ItineraryStop,
)
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent
from src.itinerary_planner import SpatialItineraryPlanner
from src.api import app


class TestEgyptianTravelAssistant(unittest.TestCase):

    def test_dataset_loading(self):
        dataset = EgyptianLandmarksDataset()
        df = dataset.get_all_landmarks()
        self.assertGreaterEqual(len(df), 20)
        required_cols = ["id", "landmark_name", "city", "region", "category", "tags", "description"]
        for col in required_cols:
            self.assertIn(col, df.columns)
        names = df["landmark_name"].tolist()
        self.assertIn("Karnak Temple", names)
        self.assertIn("Khan el-Khalili", names)
        self.assertIn("Ras Muhammad National Park", names)
        self.assertIn("Qaitbay Citadel", names)
        self.assertIn("Bibliotheca Alexandrina", names)

    def test_session_state_accumulation(self):
        session = UserSession(user_id="test_user")

        # Turn 1: user mentions ancient pharaonic history in Luxor
        pref1 = {
            "new_interests": ["pharaonic", "ancient history"],
            "target_city": "Luxor",
            "budget_or_style": "solo exploration",
        }
        session.update_profile(pref1)
        d1 = session.to_dict()
        self.assertEqual(d1["target_city"], "Luxor")
        self.assertIn("pharaonic", d1["interests"])
        self.assertIn("ancient history", d1["interests"])
        self.assertEqual(d1["budget_or_style"], "solo exploration")

        # Turn 2: user adds interest in local markets, interest should be merged without duplicating
        pref2 = {
            "new_interests": ["pharaonic", "markets & shopping"],
            "target_city": None,
            "budget_or_style": None
        }
        session.update_profile(pref2)
        d2 = session.to_dict()
        # Luxor should remain target_city
        self.assertEqual(d2["target_city"], "Luxor")
        # Interests should have 3 unique items
        self.assertEqual(len(d2["interests"]), 3)
        self.assertIn("markets & shopping", d2["interests"])

    def test_retrieval_luxor_pharaonic(self):
        dataset = EgyptianLandmarksDataset()
        session = UserSession()
        session.update_profile({
            "new_interests": ["pharaonic", "ancient history", "tombs"],
            "target_city": "Luxor",
        })

        candidates = dataset.retrieve_candidates(session, top_k=3)
        self.assertGreater(len(candidates), 0)
        top_candidate_names = [c["landmark_name"] for c in candidates]
        self.assertTrue("Karnak Temple" in top_candidate_names or "Valley of the Kings" in top_candidate_names)
        for c in candidates:
            self.assertEqual(c["city"], "Luxor")

    def test_retrieval_diving_sinai(self):
        dataset = EgyptianLandmarksDataset()
        session = UserSession()
        session.update_profile({
            "new_interests": ["diving", "coral reefs", "snorkeling"],
            "target_city": "Sharm El-Sheikh",
        })

        candidates = dataset.retrieve_candidates(session, top_k=3)
        self.assertGreater(len(candidates), 0)
        top_candidate = candidates[0]
        self.assertIn("Ras Muhammad National Park", top_candidate["landmark_name"])

    def test_agent_end_to_end_turn(self):
        dataset = EgyptianLandmarksDataset()
        agent = EgyptianTravelAgent(dataset=dataset)
        session = UserSession(user_id="test_turn")

        user_query = "I am visiting Cairo and I really want to see traditional bustling markets and try local food."
        response = agent.process_turn(user_query, session)

        self.assertIsInstance(response, AgentRecommendationResponse)
        self.assertGreater(len(response.recommendations), 0)
        d = session.to_dict()
        self.assertEqual(d["target_city"], "Cairo")
        self.assertIn("Khan el-Khalili", [r.landmark_name for r in response.recommendations])
        self.assertGreater(len(session.recommended_landmarks), 0)
        self.assertGreater(len(response.conversational_reply), 0)

    def test_turn1_turn2_alexandria_followup(self):
        """Verifies Turn 1 & Turn 2 preference retention and city update."""
        dataset = EgyptianLandmarksDataset()
        agent = EgyptianTravelAgent(dataset=dataset)
        session = UserSession(user_id="test_alexandria_flow")

        # Turn 1: Broad historical query without city
        t1_response = agent.process_turn("I love ancient history and pharaonic monuments, where should I go?", session)
        d1 = session.to_dict()
        self.assertIsNone(d1["target_city"])
        self.assertIn("pharaonic", d1["interests"])
        self.assertIn("ancient history", d1["interests"])

        # Turn 2: User shifts context to Alexandria without repeating interests
        t2_response = agent.process_turn("What if I'm visiting Alexandria?", session)
        d2 = session.to_dict()
        self.assertEqual(d2["target_city"], "Alexandria")
        # Interests must be retained
        self.assertIn("pharaonic", d2["interests"])
        self.assertIn("ancient history", d2["interests"])
        # Recommendations must all be in Alexandria
        alexandria_recs = [r.landmark_name for r in t2_response.recommendations]
        self.assertTrue(
            "Qaitbay Citadel" in alexandria_recs or
            "Bibliotheca Alexandrina" in alexandria_recs or
            "Catacombs of Kom El Shoqafa" in alexandria_recs
        )
        for r in t2_response.recommendations:
            self.assertEqual(r.city, "Alexandria")

    def test_faiss_vector_store_direct(self):
        """Verifies FAISS index creation, embedding dimension, and vector similarity search."""
        dataset = EgyptianLandmarksDataset()
        vstore = dataset.vector_store
        self.assertIsNotNone(vstore.index)
        self.assertGreater(vstore.dimension, 0)
        self.assertEqual(len(vstore.documents), len(dataset.get_all_landmarks()))

        # Direct search test on White Desert
        results = vstore.search("bizarre chalk stone formations in the desert", top_k=2)
        self.assertGreater(len(results), 0)
        top_name = results[0]["landmark_name"]
        self.assertEqual(top_name, "White Desert National Park")
        self.assertGreater(results[0]["score"], 0.0)

    def test_faiss_semantic_retrieval_sinai(self):
        """Verifies semantic dense retrieval with regional alias."""
        dataset = EgyptianLandmarksDataset()
        results = dataset.vector_store.search(
            query_text="colorful reef fish scuba diving deep marine reserve",
            top_k=2,
            target_city="Sinai"
        )
        self.assertGreater(len(results), 0)
        matched_names = [r["landmark_name"] for r in results]
        self.assertTrue("Ras Muhammad National Park" in matched_names or "Blue Hole & Canyon" in matched_names)

    def test_multimodal_image_turn(self):
        """Verifies multimodal input analysis (image + text) in EgyptianTravelAgent."""
        dataset = EgyptianLandmarksDataset()
        agent = EgyptianTravelAgent(dataset=dataset)
        session = UserSession(user_id="test_multimodal_user")

        image_path = "data/sample_images/qaitbay_citadel.jpg"
        user_query = "Where is this sea fortress located, and what is its history?"

        response = agent.process_turn(user_query, session, image=image_path)
        self.assertIsInstance(response, AgentRecommendationResponse)
        self.assertGreater(len(response.recommendations), 0)

        # Check that city was updated to Alexandria from visual recognition
        d = session.to_dict()
        self.assertEqual(d["target_city"], "Alexandria")
        self.assertIn("coastal & beaches", d["interests"])

        # Top recommendation should be Qaitbay Citadel
        top_rec_name = response.recommendations[0].landmark_name
        self.assertEqual(top_rec_name, "Qaitbay Citadel")
        self.assertEqual(response.recommendations[0].city, "Alexandria")

    def test_retrieval_fayoum_whales(self):
        """Verifies retrieval in Fayoum for prehistoric whale fossil valley."""
        dataset = EgyptianLandmarksDataset()
        session = UserSession()
        session.update_profile({
            "new_interests": ["whale fossils", "paleontology", "unesco valley"],
            "target_city": "Fayoum"
        })
        candidates = dataset.retrieve_candidates(session, top_k=2)
        self.assertGreater(len(candidates), 0)
        self.assertEqual(candidates[0]["landmark_name"], "Wadi Al-Hitan (Valley of the Whales)")
        self.assertEqual(candidates[0]["city"], "Fayoum")

    def test_retrieval_marsa_alam_dugongs(self):
        """Verifies retrieval in Marsa Alam for wild sea turtles and dugongs."""
        dataset = EgyptianLandmarksDataset()
        session = UserSession()
        session.update_profile({
            "new_interests": ["giant sea turtles", "dugong", "snorkeling in bay"],
            "target_city": "Marsa Alam"
        })
        candidates = dataset.retrieve_candidates(session, top_k=2)
        self.assertGreater(len(candidates), 0)
        self.assertEqual(candidates[0]["landmark_name"], "Marsa Abu Dabbab (Sea Turtles & Dugongs)")
        self.assertEqual(candidates[0]["city"], "Marsa Alam")

    def test_negative_constraint_filtering_museums(self):
        """Verifies that counter-indicated 'museum' items are dynamically excluded from candidates."""
        dataset = EgyptianLandmarksDataset()
        session = UserSession(user_id="test_neg_museum")
        session.update_profile({
            "new_interests": ["ancient history", "pharaonic", "art"],
            "target_city": "Cairo",
            "negative_constraints": ["museum"],
        })
        candidates = dataset.retrieve_candidates(session, top_k=4)
        self.assertGreater(len(candidates), 0)
        candidate_names = [c["landmark_name"] for c in candidates]
        # Museums must be filtered out
        for name in candidate_names:
            self.assertNotIn("Egyptian Museum", name)
            self.assertNotIn("NMEC", name)
            self.assertNotIn("Museum", name)

    def test_negative_constraint_session_accumulation(self):
        """Verifies multi-turn accumulation of negative constraints and price preferences."""
        session = UserSession(user_id="test_accumulation")
        session.update_profile({
            "new_interests": ["hiking"],
            "negative_constraints": ["crowded"],
            "price_preference": "$",
        })
        d = session.to_dict()
        self.assertIn("crowded", d["negative_constraints"])
        self.assertEqual(d["price_preference"], "$")

        # Turn 2: adds another constraint without erasing prior ones
        session.update_profile({
            "negative_constraints": ["museums"],
        })
        d2 = session.to_dict()
        self.assertIn("crowded", d2["negative_constraints"])
        self.assertIn("museums", d2["negative_constraints"])
        self.assertEqual(d2["price_preference"], "$")

    def test_price_tier_budget_filtering(self):
        """Verifies budget preference '$' filters out luxury '$$$$' candidates."""
        dataset = EgyptianLandmarksDataset()
        session = UserSession(user_id="test_price_tier")
        session.update_profile({
            "new_interests": ["nile cruise", "sailing", "adventure"],
            "target_city": "Luxor",
            "price_preference": "$",
        })
        candidates = dataset.retrieve_candidates(session, top_k=4)
        self.assertGreater(len(candidates), 0)
        for c in candidates:
            # Luxury tier $$$$ should be excluded or penalized below top results
            self.assertNotEqual(c.get("price_tier"), "$$$$")

    def test_spatial_itinerary_clustering_and_markdown(self):
        """Verifies multi-day itinerary generation, district clustering, and markdown generation."""
        dataset = EgyptianLandmarksDataset()
        planner = SpatialItineraryPlanner(dataset=dataset)
        session = UserSession(user_id="test_itinerary_user")
        session.update_profile({
            "new_interests": ["pharaonic", "pyramids", "islamic architecture"],
            "target_city": "Cairo",
        })

        itinerary = planner.plan_itinerary(session, days_count=3, pace="moderate")
        self.assertIsInstance(itinerary, ItineraryPlan)
        self.assertEqual(itinerary.city, "Cairo")
        self.assertEqual(len(itinerary.days), 3)

        for day in itinerary.days:
            self.assertGreater(len(day.stops), 0)
            self.assertTrue(len(day.theme_or_district) > 0)
            self.assertTrue(len(day.route_rationale) > 0)
            for stop in day.stops:
                self.assertIn(stop.time_slot.lower(), ["morning", "afternoon", "evening"])
                self.assertTrue(len(stop.landmark_name) > 0)
                self.assertTrue(len(stop.insider_tip) > 0)
                self.assertTrue(len(stop.transport_advice) > 0)

        # Verify markdown export
        md = itinerary.to_markdown()
        self.assertIn("# 🧭 Cleo Custom Itinerary: Cairo", md)
        self.assertIn("Day 1:", md)
        self.assertIn("Day 2:", md)
        self.assertIn("Day 3:", md)

    def test_fastapi_rest_endpoints(self):
        """Verifies FastAPI REST API endpoints using TestClient."""
        client = TestClient(app)

        # 1. Health check
        h_res = client.get("/api/v1/health")
        self.assertEqual(h_res.status_code, 200)
        self.assertEqual(h_res.json()["status"], "healthy")

        # 2. Chat endpoint
        chat_payload = {
            "session_id": "test_fastapi_session",
            "message": "I want to explore historic sites in Alexandria without crowded spots, budget style.",
        }
        c_res = client.post("/api/v1/chat", json=chat_payload)
        self.assertEqual(c_res.status_code, 200)
        c_data = c_res.json()
        self.assertEqual(c_data["session_id"], "test_fastapi_session")
        self.assertGreater(len(c_data["recommendations"]), 0)
        self.assertEqual(c_data["user_profile"]["target_city"], "Alexandria")

        # 3. Itinerary endpoint
        itin_payload = {
            "session_id": "test_fastapi_session",
            "days_count": 2,
            "pace": "moderate",
        }
        i_res = client.post("/api/v1/itinerary", json=itin_payload)
        self.assertEqual(i_res.status_code, 200)
        i_data = i_res.json()
        self.assertEqual(i_data["city"], "Alexandria")
        self.assertEqual(len(i_data["days"]), 2)

        # 4. Get session state
        s_res = client.get("/api/v1/session/test_fastapi_session")
        self.assertEqual(s_res.status_code, 200)
        s_data = s_res.json()
        self.assertEqual(s_data["session_id"], "test_fastapi_session")
        self.assertIn("crowded", s_data["profile"]["negative_constraints"])

        # 5. Delete session
        d_res = client.delete("/api/v1/session/test_fastapi_session")
        self.assertEqual(d_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()

