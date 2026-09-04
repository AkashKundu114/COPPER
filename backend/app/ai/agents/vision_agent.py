import asyncio
import json
import re
from collections.abc import AsyncGenerator
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.tools.builtin import screen_tools
from app.api.websocket.manager import manager as ws_manager
from app.core.constants import AgentType, LLMProvider
from app.core.guardian import DisagreementLevel, guardian_engine
from app.core.logger import logger

IRIS_SYSTEM_PROMPT = """You are IRIS, COPPER's Computer Use Agent. You can SEE and INTERACT with the user's desktop.

You operate in a closed-loop cycle:

OBSERVE — You receive a screenshot of the current screen.
THINK — Analyze what you see, identify UI elements.
ACT — Execute ONE action to progress toward the goal.
VERIFY — Receive the next screenshot to confirm your action worked.

AVAILABLE ACTIONS (emit ONE inside <action></action> tags):
<action>{{"type": "click", "x": 500, "y": 300, "button": "left"}}</action>
<action>{{"type": "double_click", "x": 500, "y": 300}}</action>
<action>{{"type": "type_text", "text": "Hello world"}}</action>
<action>{{"type": "hotkey", "keys": ["ctrl", "s"]}}</action>
<action>{{"type": "scroll", "x": 500, "y": 300, "direction": "down", "amount": 3}}</action>
<action>{{"type": "wait", "seconds": 2}}</action>
<action>{{"type": "done", "summary": "Task completed. Here's what I did: ..."}}</action>

RULES:

1. ALWAYS describe what you see BEFORE choosing an action.
2. Use PRECISE pixel coordinates matching the current screenshot ({screen_width}x{screen_height}).
3. ONE action per turn inside <action>...</action> tags.
4. Maximum {max_steps} actions per task.
5. NEVER interact with banking, medical, or password manager applications.
6. If typing passwords, STOP and ask the user to type manually.
7. If the task is finished, emit <action>{{"type": "done", "summary": "..."}}</action>.

SCREEN DIMENSIONS: {screen_width}x{screen_height}
CURRENT ACTIVE WINDOW: {active_window}
"""


