import unittest
from src.schemas import (
    ExtractedPreferences,
    MatchedLandmark,
    AgentRecommendationResponse,
    UserSession,
)
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent


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


if __name__ == "__main__":
    unittest.main()
