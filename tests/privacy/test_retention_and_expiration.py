from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
import pytest

from app.core.privacy.governance_manager import DataGovernanceManager


def test_retention_enforcement_purges_expired_data():
    """Verify enforce_retention_policies purges records older than classification TTLs."""
    gov = DataGovernanceManager()
    mock_db = MagicMock()

    # Mock query delete counts
    mock_db.query.return_value.filter.return_value.delete.return_value = 15

    purged = gov.enforce_retention_policies(mock_db)

    assert "expired_memories" in purged
    assert "expired_chat" in purged
    assert "expired_audit" in purged
    assert mock_db.commit.called
