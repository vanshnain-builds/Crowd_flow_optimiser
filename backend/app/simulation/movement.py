from __future__ import annotations

"""
Agent movement simulation.
Moves SimAgents along edges, handles arrival, congestion slow-down,
and agent replanning when edges become unavailable.
"""

import math
import random
from typing import TYPE_CHECKING

from app.simulation.crowd import SimAgent, CrowdGroup
from app.graph.graph import VenueGraph
from app.graph.nodes import GraphNode

if TYPE_CHECKING:
    pass

MAX_AGENTS_RENDERED = 1400   # visual cap — matches frontend constant


def spawn_agents(
    groups: list[CrowdGroup],
    sim_time_min: float,
    dt_sec: float,
    speed_mult: float,
    graph: VenueGraph,
    agents: list[SimAgent],
    next_agent_id: list[int],
    rng: random.Random,
    path_cache: dict[tuple[str, str], list[str] | None],
) -> int:
    """Spawn new agents for groups that are currently in their arrival window."""
    spawned_count = 0

    for grp in groups:
        if grp.remaining_to_spawn <= 0:
            continue
        if sim_time_min < grp.arrival_start_min or sim_time_min > grp.arrival_end_min:
            continue

        rate = grp.spawn_rate_per_min()
        to_spawn_float = rate * (dt_sec / 60.0) * speed_mult
        n = min(
            int(to_spawn_float) + (1 if rng.random() < (to_spawn_float % 1) else 0),
            grp.remaining_to_spawn,
            MAX_AGENTS_RENDERED - len(agents),
        )

        for _ in range(n):
            if len(agents) >= MAX_AGENTS_RENDERED:
                break
            agent = _spawn_one(grp, graph, next_agent_id, rng, path_cache)
            if agent:
                agents.append(agent)
                grp.spawned += 1
                grp.active += 1
                spawned_count += 1

    return spawned_count


def _spawn_one(
    grp: CrowdGroup,
    graph: VenueGraph,
    next_agent_id: list[int],
    rng: random.Random,
    path_cache: dict[tuple[str, str], list[str] | None],
) -> SimAgent | None:
    start_node = graph.get_node(grp.entry_gate_id)
    if start_node is None:
        return None

    cache_key = (grp.entry_gate_id, grp.destination_node_id)
    if cache_key not in path_cache:
        path_cache[cache_key] = graph.find_path(grp.entry_gate_id, grp.destination_node_id)
    path = path_cache[cache_key]

    if not path or len(path) < 2:
        return None

    first_edge = graph.get_edge_between(path[0], path[1])
    if first_edge is None or not first_edge.is_traversable:
        # Try to find alternative first step
        for neighbor, eid in graph.neighbors(path[0]):
            e = graph.get_edge(eid)
            if e and e.is_traversable:
                first_edge = e
                path = [path[0], neighbor] + path[2:]
                break
        else:
            return None

    aid = next_agent_id[0]
    next_agent_id[0] += 1

    return SimAgent(
        id=aid,
        x=start_node.x + (rng.random() - 0.5) * 20,
        y=start_node.y + (rng.random() - 0.5) * 20,
        vx=0.0, vy=0.0,
        group_id=grp.id,
        from_node_id=path[0],
        to_node_id=path[1],
        edge_id=first_edge.id,
        progress=0.0,
        speed=40.0 + rng.random() * 30.0,
        destination_node_id=grp.destination_node_id,
    )


