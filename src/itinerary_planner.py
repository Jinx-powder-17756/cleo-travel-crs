from __future__ import annotations

import json
from collections import defaultdict
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from src.config import get_gemini_client, DEFAULT_MODEL
from src.schemas import (
    UserSession,
    MatchedLandmark,
    ItineraryStop,
    DayPlan,
    ItineraryPlan,
    TimeSlot,
)
from src.dataset import EgyptianLandmarksDataset


class SpatialItineraryPlanner:
    """
    Spatial Day-by-Day Itinerary Planner for Egyptian Tourism.
    Clusters candidate landmarks by geographic sub-district/neighborhood to eliminate
    zigzagging and long transit delays, sequencing visits chronologically by time-of-day.
    Supports Gemini Structured Outputs and deterministic offline heuristic planning.
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

    def plan_itinerary(
        self,
        session: UserSession,
        days_count: int = 3,
        pace: str = "moderate",
        candidate_landmarks: Optional[List[Dict[str, Any]]] = None,
    ) -> ItineraryPlan:
        """
        Generates a geographically optimized day-by-day itinerary plan:
        1. Identifies destination city and travel pace constraints.
        2. Gathers sufficient landmark candidates from user session & vector store.
        3. Clusters candidates by geographic district and chronological time slot.
        4. Synthesizes an optimal ItineraryPlan via Gemini or fallback planner.
        """
        days_count = max(1, min(int(days_count), 7))
        pace = pace.lower().strip()
        if pace not in ["relaxed", "moderate", "packed"]:
            pace = "moderate"

        profile = session.to_dict()
        city = profile.get("target_city") or "Cairo"

        # Determine target number of stops
        stops_per_day = {"relaxed": 2, "moderate": 3, "packed": 4}[pace]
        needed_candidates = days_count * stops_per_day

        # Collect candidate pool
        candidates = list(candidate_landmarks or [])
        if len(candidates) < needed_candidates:
            # Retrieve additional candidates from vector store matching user profile
            retrieved = self.dataset.retrieve_candidates(
                session_state=session,
                top_k=max(needed_candidates + 2, 8),
                exclude_recommended=False,
            )
            # Merge while keeping unique landmarks
            existing_names = {c["landmark_name"] for c in candidates}
            for r in retrieved:
                if r["landmark_name"] not in existing_names:
                    candidates.append(r)
                    existing_names.add(r["landmark_name"])

        # Fallback if catalog candidates in this city are scarce
        if not candidates:
            candidates = self.dataset.vector_store.search(
                query_text="famous top landmarks sights culture",
                top_k=needed_candidates,
                target_city=city,
            )

        if not self.client:
            return self._heuristic_plan_itinerary(city, days_count, pace, candidates, session)

        return self._gemini_plan_itinerary(city, days_count, pace, candidates, session)

    def _gemini_plan_itinerary(
        self,
        city: str,
        days_count: int,
        pace: str,
        candidates: List[Dict[str, Any]],
        session: UserSession,
    ) -> ItineraryPlan:
        """Invokes Gemini with structured output schema for spatial itinerary planning."""
        profile = session.to_dict()
        interests = ", ".join(profile.get("interests", [])) or "Egyptian heritage & landmarks"
        negatives = ", ".join(profile.get("negative_constraints", [])) or "None"
        price_pref = profile.get("price_preference") or "Flexible"

        # Build candidate summary with districts
        candidate_lines = []
        for i, c in enumerate(candidates, 1):
            district = c.get("district", c.get("city", "Central"))
            price = c.get("price_tier", "$$")
            duration = c.get("typical_duration_hours", 2.0)
            candidate_lines.append(
                f"[{i}] {c['landmark_name']} | District: {district} | Price: {price} | "
                f"Typical Duration: ~{duration}h | Category: {c['category']} | Ideal For: {c.get('ideal_for', '')}\n"
                f"    Description: {c.get('description', '')}"
            )
        candidate_catalog = "\n".join(candidate_lines)

        prompt = (
            f"=== TRAVELER SESSION PROFILE ===\n"
            f"Destination City: {city}\n"
            f"Requested Duration: {days_count} Days\n"
            f"Travel Pace: {pace} (relaxed: ~2 stops/day, moderate: ~3 stops/day, packed: ~4 stops/day)\n"
            f"Traveler Interests: {interests}\n"
            f"Negative Constraints to Exclude: {negatives}\n"
            f"Budget / Price Preference: {price_pref}\n\n"
            f"=== AVAILABLE CANDIDATE SITES & DISTRICTS ===\n"
            f"{candidate_catalog}\n\n"
            f"=== SPATIAL PLANNING RULES ===\n"
            f"1. GEOGRAPHIC CLUSTERING: Each day MUST focus on a single geographic sub-district or tightly adjacent neighborhoods "
            f"(e.g. in Cairo: keep Giza Pyramids together, Islamic Cairo together, Downtown/Tahrir together, Coptic Cairo together; in Luxor: East Bank vs West Bank). "
            f"NEVER force the traveler to cross the Nile multiple times in one day or zigzag across opposing ends of the metropolis.\n"
            f"2. CHRONOLOGICAL TIME SLOTS: Assign realistic time slots ('morning', 'afternoon', 'evening'). "
            f"Place open-air tombs and desert pyramids in the cool morning, indoor air-conditioned museums or craft workshops in the midday afternoon, and bustling bazaars or illuminated monuments in the evening.\n"
            f"3. PACING: Strictly follow {pace} pace ({days_count} days, total {len(candidates)} candidates available).\n"
            f"4. TRANSIT & TIPS: Provide specific transport advice between stops (e.g. '5-minute walk through Khan souks' or '15-minute taxi via Nile Corniche') and an insider tip for each stop."
        )

        system_instruction = (
            "You are an expert Egyptian spatial urban planner and licensed tour director. "
            "You create hyper-efficient, realistic, and delightful travel itineraries that eliminate transit friction. "
            "Group sights strictly by sub-district proximity and assign time slots appropriately."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ItineraryPlan,
                    temperature=0.2,
                ),
            )
            data = json.loads(response.text)
            return ItineraryPlan.model_validate(data)
        except Exception:
            return self._heuristic_plan_itinerary(city, days_count, pace, candidates, session)

    def _heuristic_plan_itinerary(
        self,
        city: str,
        days_count: int,
        pace: str,
        candidates: List[Dict[str, Any]],
        session: UserSession,
    ) -> ItineraryPlan:
        """
        Deterministic spatial clustering algorithm for offline execution and fast testing.
        Clusters landmarks by 'district' to avoid crisscrossing, then distributes across days.
        """
        stops_per_day = {"relaxed": 2, "moderate": 3, "packed": 4}.get(pace, 3)

        # Group candidates by district
        district_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for cand in candidates:
            dist = cand.get("district") or cand.get("city") or "Central"
            district_groups[dist].append(cand)

        # Sort districts by number of candidate matches
        sorted_districts = sorted(district_groups.keys(), key=lambda d: len(district_groups[d]), reverse=True)

        day_plans: List[DayPlan] = []
        assigned_landmark_names = set()

        time_slots_cycle = ["morning", "afternoon", "evening", "evening"]

        for day_idx in range(1, days_count + 1):
            # Pick primary district for this day
            primary_district = sorted_districts[(day_idx - 1) % len(sorted_districts)] if sorted_districts else city
            district_pool = [c for c in district_groups.get(primary_district, []) if c["landmark_name"] not in assigned_landmark_names]

            # If not enough in this district, borrow from other districts
            if len(district_pool) < stops_per_day:
                for d in sorted_districts:
                    if d != primary_district:
                        extras = [c for c in district_groups[d] if c["landmark_name"] not in assigned_landmark_names]
                        district_pool.extend(extras)
                        if len(district_pool) >= stops_per_day:
                            break

            day_candidates = district_pool[:stops_per_day]
            if not day_candidates:
                # Reuse if exhausted
                day_candidates = candidates[:stops_per_day]

            stops: List[ItineraryStop] = []
            prev_cand: Optional[Dict[str, Any]] = None

            for s_idx, cand in enumerate(day_candidates):
                assigned_landmark_names.add(cand["landmark_name"])
                slot = time_slots_cycle[s_idx % len(time_slots_cycle)]
                duration = float(cand.get("typical_duration_hours", 2.0))

                # Compute realistic transit advice
                if prev_cand is None:
                    transit = "Depart from hotel / morning accommodation via local taxi or ride-hailing app."
                elif prev_cand.get("district") == cand.get("district"):
                    transit = f"Short 5-10 min walk or quick taxi ride within {cand.get('district', primary_district)}."
                else:
                    transit = f"~20 min transfer from {prev_cand.get('district', 'previous stop')} to {cand.get('district', primary_district)}."

                tip = f"Ideal for {cand.get('ideal_for', 'all travelers')}. Best experienced during the {slot} hours."

                stop = ItineraryStop(
                    time_slot=slot,
                    landmark_name=cand["landmark_name"],
                    category=cand.get("category"),
                    district=cand.get("district", primary_district),
                    duration_hours=duration,
                    insider_tip=tip,
                    transport_advice=transit,
                    price_tier=cand.get("price_tier", "$$"),
                    matched_landmark=MatchedLandmark(
                        landmark_name=cand["landmark_name"],
                        city=cand["city"],
                        category=cand.get("category", "Heritage"),
                        match_score=cand.get("score", 1.0),
                        why_matched=f"Selected for Day {day_idx} clustering in {cand.get('district', primary_district)}.",
                        highlight_tip=tip,
                        district=cand.get("district", primary_district),
                        price_tier=cand.get("price_tier", "$$"),
                    ),
                )
                stops.append(stop)
                prev_cand = cand

            theme = f"{primary_district} District & Highlights"
            rationale = (
                f"Spatially clustered stops within or neighboring {primary_district} to minimize transit "
                f"times and maintain an efficient {pace} travel rhythm."
            )
            day_plans.append(
                DayPlan(
                    day_number=day_idx,
                    theme_or_district=theme,
                    stops=stops,
                    route_rationale=rationale,
                )
            )

        summary = (
            f"A curated {days_count}-day {pace} journey through {city}, strategically clustered "
            f"by geographic districts to prevent unnecessary transit delays while exploring top landmarks."
        )

        return ItineraryPlan(
            city=city,
            total_days=days_count,
            pace=pace,
            summary=summary,
            days=day_plans,
        )
