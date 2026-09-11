import json
import os
import uuid
import hashlib
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
from app.core.logger import logger

@dataclass
class FederatedPeer:
    peer_id: str  # uuid4 or hash
    name: str  # Human-readable name (e.g., "COPPER-Home", "COPPER-Work")
    host: str  # IP/hostname
    port: int  # Port
    last_seen: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    status: str = "discovered"  # discovered, connected, syncing, synced, offline
    rounds_participated: int = 0

@dataclass
class FederatedRound:
    round_id: str  # uuid4
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, aggregating, completed, failed
    peers_contributed: list[str] = field(default_factory=list)  # peer_ids
    adapter_name: str = ""  # Which adapter was improved
    delta_count: int = 0  # Number of weight deltas received
    privacy_epsilon_spent: float = 0.0  # Total privacy cost for this round
    improvement_metric: float = 0.0  # Measured improvement (if any)

class FederatedLearner:
    def __init__(self):
        self.config_path = "data/federated_config.json"
        self.rounds_path = "data/federated_rounds.json"
        self.self_peer_id = None
        self.self_name = None
        self.port = 8000
        self.peers = {} # peer_id -> FederatedPeer
        self.rounds = {} # round_id -> FederatedRound
        self.active_deltas = {} # round_id -> list of deltas
        os.makedirs("data", exist_ok=True)
        self._load_config()
        self._load_rounds()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.self_peer_id = data.get("self_peer_id")
                    self.self_name = data.get("self_name")
                    self.port = data.get("port", 8000)
                    for p in data.get("peers", []):
                        if p.get("last_seen"): p["last_seen"] = datetime.fromisoformat(p["last_seen"])
                        if p.get("last_sync"): p["last_sync"] = datetime.fromisoformat(p["last_sync"])
                        peer = FederatedPeer(**p)
                        self.peers[peer.peer_id] = peer
            except Exception as e:
                logger.error(f"Error loading federated config: {e}")
                self.self_peer_id = str(uuid.uuid4())
        else:
            self.self_peer_id = str(uuid.uuid4())

    def _save_config(self):
        data = {
            "self_peer_id": self.self_peer_id,
            "self_name": self.self_name,
            "port": self.port,
            "peers": []
        }
        for p in self.peers.values():
            p_dict = asdict(p)
            if p_dict["last_seen"]: p_dict["last_seen"] = p_dict["last_seen"].isoformat()
            if p_dict["last_sync"]: p_dict["last_sync"] = p_dict["last_sync"].isoformat()
            data["peers"].append(p_dict)
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=4)

    def _load_rounds(self):
        if os.path.exists(self.rounds_path):
            try:
                with open(self.rounds_path, "r") as f:
                    data = json.load(f)
                    for r in data:
                        if r.get("started_at"): r["started_at"] = datetime.fromisoformat(r["started_at"])
                        if r.get("completed_at"): r["completed_at"] = datetime.fromisoformat(r["completed_at"])
                        rnd = FederatedRound(**r)
                        self.rounds[rnd.round_id] = rnd
            except Exception as e:
                logger.error(f"Error loading federated rounds: {e}")

    def _save_rounds(self):
        data = []
        for r in self.rounds.values():
            r_dict = asdict(r)
            if r_dict["started_at"]: r_dict["started_at"] = r_dict["started_at"].isoformat()
            if r_dict["completed_at"]: r_dict["completed_at"] = r_dict["completed_at"].isoformat()
            data.append(r_dict)
        with open(self.rounds_path, "w") as f:
            json.dump(data, f, indent=4)

    def register_self(self, name: str, port: int = 8000):
        self.self_name = name
        self.port = port
        import socket
        hostname = socket.gethostname()
        self.self_peer_id = hashlib.sha256(hostname.encode()).hexdigest()[:16]
        self._save_config()
        logger.info(f"Registered self as federated peer: {name} ({self.self_peer_id})")

    def add_peer(self, name: str, host: str, port: int) -> FederatedPeer:
        peer_id = hashlib.sha256(f"{host}:{port}".encode()).hexdigest()[:16]
        peer = FederatedPeer(
            peer_id=peer_id,
            name=name,
            host=host,
            port=port,
            last_seen=datetime.now(timezone.utc)
        )
        self.peers[peer_id] = peer
        self._save_config()
        logger.info(f"Added federated peer: {name} at {host}:{port}")
        return peer

    def discover_peers(self) -> list[FederatedPeer]:
        # Placeholder for actual mDNS / network discovery
        for p in self.peers.values():
            p.last_seen = datetime.now(timezone.utc)
            p.status = "connected"
        self._save_config()
        logger.info(f"Discovered {len(self.peers)} peers")
        return list(self.peers.values())

    def generate_weight_delta(self, adapter_path: str, epsilon: float = 1.0) -> dict:
        logger.info(f"Generating weight delta for adapter {adapter_path} with epsilon {epsilon}")
        
        # Fake delta for now
        shape = (10, 10)
        raw_delta = np.random.normal(0, 0.1, shape)
        
        # Apply differential privacy noise
        sensitivity = 1.0 
        noise_scale = sensitivity / epsilon
        noise = np.random.laplace(0, noise_scale, shape)
        noised_delta = raw_delta + noise

        delta_dict = {
            "delta": noised_delta.tolist(),
            "epsilon_spent": epsilon,
            "adapter_name": adapter_path,
            "peer_id": self.self_peer_id
        }
        return delta_dict

    def receive_delta(self, round_id: str, delta: dict) -> bool:
        if round_id not in self.rounds:
            logger.warning(f"Received delta for unknown round {round_id}")
            return False
        
        rnd = self.rounds[round_id]
        if rnd.status != "in_progress":
            logger.warning(f"Received delta for completed round {round_id}")
            return False

        if round_id not in self.active_deltas:
            self.active_deltas[round_id] = []
            
        self.active_deltas[round_id].append(delta)
        rnd.delta_count += 1
        rnd.privacy_epsilon_spent += delta.get("epsilon_spent", 0.0)
        
        peer_id = delta.get("peer_id")
        if peer_id and peer_id not in rnd.peers_contributed:
            rnd.peers_contributed.append(peer_id)
            if peer_id in self.peers:
                self.peers[peer_id].rounds_participated += 1
                self.peers[peer_id].last_sync = datetime.now(timezone.utc)
                self._save_config()
                
        self._save_rounds()
        logger.info(f"Received delta for round {round_id} from {peer_id}")
        return True

    def aggregate_deltas(self, round_id: str) -> dict:
        if round_id not in self.active_deltas or not self.active_deltas[round_id]:
            logger.warning(f"No deltas to aggregate for round {round_id}")
            return {}

        deltas = self.active_deltas[round_id]
        logger.info(f"Aggregating {len(deltas)} deltas for round {round_id}")
        
        # FedAvg
        arrays = [np.array(d["delta"]) for d in deltas if "delta" in d]
        if not arrays:
            return {}
            
        avg_delta = np.mean(arrays, axis=0)
        
        return {
            "aggregated_delta": avg_delta.tolist(),
            "contributors_count": len(arrays)
        }

    def start_round(self, adapter_name: str = "default") -> FederatedRound:
        round_id = str(uuid.uuid4())
        rnd = FederatedRound(
            round_id=round_id,
            started_at=datetime.now(timezone.utc),
            adapter_name=adapter_name
        )
        self.rounds[round_id] = rnd
        self.active_deltas[round_id] = []
        self._save_rounds()
        logger.info(f"Started federated round {round_id} for adapter {adapter_name}")
        return rnd

    def complete_round(self, round_id: str) -> Optional[FederatedRound]:
        if round_id not in self.rounds:
            return None
            
        rnd = self.rounds[round_id]
        if rnd.status != "in_progress":
            return rnd
            
        rnd.status = "aggregating"
        
        # Aggregate
        aggregated = self.aggregate_deltas(round_id)
        
        rnd.status = "completed"
        rnd.completed_at = datetime.now(timezone.utc)
        
        # Clean up memory
        if round_id in self.active_deltas:
            del self.active_deltas[round_id]
            
        self._save_rounds()
        logger.info(f"Completed federated round {round_id}")
        return rnd

    def get_peers(self) -> list[FederatedPeer]:
        return list(self.peers.values())

    def get_rounds(self, limit: int = 20) -> list[FederatedRound]:
        sorted_rounds = sorted(self.rounds.values(), key=lambda r: r.started_at, reverse=True)
        return sorted_rounds[:limit]

    def get_round(self, round_id: str) -> Optional[FederatedRound]:
        return self.rounds.get(round_id)

    def get_stats(self) -> dict:
        total_peers = len(self.peers)
        active_peers = sum(1 for p in self.peers.values() if p.status == "connected")
        total_rounds = len(self.rounds)
        total_eps = sum(r.privacy_epsilon_spent for r in self.rounds.values())
        
        completed = [r for r in self.rounds.values() if r.status == "completed"]
        avg_imp = sum(r.improvement_metric for r in completed) / len(completed) if completed else 0.0
        
        return {
            "total_peers": total_peers,
            "active_peers": active_peers,
            "total_rounds": total_rounds,
            "total_epsilon_spent": total_eps,
            "avg_improvement": avg_imp
        }

federated_learner = FederatedLearner()
