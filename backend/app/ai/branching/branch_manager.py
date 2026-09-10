import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.ai.memory.persistent_memory import persistent_memory
from app.core.logger import logger

BRANCHES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "branches"
BRANCHES_DIR.mkdir(parents=True, exist_ok=True)
BRANCH_STORE_FILE = BRANCHES_DIR / "branch_store.json"


class BranchManager:
    """
    Manages conversation branching trees.
    Branches share history up to the divergence point, then diverge into independent timelines.
    """

    def __init__(self, storage_path: Path | str | None = None):
        self.storage_file = Path(storage_path) if storage_path else BRANCH_STORE_FILE
        self._store: dict[str, dict[str, Any]] = self._load_store()

    def _load_store(self) -> dict[str, dict[str, Any]]:
        try:
            if self.storage_file.exists():
                with open(self.storage_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load branch store, initializing fresh: {e}")
        return {}

    def _save_store(self) -> None:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save branch store: {e}")

    def _get_session_messages(self, session_id: str) -> list[dict[str, str]]:
        """Retrieves messages for a session from persistent memory or SQLite history."""
        # 1. Check persistent memory
        history = persistent_memory.get_history(session_id)
        if history:
            return [dict(m) for m in history]

        # 2. Check if it's an existing branch
        if session_id in self._store:
            return [dict(m) for m in self._store[session_id].get("messages", [])]

        # 3. Fallback to SQLite ChatHistory
        try:
            from app.database.models.history import ChatHistory
            from app.database.postgres import SessionLocal

            db = SessionLocal()
            try:
                records = (
                    db.query(ChatHistory)
                    .filter(ChatHistory.session_id == session_id)
                    .order_by(ChatHistory.created_at.asc())
                    .all()
                )
                if records:
                    return [{"role": r.sender, "content": r.message} for r in records]
            finally:
                db.close()
        except Exception as err:
            logger.debug(f"Could not load messages from DB: {err}")

        return []

    def branch_conversation(
        self,
        session_id: str,
        message_index: int,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Creates a new branch starting from `message_index`.
        Shares history up to the divergence point, then diverges into an isolated thread.
        """
        parent_messages = self._get_session_messages(session_id)
        if not parent_messages:
            raise ValueError(f"Session '{session_id}' has no messages to branch from.")

        # Clamp index
        if message_index < 0:
            message_index = 0
        if message_index >= len(parent_messages):
            message_index = len(parent_messages) - 1

        shared_slice = [dict(m) for m in parent_messages[: message_index + 1]]
        divergence_turn = parent_messages[message_index]

        # Resolve root session
        parent_branch = self._store.get(session_id)
        root_session_id = parent_branch.get("root_session_id", session_id) if parent_branch else session_id

        # Unique branch id
        branch_id = f"{session_id}_b{uuid.uuid4().hex[:6]}"
        auto_title = title or f"Branch @ turn {message_index + 1}: {divergence_turn.get('content', '')[:35]}..."

        branch_data: dict[str, Any] = {
            "branch_id": branch_id,
            "parent_session_id": session_id,
            "root_session_id": root_session_id,
            "divergence_index": message_index,
            "divergence_message": divergence_turn,
            "title": auto_title,
            "messages": shared_slice,
            "messages_count": len(shared_slice),
            "status": "active",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        # Store branch in local store
        self._store[branch_id] = branch_data
        self._save_store()

        # Register in persistent_memory.sessions so chat turns work immediately
        persistent_memory.sessions[branch_id] = [dict(m) for m in shared_slice]
        persistent_memory._save_sessions()

        logger.info(
            f"Created branch '{branch_id}' from '{session_id}' at turn {message_index + 1} "
            f"with {len(shared_slice)} initial messages"
        )
        return branch_data

    def list_branches(self, session_id: str) -> list[dict[str, Any]]:
        """
        Lists all branches associated with a conversation (both child branches and root).
        """
        # Determine root ID
        curr = self._store.get(session_id)
        root_id = curr.get("root_session_id", session_id) if curr else session_id

        branches: list[dict[str, Any]] = []

        # 1. Include Root / Main representation
        root_messages = self._get_session_messages(root_id)
        branches.append(
            {
                "branch_id": root_id,
                "parent_session_id": None,
                "root_session_id": root_id,
                "divergence_index": 0,
                "divergence_message": root_messages[0] if root_messages else None,
                "title": "Main Timeline",
                "messages_count": len(root_messages),
                "status": "active",
                "is_main": True,
            }
        )

        # 2. Include all child branches sharing this root
        for b_id, b_data in self._store.items():
            if b_data.get("root_session_id") == root_id or b_data.get("parent_session_id") == root_id:
                # Synchronize live message count from persistent memory
                live_msgs = persistent_memory.sessions.get(b_id, b_data.get("messages", []))
                entry = dict(b_data)
                entry["messages_count"] = len(live_msgs)
                entry["is_main"] = False
                branches.append(entry)

        return branches

    def get_branch(self, branch_id: str) -> dict[str, Any] | None:
        """Retrieves a single branch with synchronized latest messages."""
        if branch_id in self._store:
            data = dict(self._store[branch_id])
            # Sync with live persistent memory
            if branch_id in persistent_memory.sessions:
                data["messages"] = [dict(m) for m in persistent_memory.sessions[branch_id]]
            return data

        # Check if it's the main timeline
        history = self._get_session_messages(branch_id)
        if history:
            return {
                "branch_id": branch_id,
                "parent_session_id": None,
                "root_session_id": branch_id,
                "divergence_index": 0,
                "divergence_message": history[0] if history else None,
                "title": "Main Timeline",
                "messages": history,
                "status": "active",
                "is_main": True,
                "created_at": datetime.now(UTC).isoformat(),
            }

        return None

    def merge_branch(
        self,
        branch_id: str,
        target_session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Merges insights and divergent discoveries from a branch into the target session.
        """
        branch = self.get_branch(branch_id)
        if not branch:
            raise ValueError(f"Branch '{branch_id}' not found.")

        target_id = target_session_id or branch.get("parent_session_id") or branch.get("root_session_id")
        if not target_id:
            raise ValueError("Target session ID could not be determined.")

        div_idx = branch.get("divergence_index", 0)
        branch_msgs = branch.get("messages", [])
        divergent_msgs = branch_msgs[div_idx + 1 :]

        if not divergent_msgs:
            summary = f"Branch '{branch['title']}' has no new divergent turns beyond divergence point."
        else:
            # Build concise synthesized summary of new discoveries
            disc_lines = []
            for m in divergent_msgs:
                role = m.get("role", "assistant").capitalize()
                content = m.get("content", "").strip().replace("\n", " ")
                disc_lines.append(f"- {role}: {content[:180]}")
            summary = (
                f"Merged {len(divergent_msgs)} turn(s) from [{branch['title']}]:\n"
                + "\n".join(disc_lines[:6])
            )

        # Inject into target session history
        merge_notification = f"🔀 [Branch Merged: {branch['title']}]\n\n{summary}"
        persistent_memory.append_message(target_id, "assistant", merge_notification)

        # Update branch status in store
        if branch_id in self._store:
            self._store[branch_id]["status"] = "merged"
            self._store[branch_id]["merged_at"] = datetime.now(UTC).isoformat()
            self._store[branch_id]["merged_into"] = target_id
            self._save_store()

        logger.info(f"Merged branch '{branch_id}' into session '{target_id}'")
        return {
            "success": True,
            "status": "merged",
            "branch_id": branch_id,
            "target_session_id": target_id,
            "divergent_turn_count": len(divergent_msgs),
            "divergent_turns_count": len(divergent_msgs),
            "summary": summary,
        }


branch_manager = BranchManager()
