from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.ai.training.federated_learner import federated_learner

router = APIRouter(prefix="/federated", tags=["federated-learning"])

class RegisterRequest(BaseModel):
    name: str
    port: int = 8000

class PeerRequest(BaseModel):
    name: str
    host: str
    port: int

class StartRoundRequest(BaseModel):
    adapter_name: str = "default"

class ContributeRequest(BaseModel):
    adapter_path: str
    epsilon: float = 1.0

class ReceiveRequest(BaseModel):
    delta: List[Any]
    epsilon_spent: float
    peer_id: str
    adapter_name: Optional[str] = None

@router.post("/register")
async def register_self(req: RegisterRequest):
    federated_learner.register_self(name=req.name, port=req.port)
    return {"status": "success", "peer_id": federated_learner.self_peer_id}

@router.post("/peers")
async def add_peer(req: PeerRequest):
    peer = federated_learner.add_peer(name=req.name, host=req.host, port=req.port)
    return {"status": "success", "peer": peer}

@router.get("/peers")
async def get_peers():
    return federated_learner.get_peers()

@router.post("/discover")
async def discover_peers():
    peers = federated_learner.discover_peers()
    return {"status": "success", "discovered": len(peers)}

@router.post("/rounds/start")
async def start_round(req: StartRoundRequest):
    rnd = federated_learner.start_round(adapter_name=req.adapter_name)
    return rnd

@router.post("/rounds/{round_id}/contribute")
async def contribute(round_id: str, req: ContributeRequest):
    rnd = federated_learner.get_round(round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
        
    delta_data = federated_learner.generate_weight_delta(adapter_path=req.adapter_path, epsilon=req.epsilon)
    success = federated_learner.receive_delta(round_id, delta_data)
    
    if success:
        return {"status": "success", "epsilon_spent": delta_data["epsilon_spent"]}
    else:
        raise HTTPException(status_code=400, detail="Failed to contribute delta")

@router.post("/rounds/{round_id}/receive")
async def receive_delta(round_id: str, req: ReceiveRequest):
    delta_dict = {
        "delta": req.delta,
        "epsilon_spent": req.epsilon_spent,
        "peer_id": req.peer_id,
        "adapter_name": req.adapter_name
    }
    success = federated_learner.receive_delta(round_id, delta_dict)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Failed to receive delta")

@router.post("/rounds/{round_id}/aggregate")
async def aggregate_round(round_id: str):
    rnd = federated_learner.complete_round(round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    return rnd

@router.get("/rounds")
async def get_rounds(limit: int = 20):
    return federated_learner.get_rounds(limit=limit)

@router.get("/rounds/{round_id}")
async def get_round(round_id: str):
    rnd = federated_learner.get_round(round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    return rnd

@router.get("/stats")
async def get_stats():
    return federated_learner.get_stats()
