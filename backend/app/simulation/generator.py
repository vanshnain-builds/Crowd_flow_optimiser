from __future__ import annotations

"""
Deterministic crowd generator.
Creates CrowdGroup objects from scenario parameters.
Uses a seeded random for reproducible simulations.
"""

import random
from typing import Any

from app.simulation.crowd import CrowdGroup


def generate_crowd_groups(
    scenario: dict[str, Any],
    seed: int = 42,
) -> list[CrowdGroup]:
    """
    Build CrowdGroup list from a scenario dict.
    Scenario dict fields (matches frontend Scenario type):
      - crowdGroups: list of group dicts
      - crowdSize: int
      - entryDistribution: list of {gateId, fraction}
      - timing: {startMinutesOfDay, durationMin, arrivalPattern, departurePattern}
    """
    rng = random.Random(seed)

    # If explicit crowdGroups provided, use them directly
    if scenario.get("crowdGroups"):
        groups: list[CrowdGroup] = []
        for g in scenario["crowdGroups"]:
            groups.append(CrowdGroup(
                id=g["id"],
                name=g.get("name", g["id"]),
                total_size=g["size"],
                entry_gate_id=g["entryGateId"],
                destination_node_id=g["destinationNodeId"],
                arrival_start_min=float(g.get("arrivalStartMin", -60)),
                arrival_end_min=float(g.get("arrivalEndMin", 0)),
            ))
        return groups

    # Otherwise, auto-generate from distribution
    crowd_size = scenario.get("crowdSize", 10000)
    entry_dist = scenario.get("entryDistribution", [])
    timing = scenario.get("timing", {})
    arrival_pattern = timing.get("arrivalPattern", "surge")
    duration = float(timing.get("durationMin", 180))

    if not entry_dist:
        return []

    groups = []
    total_assigned = 0

    for i, dist in enumerate(entry_dist):
        gate_id = dist["gateId"]
        fraction = float(dist.get("fraction", 1.0 / len(entry_dist)))
        size = int(crowd_size * fraction)
        if i == len(entry_dist) - 1:
            size = crowd_size - total_assigned  # absorb rounding
        total_assigned += size

        # Arrival window based on pattern
        if arrival_pattern == "surge":
            start = -60.0
            end = 0.0
        elif arrival_pattern == "gradual":
            start = -90.0
            end = 30.0
        elif arrival_pattern == "peak-early":
            start = -60.0
            end = -10.0
        else:  # sustained
            start = -60.0
            end = duration * 0.5

        groups.append(CrowdGroup(
            id=f"g-auto-{gate_id}",
            name=f"Crowd via {gate_id}",
            total_size=size,
            entry_gate_id=gate_id,
            destination_node_id="stage",  # default destination
            arrival_start_min=start,
            arrival_end_min=end,
        ))

    return groups


def default_scenario_dict() -> dict:
    """Return the default Evening Concert scenario matching frontend DEFAULT_SCENARIO."""
    return {
        "id": "scenario-default",
        "name": "Evening Concert",
        "venueId": "venue-stadium-a",
        "crowdSize": 20000,
        "entryDistribution": [
            {"gateId": "gate-e", "fraction": 0.55},
            {"gateId": "gate-w", "fraction": 0.30},
            {"gateId": "gate-s", "fraction": 0.15},
        ],
        "crowdGroups": [
            {"id": "g-front", "name": "Front-of-stage crowd", "size": 9000,
             "entryGateId": "gate-e", "destinationNodeId": "stage",
             "arrivalStartMin": -60, "arrivalEndMin": 0},
            {"id": "g-mid", "name": "Mid-field crowd", "size": 7000,
             "entryGateId": "gate-e", "destinationNodeId": "stage",
             "arrivalStartMin": -45, "arrivalEndMin": 10},
            {"id": "g-west", "name": "West-side crowd", "size": 2500,
             "entryGateId": "gate-w", "destinationNodeId": "stage",
             "arrivalStartMin": -50, "arrivalEndMin": 5},
            {"id": "g-food", "name": "Food-court visitors", "size": 1500,
             "entryGateId": "gate-s", "destinationNodeId": "food-n",
             "arrivalStartMin": -40, "arrivalEndMin": 20},
        ],
        "timing": {
            "startMinutesOfDay": 1140,
            "durationMin": 180,
            "arrivalPattern": "surge",
            "departurePattern": "surge",
        },
        "entryRate": 600,
        "exitRate": 800,
        "specialConditions": [],
        "naturalLanguage": "A concert with 20,000 people starts at 7 PM. Most people enter through the east gate and food stalls are near the north corridor.",
    }
