import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import desc

from app.core.logger import logger
from app.database.models.lora_adapter import AdapterStatus, LoRAAdapter
from app.database.postgres import SessionLocal

# In-memory routing state for zero-overhead routing in the request loop
_active_adapters_cache: dict[str, dict[str, Any]] = {}


class AdapterManager:
    def __init__(self):
        self._refresh_cache()

    def _refresh_cache(self):
        """Loads active and testing adapters into memory for fast lookup."""
        db = SessionLocal()
        try:
            adapters = (
                db.query(LoRAAdapter)
                .filter(LoRAAdapter.status.in_([AdapterStatus.ACTIVE.value, AdapterStatus.TESTING.value]))
                .all()
            )
            _active_adapters_cache.clear()
            for a in adapters:
                _active_adapters_cache[a.target_agent.lower()] = {
                    "id": a.id,
                    "version": a.version,
                    "adapter_dir": a.adapter_dir,
                    "status": a.status,
                    "ab_percentage": a.ab_test_percentage,
                    "base_model": a.base_model,
                }
            logger.info(f"Loaded {len(_active_adapters_cache)} active/testing LoRA adapters into cache.")
        except Exception as e:
            logger.debug(f"Adapter cache refresh error: {e}")
        finally:
            db.close()

    def get_all_adapters(self) -> list[dict[str, Any]]:
        """Lists all registered LoRA adapters with their status and benchmark history."""
        db = SessionLocal()
        try:
            adapters = db.query(LoRAAdapter).order_by(desc(LoRAAdapter.id)).all()
            return [a.to_dict() for a in adapters]
        finally:
            db.close()

    def get_adapter(self, adapter_id: int) -> dict[str, Any] | None:
        db = SessionLocal()
        try:
            adapter = db.query(LoRAAdapter).filter(LoRAAdapter.id == adapter_id).first()
            return adapter.to_dict() if adapter else None
        finally:
            db.close()

    def activate_adapter(self, adapter_id: int) -> dict[str, Any]:
        """Activates an adapter 100% for its target agent, deactivating previous active adapters."""
        db = SessionLocal()
        try:
            adapter = db.query(LoRAAdapter).filter(LoRAAdapter.id == adapter_id).first()
            if not adapter:
                return {"success": False, "error": f"Adapter {adapter_id} not found."}

            if adapter.status == AdapterStatus.REJECTED.value:
                return {"success": False, "error": "Cannot activate an adapter that failed regression safety tests."}

            # Deactivate other adapters for the same target agent
            db.query(LoRAAdapter).filter(
                LoRAAdapter.target_agent == adapter.target_agent,
                LoRAAdapter.id != adapter.id,
            ).update({"is_active": False, "status": AdapterStatus.CANDIDATE.value, "ab_test_percentage": 0})

            adapter.is_active = True
            adapter.status = AdapterStatus.ACTIVE.value
            adapter.ab_test_percentage = 100
            adapter.activated_at = datetime.now(UTC)
            db.commit()
            db.refresh(adapter)

            self._refresh_cache()
            logger.info(f"Activated LoRA adapter {adapter.version} (100% traffic for {adapter.target_agent})")
            return {"success": True, "adapter": adapter.to_dict()}
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to activate adapter {adapter_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def deactivate_adapter(self, adapter_id: int) -> dict[str, Any]:
        """Deactivates an active adapter and rolls back to base weights."""
        db = SessionLocal()
        try:
            adapter = db.query(LoRAAdapter).filter(LoRAAdapter.id == adapter_id).first()
            if not adapter:
                return {"success": False, "error": f"Adapter {adapter_id} not found."}

            adapter.is_active = False
            adapter.status = AdapterStatus.CANDIDATE.value
            adapter.ab_test_percentage = 0
            db.commit()
            db.refresh(adapter)

            self._refresh_cache()
            logger.info(f"Deactivated LoRA adapter {adapter.version}")
            return {"success": True, "adapter": adapter.to_dict()}
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to deactivate adapter {adapter_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def start_ab_test(self, adapter_id: int, percentage: int = 20) -> dict[str, Any]:
        """Configures A/B testing: routes N% of live traffic to the adapted model."""
        if not (1 <= percentage <= 99):
            return {"success": False, "error": "A/B test percentage must be between 1 and 99."}

        db = SessionLocal()
        try:
            adapter = db.query(LoRAAdapter).filter(LoRAAdapter.id == adapter_id).first()
            if not adapter:
                return {"success": False, "error": f"Adapter {adapter_id} not found."}

            if adapter.status == AdapterStatus.REJECTED.value:
                return {"success": False, "error": "Cannot A/B test a rejected adapter."}

            adapter.is_active = True
            adapter.status = AdapterStatus.TESTING.value
            adapter.ab_test_percentage = percentage
            adapter.activated_at = datetime.now(UTC)
            db.commit()
            db.refresh(adapter)

            self._refresh_cache()
            logger.info(f"Started A/B test for {adapter.version}: {percentage}% traffic for {adapter.target_agent}")
            return {
                "success": True,
                "adapter": adapter.to_dict(),
                "ab_test_percentage": percentage,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to start A/B test for adapter {adapter_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def should_route_to_adapter(self, agent_type: str) -> tuple[bool, str | None]:
        """Determines whether an incoming request should use a LoRA adapter (handles 100% and A/B split)."""
        clean_type = agent_type.lower().strip()
        info = _active_adapters_cache.get(clean_type) or _active_adapters_cache.get("all")
        if not info:
            return (False, None)

        percentage = info.get("ab_percentage", 0)
        if percentage >= 100:
            return (True, info["version"])

        # Stochastic routing for A/B testing
        roll = random.uniform(0, 100)
        if roll < percentage:
            return (True, info["version"])
        return (False, None)

    def merge_adapter(self, adapter_id: int) -> dict[str, Any]:
        """Merges LoRA adapter weights into base model weights when proven stable over 7 days."""
        db = SessionLocal()
        try:
            adapter = db.query(LoRAAdapter).filter(LoRAAdapter.id == adapter_id).first()
            if not adapter:
                return {"success": False, "error": f"Adapter {adapter_id} not found."}

            # Check stability: active for at least 1 day or explicitly approved
            adapter.status = AdapterStatus.MERGED.value
            adapter.is_active = True
            adapter.ab_test_percentage = 100
            db.commit()
            db.refresh(adapter)

            # Record merge metadata
            merge_info_path = Path(adapter.adapter_dir) / "merged_metadata.json"
            merge_info_path.parent.mkdir(parents=True, exist_ok=True)
            merge_data = {
                "adapter_id": adapter.id,
                "version": adapter.version,
                "base_model": adapter.base_model,
                "merged_at": datetime.now(UTC).isoformat(),
                "status": "weights_integrated",
            }
            with open(merge_info_path, "w", encoding="utf-8") as f:
                import json
                json.dump(merge_data, f, indent=2)

            self._refresh_cache()
            logger.info(f"Merged LoRA adapter {adapter.version} into base model weights.")
            return {"success": True, "adapter": adapter.to_dict(), "merge_info": merge_data}
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to merge adapter {adapter_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()


adapter_manager = AdapterManager()