def move_agents(
    agents: list[SimAgent],
    dt_sec: float,
    speed_mult: float,
    graph: VenueGraph,
    groups: list[CrowdGroup],
    rng: random.Random,
    path_cache: dict[tuple[str, str], list[str] | None],
) -> tuple[list[SimAgent], int]:
    """
    Move all agents one timestep. Returns (remaining_agents, exited_count).
    """
    remaining: list[SimAgent] = []
    exited_count = 0
    group_map = {g.id: g for g in groups}

    for a in agents:
        edge = graph.get_edge(a.edge_id)

        # Edge closed under agent — replan
        if edge is None or not edge.is_traversable:
            success = _replan_agent(a, graph, group_map, rng, path_cache)
            if success:
                remaining.append(a)
            else:
                exited_count += 1  # stuck, treat as exited for now
            continue

        from_node = graph.get_node(a.from_node_id)
        to_node = graph.get_node(a.to_node_id)
        if from_node is None or to_node is None:
            continue

        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        length = math.hypot(dx, dy)

        if length < 0.1:
            _advance_agent(a, graph, group_map, remaining, rng, path_cache)
            if a.edge_id:
                remaining.append(a) if a not in remaining else None
            continue

        congestion_factor = max(0.2, 1.0 - edge.density * 0.7)
        step = (a.speed * congestion_factor * dt_sec * speed_mult) / length
        a.progress += step

        if a.progress >= 1.0:
            arrived = a.to_node_id
            if arrived == a.destination_node_id:
                # Destination reached
                grp = group_map.get(a.group_id)
                if grp:
                    grp.active -= 1
                    grp.exited += 1
                exited_count += 1
            else:
                _replan_agent(a, graph, group_map, rng, path_cache, from_node=arrived)
                remaining.append(a)
        else:
            a.x = from_node.x + dx * a.progress
            a.y = from_node.y + dy * a.progress
            a.vx = dx / length
            a.vy = dy / length
            remaining.append(a)

    return remaining, exited_count


def _advance_agent(
    a: SimAgent,
    graph: VenueGraph,
    group_map: dict[str, CrowdGroup],
    remaining: list[SimAgent],
    rng: random.Random,
    path_cache: dict[tuple[str, str], list[str] | None],
) -> None:
    arrived = a.to_node_id
    if arrived == a.destination_node_id:
        grp = group_map.get(a.group_id)
        if grp:
            grp.active -= 1
            grp.exited += 1
        a.edge_id = ""
    else:
        _replan_agent(a, graph, group_map, rng, path_cache, from_node=arrived)


def _replan_agent(
    a: SimAgent,
    graph: VenueGraph,
    group_map: dict[str, CrowdGroup],
    rng: random.Random,
    path_cache: dict[tuple[str, str], list[str] | None],
    from_node: str | None = None,
) -> bool:
    """Replan agent path. Returns True if successful."""
    here = from_node or a.to_node_id
    grp = group_map.get(a.group_id)
    if grp is None:
        return False

    dest = grp.destination_node_id
    # Always recompute (avoids stale cache after edge closures)
    path = graph.find_path(here, dest)
    path_cache[(here, dest)] = path

    if not path or len(path) < 2:
        return False

    e = graph.get_edge_between(path[0], path[1])
    if e is None or not e.is_traversable:
        return False

    from_n = graph.get_node(path[0])
    a.from_node_id = path[0]
    a.to_node_id = path[1]
    a.edge_id = e.id
    a.progress = 0.0
    if from_n:
        a.x = from_n.x
        a.y = from_n.y
    return True


def update_edge_metrics(agents: list[SimAgent], graph: VenueGraph) -> None:
    """Update flow/density on all edges based on current agent distribution."""
    counts: dict[str, int] = {}
    for a in agents:
        if a.edge_id:
            counts[a.edge_id] = counts.get(a.edge_id, 0) + 1

    # Reset all edges
    for e in graph.edges.values():
        e.flow = 0.0
        e.density = 0.0

    # Update from counts
    for edge_id, count in counts.items():
        e = graph.get_edge(edge_id)
        if e is None:
            continue
        cap = max(e.capacity * 0.08, 8)
        e.density = min(1.0, count / cap)
        e.flow = round(count * 2.0, 1)

        if e.status in ("emergency-closed", "closed"):
            continue
        if e.density > 0.8:
            e.status = "congested"
        else:
            e.status = "open"
