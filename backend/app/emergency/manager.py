from __future__ import annotations

"""
Emergency event manager.
Handles emergency events: closes edges/nodes, recalculates routes,
triggers AI safety analysis. Simulation continues through emergencies.
"""

import time
from typing import TYPE_CHECKING

from app.graph.graph import VenueGraph
from app.simulation.state import EmergencyRecord, SimulationRuntimeState
from app.routing.dynamic_router import recompute_routes, build_default_routes
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

log = get_logger(__name__)

_EMERGENCY_TYPE_LABELS = {
    "fire": "Fire",
    "medical": "Medical incident",
    "structural": "Structural failure",
    "security": "Security threat",
    "crowd-crush": "Crowd crush risk",
    "gate-failure": "Gate failure",
}


def trigger_emergency(
    sim_state: SimulationRuntimeState,
    graph: VenueGraph,
    emergency_type: str,
    node_id: str,
) -> EmergencyRecord:
    """
    Trigger an emergency at node_id.
    Closes all edges connected to the node, recalculates routes.
    """
    if sim_state.emergency and sim_state.emergency.active:
        raise ValueError("An emergency is already active")

    node = graph.get_node(node_id)
    if node is None:
        raise ValueError(f"Node '{node_id}' not found")

    type_label = _EMERGENCY_TYPE_LABELS.get(emergency_type, emergency_type)

    # Close edges around the node
    closed_ids = graph.close_node_edges(node_id)
    for eid in closed_ids:
        sim_state.disabled_edges.add(eid)

    # Invalidate path cache — must recompute with new disabled edges
    sim_state.path_cache.clear()

    em = EmergencyRecord(
        id=f"em-{int(time.time())}",
        type=emergency_type,
        location=node.label,
        node_id=node_id,
        at_minute=sim_state.sim_time_min,
        active=True,
        closed_edge_ids=closed_ids,
        summary=(
            f"{type_label} reported at {node.label}. "
            f"{len(closed_ids)} route segment(s) disabled and rerouting initiated."
        ),
    )
    sim_state.emergency = em

    # Recompute routes
    updated_routes, changes = recompute_routes(
        sim_state.routes,
        graph,
        sim_state.disabled_edges,
        sim_state.sim_time_min,
        emergency_location=node.label,
    )
    sim_state.routes = updated_routes
    sim_state.route_changes = changes + sim_state.route_changes

    sim_state.push_timeline(
        "emergency",
        f"EMERGENCY: {type_label} at {node.label}",
        f"{len(closed_ids)} route segment(s) disabled. Rerouting in progress.",
        severity="emergency",
    )

    log.warning(
        "Emergency triggered | type=%s node=%s closed_edges=%s",
        emergency_type, node_id, closed_ids,
    )
    return em


def clear_emergency(
    sim_state: SimulationRuntimeState,
    graph: VenueGraph,
) -> None:
    """
    Clear the active emergency.
    Reopens previously closed edges, recalculates routes.
    """
    em = sim_state.emergency
    if em is None:
        return

    em.active = False

    # Reopen edges
    for eid in em.closed_edge_ids:
        graph.open_edge(eid)
        sim_state.disabled_edges.discard(eid)

    # Invalidate path cache
    sim_state.path_cache.clear()

    # Recompute routes
    updated_routes, changes = recompute_routes(
        sim_state.routes,
        graph,
        sim_state.disabled_edges,
        sim_state.sim_time_min,
    )
    sim_state.routes = updated_routes
    sim_state.route_changes = changes + sim_state.route_changes

    sim_state.push_timeline(
        "emergency",
        "Emergency cleared",
        f"{em.location} reopened. Routes restored.",
    )

    sim_state.emergency = None
    log.info("Emergency cleared | location=%s", em.location)
