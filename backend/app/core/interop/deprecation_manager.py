"""API Versioning & Deprecation Lifecycle Manager for C.O.P.P.E.R.

Enforces structured deprecation schedules, sunset dates, backward-compatible fallback paths,
and RFC 8594-compliant HTTP deprecation metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logger import logger


@dataclass
class DeprecationNotice:
    component_name: str
    current_version: str
    deprecated_since: str
    sunset_date: str
    migration_target: str
    is_active: bool = True
    call_count: int = 0


class DeprecationManager:
    """Manages API contracts, backwards compatibility, and deprecation governance."""

    def __init__(self):
        self._notices: dict[str, DeprecationNotice] = {}

    def register_deprecation(
        self,
        component_name: str,
        current_version: str,
        sunset_date: str,
        migration_target: str,
        deprecated_since: str | None = None,
    ) -> DeprecationNotice:
        """Registers a formal deprecation schedule for an API contract or component."""
        dep_since = deprecated_since or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        notice = DeprecationNotice(
            component_name=component_name,
            current_version=current_version,
            deprecated_since=dep_since,
            sunset_date=sunset_date,
            migration_target=migration_target,
        )
        self._notices[component_name] = notice
        logger.warning(
            f"[DeprecationManager] Registered deprecation for '{component_name}' v{current_version}. "
            f"Sunset: {sunset_date}. Migrate to: '{migration_target}'"
        )
        return notice

    def record_usage(self, component_name: str) -> dict[str, str]:
        """Records an invocation of a deprecated component and returns RFC 8594 headers."""
        if component_name not in self._notices:
            return {}

        notice = self._notices[component_name]
        notice.call_count += 1
        logger.warning(
            f"[DeprecationWarning] Invoked deprecated component '{component_name}'. "
            f"Migration target: '{notice.migration_target}'. Sunset date: {notice.sunset_date} "
            f"(Total calls: {notice.call_count})"
        )

        return {
            "Deprecation": f"@{notice.deprecated_since}",
            "Sunset": notice.sunset_date,
            "Link": f'<{notice.migration_target}>; rel="successor-version"',
        }

    def is_sunset(self, component_name: str) -> bool:
        """Evaluates whether a deprecated component has passed its sunset date."""
        if component_name not in self._notices:
            return False

        notice = self._notices[component_name]
        try:
            sunset_dt = datetime.strptime(notice.sunset_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) >= sunset_dt
        except ValueError:
            return False

    def list_deprecated_components(self) -> list[dict[str, Any]]:
        return [
            {
                "component": n.component_name,
                "version": n.current_version,
                "deprecated_since": n.deprecated_since,
                "sunset_date": n.sunset_date,
                "migration_target": n.migration_target,
                "invocations": n.call_count,
                "is_sunset": self.is_sunset(n.component_name),
            }
            for n in self._notices.values()
        ]


deprecation_manager = DeprecationManager()
