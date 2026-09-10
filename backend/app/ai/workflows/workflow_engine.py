import asyncio
import time
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.ai.tools.executor import tool_executor
from app.ai.workflows.dsl import (
    ActionFailurePolicy,
    ExecutionRecord,
    TriggerType,
    Workflow,
    workflow_store,
)
from app.ai.workflows.trigger_parser import parse_interval_seconds
from app.core.logger import logger


class WorkflowEngine:
    def __init__(self, store=workflow_store):
        self.store = store
        self._scheduler: AsyncIOScheduler | None = None
        self._event_listeners: dict[str, list[str]] = {}  # event_name -> list of workflow_ids

    def set_scheduler(self, scheduler: AsyncIOScheduler):
        """Attaches an AsyncIOScheduler instance."""
        self._scheduler = scheduler

    def initialize(self, scheduler: AsyncIOScheduler | None = None):
        """
        Loads all enabled workflows from store and registers them with the scheduler.
        """
        if scheduler:
            self._scheduler = scheduler

        logger.info("Initializing WorkflowEngine and registering active workflows...")
        enabled_workflows = self.store.get_all(enabled_only=True)
        registered_count = 0

        # Re-index event listeners
        self._event_listeners.clear()

        for wf in enabled_workflows:
            try:
                self.register_workflow(wf)
                registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register workflow '{wf.name}' ({wf.id}): {e}")

        logger.info(f"WorkflowEngine initialized: {registered_count} workflows active.")

    def register_workflow(self, workflow: Workflow):
        """
        Registers a single workflow into the scheduler or event listener registry.
        """
        if not workflow.enabled:
            self.unregister_workflow(workflow.id)
            return

        t_type = workflow.trigger.type
        t_type_val = t_type.value if isinstance(t_type, TriggerType) else str(t_type)

        # 1. Event trigger registration
        if t_type_val == TriggerType.EVENT.value:
            event_name = str(workflow.trigger.value)
            if event_name not in self._event_listeners:
                self._event_listeners[event_name] = []
            if workflow.id not in self._event_listeners[event_name]:
                self._event_listeners[event_name].append(workflow.id)
            logger.info(f"Workflow '{workflow.name}' listening for event '{event_name}'")
            return

        # 2. Scheduler-based triggers (cron / interval)
        if not self._scheduler:
            logger.debug(f"Scheduler not yet attached. Deferred registration for '{workflow.name}'.")
            return

        job_id = f"workflow_{workflow.id}"

        if t_type_val == TriggerType.CRON.value:
            cron_expr = str(workflow.trigger.value).strip()
            trigger = CronTrigger.from_crontab(cron_expr)
            self._scheduler.add_job(
                self.execute_workflow,
                trigger=trigger,
                args=[workflow.id],
                id=job_id,
                name=workflow.name,
                replace_existing=True,
            )
            logger.info(f"Registered CRON workflow '{workflow.name}' [{cron_expr}]")

        elif t_type_val == TriggerType.INTERVAL.value:
            ok, secs, err = parse_interval_seconds(workflow.trigger.value)
            if not ok or secs is None:
                logger.error(f"Cannot schedule interval workflow '{workflow.name}': {err}")
                return
            trigger = IntervalTrigger(seconds=secs)
            self._scheduler.add_job(
                self.execute_workflow,
                trigger=trigger,
                args=[workflow.id],
                id=job_id,
                name=workflow.name,
                replace_existing=True,
            )
            logger.info(f"Registered INTERVAL workflow '{workflow.name}' [{secs}s]")

        elif t_type_val == TriggerType.MANUAL.value:
            # Manual triggers are executed on-demand, no scheduler job needed
            pass

    def unregister_workflow(self, workflow_id: str):
        """
        Removes a workflow from the scheduler and event listeners.
        """
        # Remove from scheduler
        if self._scheduler:
            job_id = f"workflow_{workflow_id}"
            try:
                self._scheduler.remove_job(job_id)
                logger.debug(f"Removed job '{job_id}' from scheduler")
            except Exception:
                pass

        # Remove from event listeners
        for ev, wf_list in list(self._event_listeners.items()):
            if workflow_id in wf_list:
                wf_list.remove(workflow_id)

    async def trigger_event(self, event_name: str, event_data: dict[str, Any] | None = None) -> list[ExecutionRecord]:
        """
        Dispatches an event (e.g. 'on_app_launch', 'on_file_change', 'on_idle') to all registered workflows.
        """
        wf_ids = list(self._event_listeners.get(event_name, []))
        records = []
        for wf_id in wf_ids:
            wf = self.store.get(wf_id)
            if not wf or not wf.enabled:
                continue

            # Check event metadata filter if any (e.g., specific app match)
            if event_data and wf.trigger.metadata:
                mismatch = False
                for k, v in wf.trigger.metadata.items():
                    if event_data.get(k) != v:
                        mismatch = True
                        break
                if mismatch:
                    continue

            record = await self.execute_workflow(wf_id, context=event_data)
            records.append(record)
        return records

    async def execute_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        """
        Executes a workflow's actions sequentially through the tool executor with Guardian checks.
        Handles failures (retry/skip/abort), saves execution history, and sends WebSocket notifications.
        """
        wf = self.store.get(workflow_id)
        if not wf:
            err = f"Workflow '{workflow_id}' not found in store."
            logger.warning(err)
            return ExecutionRecord(
                workflow_id=workflow_id,
                workflow_name="Unknown",
                status="failed",
                error=err,
            )

        start_time = time.time()
        exec_context = dict(context or {})
        exec_context.update({"workflow_id": wf.id, "workflow_name": wf.name})

        # 1. Evaluate conditions
        for cond in wf.conditions:
            if not cond.evaluate(exec_context):
                logger.info(f"Condition not met for workflow '{wf.name}': {cond.field} {cond.operator} {cond.value}")
                record = ExecutionRecord(
                    workflow_id=wf.id,
                    workflow_name=wf.name,
                    started_at=start_time,
                    completed_at=time.time(),
                    status="skipped",
                    error="Conditions not met",
                )
                self.store.add_history(record)
                return record

        action_results: list[dict[str, Any]] = []
        overall_status = "success"
        wf_error: str | None = None

        logger.info(f"Executing workflow '{wf.name}' ({len(wf.actions)} actions)...")

        # 2. Execute actions sequentially
        for idx, action in enumerate(wf.actions):
            policy = action.on_failure
            if isinstance(policy, str):
                try:
                    policy = ActionFailurePolicy(policy.lower())
                except ValueError:
                    policy = ActionFailurePolicy.SKIP

            # Interpolate arguments with dynamic context from previous steps
            resolved_args = self._interpolate_args(action.arguments, exec_context)

            step_success = False
            tool_res = None
            retries_remaining = action.max_retries if policy == ActionFailurePolicy.RETRY else 0

            while True:
                tool_res = await tool_executor.execute(
                    tool_name=action.tool,
                    arguments=resolved_args,
                    context=exec_context,
                )
                if tool_res.success:
                    step_success = True
                    break

                if retries_remaining > 0:
                    retries_remaining -= 1
                    logger.warning(
                        f"Action {idx + 1} ({action.tool}) failed: {tool_res.error}. Retrying ({retries_remaining} left)..."
                    )
                    await asyncio.sleep(action.retry_delay_seconds)
                else:
                    break

            action_results.append(
                {
                    "step": idx + 1,
                    "tool": action.tool,
                    "arguments": resolved_args,
                    "success": tool_res.success,
                    "output": tool_res.output,
                    "error": tool_res.error,
                    "execution_time_ms": tool_res.execution_time_ms,
                    "guardian_verdict": tool_res.guardian_verdict,
                }
            )

            # Update execution context with output
            exec_context[f"step_{idx + 1}_output"] = tool_res.output
            exec_context["last_output"] = tool_res.output

            if not step_success:
                wf_error = f"Step {idx + 1} ({action.tool}) failed: {tool_res.error}"

                if policy == ActionFailurePolicy.ABORT:
                    logger.warning(f"Workflow '{wf.name}' aborted at step {idx + 1} due to failure policy ABORT.")
                    overall_status = "aborted"
                    break
                elif policy == ActionFailurePolicy.SKIP:
                    logger.info(f"Workflow '{wf.name}' skipping failed step {idx + 1} and continuing.")

        # 3. Finalize execution record
        if overall_status != "aborted":
            total_actions = len(action_results)
            succeeded_actions = sum(1 for r in action_results if r.get("success"))
            if succeeded_actions == total_actions and total_actions > 0:
                overall_status = "success"
            elif succeeded_actions == 0:
                overall_status = "failed"
            else:
                overall_status = "partial"

        completed_time = time.time()
        record = ExecutionRecord(
            workflow_id=wf.id,
            workflow_name=wf.name,
            started_at=start_time,
            completed_at=completed_time,
            status=overall_status,
            action_results=action_results,
            error=wf_error,
        )

        # Update workflow metadata in store
        wf.last_run = completed_time
        wf.last_status = overall_status
        self.store.update(wf)
        self.store.add_history(record)

        # 4. Dispatch WebSocket notifications
        try:
            await self._dispatch_notification(wf, record)
            record.notification_sent = True
        except Exception as e:
            logger.error(f"Failed to dispatch workflow notification: {e}")

        logger.info(f"Completed workflow '{wf.name}' with status '{overall_status}' in {round(completed_time - start_time, 2)}s.")
        return record

    def _interpolate_args(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Interpolates {key} placeholders in action arguments from context."""
        interpolated = {}
        for k, v in args.items():
            if isinstance(v, str) and "{" in v and "}" in v:
                try:
                    interpolated[k] = v.format(**context)
                except Exception:
                    interpolated[k] = v
            elif isinstance(v, dict):
                interpolated[k] = self._interpolate_args(v, context)
            else:
                interpolated[k] = v
        return interpolated

    async def _dispatch_notification(self, workflow: Workflow, record: ExecutionRecord):
        """Sends rich notification over WebSocket connection."""
        if workflow.notification.type == "silent":
            return

        from app.api.websocket.manager import manager

        # Build human-readable output summary
        output_snippets = []
        for res in record.action_results:
            if res.get("success"):
                out = res.get("output")
                if isinstance(out, dict):
                    # Summarize dict
                    out_str = out.get("summary") or out.get("result") or str(out)[:200]
                else:
                    out_str = str(out)[:200]
                output_snippets.append(f"[{res.get('tool')}]: {out_str}")
            else:
                output_snippets.append(f"[{res.get('tool')} FAILED]: {res.get('error')}")

        result_summary = "\n".join(output_snippets) if output_snippets else "No output"

        # Format message template
        template = workflow.notification.template or "Workflow '{name}' executed with status: {status}"
        try:
            rendered_msg = template.format(
                name=workflow.name,
                status=record.status,
                result=result_summary,
                error=record.error or "",
            )
        except Exception:
            rendered_msg = f"Workflow '{workflow.name}' finished with status: {record.status}\n{result_summary}"

        # Send proactive toast alert
        await manager.push_proactive(
            {
                "alert_id": f"wf_{workflow.id}_{int(time.time())}",
                "severity": "info" if record.status == "success" else "warning",
                "category": "workflow",
                "title": f"Workflow: {workflow.name}",
                "message": rendered_msg,
                "mode": "normal",
                "suggested_actions": ["View History", "Dismiss"],
            }
        )

        # Broadcast structured event
        await manager.broadcast(
            {
                "type": "workflow_executed",
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "status": record.status,
                "execution_id": record.id,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "results": record.action_results,
            }
        )


workflow_engine = WorkflowEngine()
