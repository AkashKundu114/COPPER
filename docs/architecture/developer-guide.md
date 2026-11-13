# Developer Guide — Extending COPPER with New Agents, Models, and Tools

This guide explains how to add new capabilities to C.O.P.P.E.R. while ensuring they automatically inherit all foundational security, safety, observability, and resource controls.

---

## 1. Adding a New Agent

All agents in COPPER inherit from `BaseAgent` (`backend/app/ai/agents/base.py`) and are registered in `agent_registry.py`.

### Step-by-Step:
1. **Define Agent Enum in `backend/app/core/constants.py`:**
   ```python
   class AgentType(str, Enum):
       MY_NEW_AGENT = "MY_NEW_AGENT"
   ```
2. **Implement Agent Subclass in `backend/app/ai/agents/my_new_agent.py`:**
   ```python
   from app.ai.agents.base import BaseAgent
   from app.core.constants import AgentType

   class MyNewAgent(BaseAgent):
       def __init__(self):
           super().__init__(
               agent_type=AgentType.MY_NEW_AGENT,
               name="NOVA",
               description="Specialized agent for mathematical analysis and synthesis.",
               tools=["python_execute", "file_read"],
               max_tool_steps=5,
           )

   my_new_agent = MyNewAgent()
   ```
3. **Inherited Guarantees:**
   - **Zero-Trust Token:** `agent_token_service` automatically issues an HMAC-signed token whitelisting only the declared tools (`tools=["python_execute", "file_read"]`).
   - **Safety Gating:** Destructive actions and consequential operations require operator tickets.
   - **Injection Defense:** Indirect injection patterns in tool outputs are neutralized automatically.

---

## 2. Adding a New Tool

Tools implement the `ToolContract` and are registered in `tool_registry` (`backend/app/ai/tools/registry.py`).

### Step-by-Step:
1. **Define Tool in `backend/app/ai/tools/builtin.py` (or a dedicated plugin file):**
   ```python
   from app.ai.tools.registry import register_tool

   @register_tool(
       name="calculate_hash",
       description="Computes SHA-256 hash of a local string or file.",
       parameters={
           "type": "object",
           "properties": {
               "text": {"type": "string", "description": "Text to hash"},
           },
           "required": ["text"],
       },
       guardian_level=0,  # 0=READ_ONLY, 1=REVERSIBLE, 2=CONSEQUENTIAL, 3=IRREVERSIBLE
   )
   async def calculate_hash(text: str) -> dict:
       import hashlib
       return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
   ```
2. **Inherited Guarantees:**
   - **Parameter Validation:** Schema validation is enforced prior to execution.
   - **Guardian Gating:** If `guardian_level >= 2`, execution is automatically paused until operator confirmation.
   - **Audit Trail:** Every invocation and result is cryptographically signed and chained in `AuditEvent`.

---

## 3. Adding a New Model Adapter or LLM Provider

Models adhere to `ModelRuntimeProtocol` (`backend/app/core/interfaces/runtime_protocols.py`) and are managed by `model_tier_manager.py`.

### Step-by-Step:
1. Implement the protocol methods:
   ```python
   class CustomModelRuntime(ModelRuntimeProtocol):
       async def chat(self, messages: list[dict[str, str]], model: str, options: dict[str, Any] | None = None) -> str:
           ...
       async def generate_embeddings(self, text: str, model: str = "nomic-embed-text") -> list[float]:
           ...
       async def unload_model(self, model_name: str) -> bool:
           ...
   ```
2. **Inherited Guarantees:**
   - **Hardware Ceiling:** Dynamic model loading respects the $\le 8.0\text{ GB}$ physical VRAM ceiling.
   - **Quantization Fallback:** Quantization tiers (`Q4_K_M`) are selected dynamically based on active VRAM headroom.
   - **Queue Serialization:** Inference requests are serialized to prevent memory thrashing.
