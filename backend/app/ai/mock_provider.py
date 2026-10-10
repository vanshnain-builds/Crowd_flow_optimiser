from __future__ import annotations

"""
MockAIProvider — generates realistic mock analysis without HuggingFace.
Used when HF_TOKEN is unavailable or AI_PROVIDER_MODE=mock.
The simulation runs identically with this provider.
"""

import time
from datetime import datetime, timezone
from typing import Any

from app.ai.provider import AIProvider
from app.ai.schemas import (
    ScenarioParseResult, ParsedScenario, SafetyAnalysis,
    EntryDistributionItem, EventTimingInfo, CrowdGroupInfo,
)
from app.core.logging import get_logger

log = get_logger(__name__)


class MockAIProvider(AIProvider):
    """
    Deterministic mock AI provider.
    Produces realistic-looking output for development/demo without network calls.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def is_available(self) -> bool:
        return True

    async def parse_scenario(self, text: str) -> ScenarioParseResult:
        """Simple regex-based extraction matching the frontend's interpretScenarioText."""
        import re
        log.info("MockAI: parsing scenario text (%d chars)", len(text))
        lower = text.lower()
        notes: list[str] = []

        # Crowd size
        crowd_size = 20000
        size_match = re.search(r"([\d,]+)\s*(?:people|attendees|persons|visitors|crowd|spectators)", text, re.I)
        if size_match:
            crowd_size = int(size_match.group(1).replace(",", ""))
            notes.append(f"Detected crowd size: {crowd_size:,}")
        else:
            notes.append("Crowd size not specified — defaulting to 20,000")

        # Event time
        start_min = 19 * 60  # default 7 PM
        time_match = re.search(r"(\d{1,2})\s*(?:am|pm)\b", text, re.I)
        if time_match:
            h = int(time_match.group(1))
            if "pm" in time_match.group(0).lower() and h < 12:
                h += 12
            start_min = h * 60
            notes.append(f"Event start: {h:02d}:00")

        # Entry distribution
        entry_dist = [
            EntryDistributionItem(gateId="gate-e", fraction=0.55),
            EntryDistributionItem(gateId="gate-w", fraction=0.30),
            EntryDistributionItem(gateId="gate-s", fraction=0.15),
        ]
        if "east gate" in lower or "gate a" in lower:
            entry_dist[0].fraction = 0.60
            entry_dist[1].fraction = 0.25
            entry_dist[2].fraction = 0.15
            notes.append("Primary entry: East Gate (60%)")
        elif "west gate" in lower or "gate b" in lower:
            entry_dist[0].fraction = 0.30
            entry_dist[1].fraction = 0.55
            entry_dist[2].fraction = 0.15
            notes.append("Primary entry: West Gate (55%)")
        elif "south gate" in lower:
            entry_dist[0].fraction = 0.30
            entry_dist[1].fraction = 0.20
            entry_dist[2].fraction = 0.50
            notes.append("Primary entry: South Gate (50%)")

        # Event type
        name = "Event"
        if any(w in lower for w in ["concert", "gig", "show", "performance"]):
            name = "Concert"
            notes.append("Event type: Concert")
        elif any(w in lower for w in ["match", "game", "sport", "ipl", "tournament"]):
            name = "Sporting Event"
            notes.append("Event type: Sporting Event")
        elif any(w in lower for w in ["festival", "fair"]):
            name = "Festival"
            notes.append("Event type: Festival")

        # Crowd groups
        groups = [
            CrowdGroupInfo(
                id="g-main", name="Main crowd",
                size=int(crowd_size * 0.65),
                entryGateId="gate-e", destinationNodeId="stage",
                arrivalStartMin=-60, arrivalEndMin=0,
            ),
            CrowdGroupInfo(
                id="g-west", name="West crowd",
                size=int(crowd_size * 0.25),
                entryGateId="gate-w", destinationNodeId="stage",
                arrivalStartMin=-50, arrivalEndMin=5,
            ),
            CrowdGroupInfo(
                id="g-food", name="Food court visitors",
                size=int(crowd_size * 0.10),
                entryGateId="gate-s", destinationNodeId="food-n",
                arrivalStartMin=-40, arrivalEndMin=20,
            ),
        ]

        if "halftime" in lower or "half time" in lower or "food court" in lower:
            notes.append("Halftime movement to food courts detected")

        parsed = ParsedScenario(
            name=name,
            venueId="venue-stadium-a",
            crowdSize=crowd_size,
            entryDistribution=entry_dist,
            crowdGroups=groups,
            timing=EventTimingInfo(
                startMinutesOfDay=start_min,
                durationMin=180,
                arrivalPattern="surge",
                departurePattern="surge",
            ),
            entryRate=min(crowd_size // 30, 800),
            exitRate=min(crowd_size // 20, 1000),
            naturalLanguage=text,
            notes=notes,
        )

        return ScenarioParseResult(
            success=True,
            parsed=parsed,
            stage="ready",
            notes=notes,
            raw_text=text,
        )

    async def analyze_safety(
        self,
        metrics: dict[str, Any],
        safety_state: dict[str, Any],
        sim_time_min: float,
        sim_status: str,
        emergency: dict | None = None,
        route_changes: list[dict] | None = None,
    ) -> SafetyAnalysis:
        """Generate a mock safety analysis from actual simulation data."""
        risk_level = safety_state.get("riskLevel", "low")
        risk_score = safety_state.get("riskScore", 0)
        bottlenecks = safety_state.get("bottlenecks", [])
        people = metrics.get("peopleCount", 0)
        density = metrics.get("avgDensity", 0.0)
        flow = metrics.get("flowRate", 0.0)
        cap_util = metrics.get("capacityUtilization", 0.0)

        if emergency and emergency.get("active"):
            return SafetyAnalysis(
                summary=f"Emergency at {emergency.get('location', 'unknown')} — immediate action required.",
                risk_explanation=(
                    f"An active {emergency.get('type', 'emergency')} event at {emergency.get('location')} "
                    f"has disabled routes, forcing crowd redistribution. "
                    f"{people:,} people are currently active in the venue."
                ),
                affected_locations=[emergency.get("location", "")],
                contributing_factors=["Active emergency", "Disabled routes", "Forced crowd redistribution"],
                recommended_action=(
                    f"Direct all crowd flow away from {emergency.get('location')}. "
                    "Activate emergency exits. Deploy staff to North Exit, SW Exit, and SE Exit. "
                    "Monitor alternative corridors for secondary bottlenecks."
                ),
                urgency="emergency",
                supporting_metrics={
                    "people_count": people,
                    "risk_score": risk_score,
                    "capacity_utilization": cap_util,
                },
                confidence="high",
            )

        if bottlenecks:
            bn = bottlenecks[0]
            pct = round(bn.get("capacityUtilization", 0) * 100)
            ttc = bn.get("timeToCriticalMin")
            ttc_str = f" Estimated time to critical: {ttc:.0f} min." if ttc else ""
            return SafetyAnalysis(
                summary=f"Congestion developing at {bn.get('location', 'unknown corridor')}.",
                risk_explanation=(
                    f"{bn.get('location')} is operating at {pct}% capacity with density "
                    f"{bn.get('currentDensity', 0):.0%}. Current flow rate is {flow:.0f} people/min. "
                    f"Risk level is {risk_level} ({risk_score}/100)."
                ),
                affected_locations=[bn.get("location", "")],
                contributing_factors=[
                    f"High density ({bn.get('currentDensity', 0):.0%})",
                    f"Capacity utilization at {pct}%",
                    "Insufficient outflow" if cap_util > 0.7 else "Queue growth",
                ],
                recommended_action=(
                    bn.get("recommendedAction", "Monitor and redirect flow.")
                    + ttc_str
                ),
                urgency=risk_level if risk_level in ("low", "moderate", "high", "critical", "emergency") else "moderate",
                supporting_metrics={
                    "capacity_utilization": bn.get("capacityUtilization"),
                    "current_density": bn.get("currentDensity"),
                    "risk_score": risk_score,
                    "flow_rate": flow,
                },
                confidence="high" if risk_level in ("critical", "high") else "medium",
            )

        return SafetyAnalysis(
            summary="Crowd conditions are within normal parameters.",
            risk_explanation=(
                f"All monitored corridors are below congestion thresholds. "
                f"Current crowd is {people:,} with average density {density:.0%}. "
                f"No bottlenecks detected. Risk score is {risk_score}/100."
            ),
            affected_locations=[],
            contributing_factors=["All edge densities below threshold", "Normal flow rates"],
            recommended_action="Continue routine monitoring. No intervention required at this time.",
            urgency="low",
            supporting_metrics={
                "people_count": people,
                "avg_density": density,
                "risk_score": risk_score,
                "flow_rate": flow,
            },
            confidence="high",
        )
