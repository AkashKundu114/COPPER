"""Tests for Real-Time Human-in-the-Loop Operator Approval Channel."""

import asyncio
import pytest

from app.core.safety.operator_approval_manager import OperatorApprovalManager, TicketStatus
from app.core.control_plane import ArchitecturalControlPlane
from app.core.interfaces.contracts import ExecutionContext, ExecutionOrigin


@pytest.mark.asyncio
async def test_ticket_creation_and_resolution():
    manager = OperatorApprovalManager(default_timeout_sec=5.0)

    broadcasted_events = []
    async def mock_broadcast(event):
        broadcasted_events.append(event)

    manager.register_broadcast_hook(mock_broadcast)

    # 1. Create ticket
    ticket = await manager.create_ticket(
        action="database_drop",
        target="users_table",
        actor="AXIS",
        reason="Requested database schema migration",
        required_controls=["operator_confirmation"],
    )

    assert ticket.ticket_id.startswith("appr_")
    assert ticket.status == TicketStatus.PENDING
    assert len(broadcasted_events) == 1
    assert broadcasted_events[0]["type"] == "operator_approval_request"
    assert broadcasted_events[0]["ticket"]["ticket_id"] == ticket.ticket_id

    # 2. Asynchronously approve ticket
    async def delayed_approve():
        await asyncio.sleep(0.05)
        manager.resolve_ticket(ticket.ticket_id, approved=True, confirmed_by="admin_user")

    asyncio.create_task(delayed_approve())
    decision = await manager.wait_for_decision(ticket.ticket_id)
    assert decision is True

    resolved_ticket = manager.get_ticket(ticket.ticket_id)
    assert resolved_ticket["status"] == TicketStatus.APPROVED.value
    assert resolved_ticket["confirmed_by"] == "admin_user"


@pytest.mark.asyncio
async def test_ticket_rejection():
    manager = OperatorApprovalManager(default_timeout_sec=5.0)

    ticket = await manager.create_ticket(
        action="shell_execute",
        target="reboot",
        actor="FORGE",
        reason="Server reboot requested",
    )

    async def delayed_reject():
        await asyncio.sleep(0.05)
        manager.resolve_ticket(ticket.ticket_id, approved=False, reason="Reboot disallowed during active session")

    asyncio.create_task(delayed_reject())
    decision = await manager.wait_for_decision(ticket.ticket_id)
    assert decision is False

    resolved_ticket = manager.get_ticket(ticket.ticket_id)
    assert resolved_ticket["status"] == TicketStatus.REJECTED.value
    assert "disallowed" in resolved_ticket["decision_reason"]


@pytest.mark.asyncio
async def test_ticket_expiration_timeout():
    # Short timeout of 0.1s
    manager = OperatorApprovalManager(default_timeout_sec=0.1)

    ticket = await manager.create_ticket(
        action="file_delete",
        target="critical_file.log",
        actor="KINESIS",
        reason="Disk cleanup",
        timeout_seconds=0.1,
    )

    decision = await manager.wait_for_decision(ticket.ticket_id)
    assert decision is False
    assert manager.get_ticket(ticket.ticket_id)["status"] == TicketStatus.EXPIRED.value


@pytest.mark.asyncio
async def test_control_plane_lifecycle_approval_unblocking():
    """Verify that ArchitecturalControlPlane awaits approval and unblocks execution when approved."""
    cp = ArchitecturalControlPlane()
    from app.core.safety.operator_approval_manager import operator_approval_manager

    executed = False
    async def consequential_handler(ctx: ExecutionContext):
        nonlocal executed
        executed = True
        return "operation_success"

    ctx = ExecutionContext(
        task_id="tsk_consequential_approval",
        execution_origin=ExecutionOrigin.AGENT,
        agent_id="AXIS",
        metadata={"wait_for_approval": True},
    )

    async def auto_approve():
        # Poll for pending ticket
        for _ in range(50):
            await asyncio.sleep(0.02)
            pending = operator_approval_manager.get_pending_tickets()
            if pending:
                t_id = pending[0]["ticket_id"]
                operator_approval_manager.resolve_ticket(t_id, approved=True, confirmed_by="supervisor")
                break

    asyncio.create_task(auto_approve())

    res = await cp.execute_lifecycle(
        request_payload={"action": "file_delete", "target": "archive_2025.tar.gz"},
        handler=consequential_handler,
        context=ctx,
        actor="AXIS",
        wait_for_approval=True,
    )

    assert res.status == "success"
    assert res.data == "operation_success"
    assert executed is True
