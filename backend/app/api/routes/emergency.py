from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import simulation_service
from app.emergency.manager import trigger_emergency, clear_emergency

router = APIRouter(prefix="/api/simulations", tags=["Emergency"])


class TriggerEmergencyRequest(BaseModel):
    type: str       # fire|medical|structural|security|crowd-crush|gate-failure
    node_id: str


@router.post("/{simulation_id}/emergency")
async def trigger_em(simulation_id: str, req: TriggerEmergencyRequest):
    engine = simulation_service.get_simulation(simulation_id)
    em = trigger_emergency(engine.state, engine.graph, req.type, req.node_id)
    return em.to_frontend_dict()


@router.delete("/{simulation_id}/emergency")
async def clear_em(simulation_id: str):
    engine = simulation_service.get_simulation(simulation_id)
    clear_emergency(engine.state, engine.graph)
    return {"status": "cleared"}