class VisionAgent(BaseAgent):
    """
    IRIS: Autonomous Computer Use Agent with closed-loop perception,
    spatial action grounding, and Guardian safety boundaries.
    """

    def __init__(self, max_steps: int = 15):
        super().__init__(
            agent_type=AgentType.VISION,
            name="IRIS (Computer Use Agent)",
            description="Perceives the desktop screen, grounds UI elements, plans and executes mouse & keyboard actions.",
            tools=[
                "screenshot",
                "click",
                "double_click",
                "type_text",
                "hotkey",
                "scroll",
                "wait",
            ],
            max_tool_steps=max_steps,
        )
        self.max_steps = max_steps

    def get_target_model(self) -> str:
        """Primary model for visual reasoning and action planning (Qwen2-VL-7B)."""
        return model_manager.get_model("vision_agents.vision_primary", "qwen2.5-vl-abliterated:7b")

    def get_grounding_model(self) -> str:
        """Fast model for rapid UI element detection and OCR (Qwen2-VL-2B)."""
        return model_manager.get_model("vision_agents.vision_lightweight", "qwen2-vl:2b")

    def _build_iris_system_prompt(self, screen_w: int, screen_h: int, active_window: str) -> str:
        return IRIS_SYSTEM_PROMPT.format(
            screen_width=screen_w,
            screen_height=screen_h,
            active_window=active_window or "Desktop / Background",
            max_steps=self.max_steps,
        )

    def parse_action(self, response_text: str) -> tuple[str, dict[str, Any] | None]:
        """
        Extract the thinking/observation portion and the action JSON from model output.
        Looks for <action>{...}</action> or standard JSON blocks.
        """
        thought = response_text.strip()
        action_data = None

        # 1. Primary: Extract from <action>...</action> tags
        match = re.search(r"<action>(.*?)</action>", response_text, re.DOTALL | re.IGNORECASE)
        if match:
            action_str = match.group(1).strip()
            # Everything before or around <action> is considered thought
            thought = re.sub(r"<action>.*?</action>", "", response_text, flags=re.DOTALL | re.IGNORECASE).strip()
            try:
                action_data = json.loads(action_str)
                return thought, action_data
            except Exception as e:
                logger.warning(f"Failed to parse JSON in <action> tags: {action_str} - {e}")

        # 2. Fallback: Check for markdown JSON code block
        code_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if code_match:
            try:
                action_data = json.loads(code_match.group(1))
                if isinstance(action_data, dict) and "type" in action_data:
                    thought = response_text[: code_match.start()].strip()
                    return thought, action_data
            except Exception:
                pass

        # 3. Fallback: Scan for bare JSON object containing "type"
        raw_json_match = re.search(r'\{\s*"type"\s*:\s*"[^"]+"\s*.*?\}', response_text, re.DOTALL)
        if raw_json_match:
            try:
                candidate = json.loads(raw_json_match.group(0))
                if isinstance(candidate, dict) and "type" in candidate:
                    thought = response_text[: raw_json_match.start()].strip()
                    return thought, candidate
            except Exception:
                pass

        return thought, None

    async def _emit_step_event(
        self,
        session_id: str | None,
        step: int,
        action: str,
        action_details: dict[str, Any],
        thought: str,
        screenshot_b64: str,
        status: str = "running",
        summary: str = "",
        window_title: str = "",
        coordinates: dict[str, int] | None = None,
    ):
        """Broadcast live step-by-step updates to the frontend via WebSocket."""
        event_payload = {
            "type": "computer_use_step",
            "step": step,
            "max_steps": self.max_steps,
            "action": action,
            "action_details": action_details,
            "thought": thought,
            "screenshot_b64": screenshot_b64,
            "status": status,
            "summary": summary,
            "window_title": window_title,
            "coordinates": coordinates,
        }

        try:
            if session_id:
                await ws_manager.send(session_id, event_payload)
            # Also broadcast so active monitors/inspectors stay synced
            await ws_manager.broadcast(event_payload)
        except Exception as e:
            logger.debug(f"Could not send computer_use_step WS event: {e}")

    async def ground_ui_element(
        self, element_query: str, screenshot_b64: str, screen_w: int, screen_h: int
    ) -> dict[str, Any] | None:
        """
        Use fast Qwen2-VL-2B model for rapid UI element detection, bounding boxes, and label localization.
        """
        grounding_model = self.get_grounding_model()
        prompt = (
            f"Locate the UI element, button, text, or icon matching: '{element_query}'.\n"
            f"Screen dimensions: {screen_w}x{screen_h}.\n"
            "Return JSON only with exact pixel coordinates:\n"
            '{"found": true, "x": center_x, "y": center_y, "box": [ymin, xmin, ymax, xmax], "label": "description"}\n'
            'If not found, return: {"found": false}'
        )

        messages = [
            {
                "role": "user",
                "content": prompt,
                "images": [screenshot_b64],
            }
        ]

        try:
            res = await ollama_client.chat(messages, model=grounding_model, agent_type=self.agent_type)
            match = re.search(r"\{.*?\}", res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if data.get("found"):
                    return data
        except Exception as e:
            logger.debug(f"Fast visual grounding with {grounding_model} failed: {e}")
        return None

    async def _execute_action(
        self,
        action_data: dict[str, Any],
        scale_factor: float,
        screenshot_b64: str = "",
        screen_w: int = 1920,
        screen_h: int = 1080,
    ) -> dict[str, Any]:
        """Map and execute action coordinates to the physical screen."""
        action_type = action_data.get("type", "").lower().strip()

        # Coordinate rescaling if screenshot was downsampled
        raw_x = action_data.get("x")
        raw_y = action_data.get("y")

        # Fast UI Grounding with Qwen2-VL-2B if target query is specified without exact coordinates
        if action_type in ["click", "double_click", "ground"] and (raw_x is None or raw_y is None):
            target = action_data.get("target") or action_data.get("element") or action_data.get("text")
            if target and screenshot_b64:
                grounded = await self.ground_ui_element(target, screenshot_b64, screen_w, screen_h)
                if grounded and "x" in grounded and "y" in grounded:
                    raw_x = grounded["x"]
                    raw_y = grounded["y"]
                    action_data["x"] = raw_x
                    action_data["y"] = raw_y
                    logger.info(f"Grounded target '{target}' to ({raw_x}, {raw_y}) via 2B model")

        target_x = int(round(raw_x / scale_factor)) if raw_x is not None and scale_factor > 0 else raw_x
        target_y = int(round(raw_y / scale_factor)) if raw_y is not None and scale_factor > 0 else raw_y

        if action_type == "click":
            button = action_data.get("button", "left")
            return await screen_tools.click(target_x, target_y, button=button)

        elif action_type == "double_click":
            return await screen_tools.double_click(target_x, target_y)

        elif action_type == "type_text":
            text = action_data.get("text", "")
            interval = action_data.get("interval", 0.02)
            return await screen_tools.type_text(text, interval=interval)

        elif action_type == "hotkey":
            keys = action_data.get("keys", [])
            return await screen_tools.hotkey(keys)

        elif action_type == "scroll":
            direction = action_data.get("direction", "down")
            amount = action_data.get("amount", 3)
            return await screen_tools.scroll(
                target_x if target_x is not None else 500,
                target_y if target_y is not None else 500,
                direction=direction,
                amount=amount,
            )

        elif action_type == "wait":
            seconds = action_data.get("seconds", 1.0)
            return await screen_tools.wait(seconds=seconds)

        elif action_type == "ground":
            return {"status": "success", "action": "ground", "x": target_x, "y": target_y}

        elif action_type == "done":
            return {"status": "success", "action": "done", "summary": action_data.get("summary", "")}

        else:
            return {"status": "error", "error": f"Unknown action type '{action_type}'"}

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        """
        Execute closed-loop ReAct cycle for Computer Use.
        Returns final completion report or error message.
        """
        session_id = kwargs.get("session_id")
        screen_w, screen_h = screen_tools.get_screen_size()
        target_model = self.get_target_model()

        action_history: list[dict[str, Any]] = []
        final_summary = ""

        logger.info(f"IRIS Computer Use Agent starting task: '{message}' on {screen_w}x{screen_h} display.")

        for step in range(1, self.max_steps + 1):
            # 1. OBSERVE — Capture current desktop screen
            shot = await screen_tools.screenshot()
            if shot.get("status") == "error":
                err_msg = f"[IRIS Error]: Failed to capture screen: {shot.get('error')}"
                logger.error(err_msg)
                return err_msg

            img_b64 = shot["image_b64"]
            scale_factor = shot.get("scale_factor", 1.0)
            active_window = screen_tools.get_active_window_title()

            # 2. GUARDIAN PRE-CHECK — Active window safety
            win_verdict = guardian_engine.check_window_safety(active_window)
            if win_verdict.level >= DisagreementLevel.CHALLENGE:
                blocked_msg = (
                    f"🛡️ [Guardian Intervention]: Safety boundary triggered for window '{active_window}'.\n"
                    f"{win_verdict.reasoning}\n{win_verdict.recommendation}"
                )
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action="blocked",
                    action_details={"window": active_window},
                    thought=f"Guardian blocked interaction with window: {active_window}",
                    screenshot_b64=img_b64,
                    status="blocked",
                    summary=blocked_msg,
                    window_title=active_window,
                )
                return blocked_msg

            # 3. THINK & PLAN — Query Multimodal LLM
            system_prompt = self._build_iris_system_prompt(screen_w, screen_h, active_window)

            history_summary = (
                "\n".join(
                    [
                        f"Step {h['step']}: {h['thought'][:100]}... -> Action: {json.dumps(h['action'])} ({h['status']})"
                        for h in action_history[-4:]
                    ]
                )
                if action_history
                else "None (Initial step)."
            )

            user_step_prompt = (
                f"GOAL: {message}\n\n"
                f"STEP {step}/{self.max_steps}\n"
                f"Active Window: '{active_window}'\n"
                f"Previous Action History:\n{history_summary}\n\n"
                "Examine the current screenshot. Describe what you observe, then output your next single action in <action>...</action> tags."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_step_prompt,
                    "images": [img_b64],
                },
            ]

            try:
                llm_response = await ollama_client.chat(
                    messages,
                    model=target_model,
                    agent_type=self.agent_type,
                )
            except Exception as e:
                err_msg = f"[IRIS Error]: LLM invocation failed at step {step}: {e}"
                logger.error(err_msg)
                return err_msg

            # 4. PARSE ACTION
            thought, action_data = self.parse_action(llm_response)

            if not action_data:
                # No action tag found; if response seems to conclude or is stuck
                logger.warning(f"IRIS step {step}: Model emitted no valid <action> tag. Raw: {llm_response[:120]}")
                action_data = {"type": "wait", "seconds": 1.0}

            action_type = action_data.get("type", "").lower().strip()
            coordinates = None
            if "x" in action_data and "y" in action_data:
                coordinates = {"x": action_data["x"], "y": action_data["y"]}

            # 5. GUARDIAN ACTION VALIDATION
            action_verdict = guardian_engine.evaluate_screen_action(
                action_type=action_type,
                action_data=action_data,
                window_title=active_window,
            )
            if action_verdict.level >= DisagreementLevel.CHALLENGE:
                challenge_msg = (
                    f"🛡️ [Guardian Intervention]: Blocked unsafe action '{action_type}'.\n"
                    f"{action_verdict.reasoning}\n{action_verdict.recommendation}"
                )
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action=action_type,
                    action_details=action_data,
                    thought=thought,
                    screenshot_b64=img_b64,
                    status="blocked",
                    summary=challenge_msg,
                    window_title=active_window,
                    coordinates=coordinates,
                )
                return challenge_msg

            # 6. CHECK FOR TASK COMPLETION
            if action_type == "done":
                final_summary = action_data.get("summary", thought) or "Task completed successfully."
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action="done",
                    action_details=action_data,
                    thought=thought,
                    screenshot_b64=img_b64,
                    status="completed",
                    summary=final_summary,
                    window_title=active_window,
                )
                action_history.append(
                    {
                        "step": step,
                        "thought": thought,
                        "action": action_data,
                        "status": "completed",
                    }
                )
                logger.info(f"IRIS completed task in {step} steps: {final_summary}")
                return f"✅ **Task Completed**\n\n{final_summary}"

            # 7. EXECUTE ACTION
            logger.info(f"IRIS step {step}/{self.max_steps} executing action '{action_type}': {action_data}")
            exec_result = await self._execute_action(
                action_data, scale_factor, screenshot_b64=img_b64, screen_w=screen_w, screen_h=screen_h
            )
            exec_status = exec_result.get("status", "success")

            # 8. STREAM WEBSOCKET STEP UPDATE
            await self._emit_step_event(
                session_id=session_id,
                step=step,
                action=action_type,
                action_details=action_data,
                thought=thought,
                screenshot_b64=img_b64,
                status=exec_status,
                summary=f"Executed {action_type}",
                window_title=active_window,
                coordinates=coordinates,
            )

            action_history.append(
                {
                    "step": step,
                    "thought": thought,
                    "action": action_data,
                    "status": exec_status,
                }
            )

            # Small cooldown before next observation
            await asyncio.sleep(0.3)

        fallback_done = (
            f"⚠️ Reached maximum step limit ({self.max_steps}) for this task.\n\n"
            f"**Last Observation:**\n{action_history[-1]['thought'] if action_history else 'No steps recorded.'}"
        )
        return fallback_done

    async def stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream live progress updates of the Computer Use loop.
        """
        session_id = kwargs.get("session_id")
        screen_w, screen_h = screen_tools.get_screen_size()
        target_model = self.get_target_model()

        yield "👁️ **IRIS (Computer Use Agent) Activated**\n"
        yield f"- **Display Resolution:** `{screen_w}x{screen_h}`\n"
        yield f"- **Vision Model:** `{target_model}`\n"
        yield f"- **Goal:** {message}\n\n"

        action_history: list[dict[str, Any]] = []

        for step in range(1, self.max_steps + 1):
            yield f"---\n\n### 📸 Step {step}/{self.max_steps}: Perceiving Desktop\n"

            # 1. OBSERVE
            shot = await screen_tools.screenshot()
            if shot.get("status") == "error":
                yield f"❌ **Error capturing screen:** {shot.get('error')}\n"
                return

            img_b64 = shot["image_b64"]
            scale_factor = shot.get("scale_factor", 1.0)
            active_window = screen_tools.get_active_window_title()

            yield f"- **Active Window:** `{active_window or 'Desktop'}`\n"

            # 2. GUARDIAN CHECK
            win_verdict = guardian_engine.check_window_safety(active_window)
            if win_verdict.level >= DisagreementLevel.CHALLENGE:
                challenge_msg = (
                    f"🛡️ **Guardian Safety Boundary Triggered!**\n"
                    f"Interaction blocked on window: `{active_window}`\n\n"
                    f"{win_verdict.reasoning}\n\n"
                    f"👉 *{win_verdict.recommendation}*\n"
                )
                yield challenge_msg
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action="blocked",
                    action_details={"window": active_window},
                    thought=f"Guardian blocked interaction with window: {active_window}",
                    screenshot_b64=img_b64,
                    status="blocked",
                    summary=challenge_msg,
                    window_title=active_window,
                )
                return

            # 3. THINK & PLAN
            system_prompt = self._build_iris_system_prompt(screen_w, screen_h, active_window)
            history_summary = (
                "\n".join(
                    [
                        f"Step {h['step']}: {h['thought'][:100]}... -> Action: {json.dumps(h['action'])} ({h['status']})"
                        for h in action_history[-4:]
                    ]
                )
                if action_history
                else "None (Initial step)."
            )

            user_step_prompt = (
                f"GOAL: {message}\n\n"
                f"STEP {step}/{self.max_steps}\n"
                f"Active Window: '{active_window}'\n"
                f"Previous Action History:\n{history_summary}\n\n"
                "Examine the current screenshot. Describe what you observe, then output your next single action in <action>...</action> tags."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_step_prompt,
                    "images": [img_b64],
                },
            ]

            yield f"- **Reasoning:** Analyzing screen with {target_model}...\n"
            try:
                llm_response = await ollama_client.chat(
                    messages,
                    model=target_model,
                    agent_type=self.agent_type,
                )
            except Exception as e:
                yield f"❌ **LLM Error at step {step}:** {e}\n"
                return

            thought, action_data = self.parse_action(llm_response)
            if thought:
                yield f"> {thought}\n\n"

            if not action_data:
                action_data = {"type": "wait", "seconds": 1.0}

            action_type = action_data.get("type", "").lower().strip()
            coordinates = None
            if "x" in action_data and "y" in action_data:
                coordinates = {"x": action_data["x"], "y": action_data["y"]}

            # 4. GUARDIAN ACTION VALIDATION
            action_verdict = guardian_engine.evaluate_screen_action(
                action_type=action_type,
                action_data=action_data,
                window_title=active_window,
            )
            if action_verdict.level >= DisagreementLevel.CHALLENGE:
                action_block_msg = (
                    f"🛡️ **Guardian Blocked Action `{action_type}`**\n"
                    f"{action_verdict.reasoning}\n\n"
                    f"👉 *{action_verdict.recommendation}*\n"
                )
                yield action_block_msg
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action=action_type,
                    action_details=action_data,
                    thought=thought,
                    screenshot_b64=img_b64,
                    status="blocked",
                    summary=action_block_msg,
                    window_title=active_window,
                    coordinates=coordinates,
                )
                return

            # 5. COMPLETION CHECK
            if action_type == "done":
                final_summary = action_data.get("summary", thought) or "Task completed successfully."
                yield f"🎉 **Task Finished:**\n\n{final_summary}\n"
                await self._emit_step_event(
                    session_id=session_id,
                    step=step,
                    action="done",
                    action_details=action_data,
                    thought=thought,
                    screenshot_b64=img_b64,
                    status="completed",
                    summary=final_summary,
                    window_title=active_window,
                )
                return

            # 6. EXECUTE ACTION
            yield f"⚡ **Executing Action:** `{action_type}` `{json.dumps(action_data)}`\n\n"
            exec_result = await self._execute_action(
                action_data, scale_factor, screenshot_b64=img_b64, screen_w=screen_w, screen_h=screen_h
            )
            exec_status = exec_result.get("status", "success")

            # 7. EMIT STEP EVENT
            await self._emit_step_event(
                session_id=session_id,
                step=step,
                action=action_type,
                action_details=action_data,
                thought=thought,
                screenshot_b64=img_b64,
                status=exec_status,
                summary=f"Executed {action_type}",
                window_title=active_window,
                coordinates=coordinates,
            )

            action_history.append(
                {
                    "step": step,
                    "thought": thought,
                    "action": action_data,
                    "status": exec_status,
                }
            )

            await asyncio.sleep(0.3)

        yield f"⚠️ **Step limit reached ({self.max_steps}). IRIS concluded task.**\n"


vision_agent = VisionAgent()
