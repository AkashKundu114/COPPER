# C.O.P.P.E.R. Pre-Trained Model Selection & Agent Mapping Strategy

---

## 1. Architectural Model Strategy Shift

Rather than requiring custom LoRA fine-tuning for all 30 individual agents (which incurs high compute, VRAM management overhead, and training complexity), **C.O.P.P.E.R.** utilizes a **Pre-Trained Model Pool Architecture**.

All 30 specialized agents + COPPER Orchestrator are mapped onto **8 high-capability pre-trained foundational models** (local Ollama engines + zero-trust cloud fallbacks). Specialized agent behaviors, personas, and payload schemas are enforced via dynamic system prompt injection and structured JSON output constraints.

```
+-----------------------------------------------------------------------------------+
|                           AGENT ROUTER & ORCHESTRATOR                             |
+-----------------------------------------------------------------------------------+
                                         |
            +----------------------------+----------------------------+
            | (Local First Inference)                                 | (Cloud Fallback)
            v                                                         v
+----------------------------------------+               +--------------------------+
| 5-6 LOCAL PRE-TRAINED MODELS (OLLAMA)  |               | 2-3 CLOUD MODELS (API)   |
| 1. Llama 3.1 8B (General & Guardian)   |               | 1. GPT-4o-mini           |
| 2. Qwen 2.5 Coder 14B/32B (Coding)     |               | 2. Claude 3.5 Sonnet     |
| 3. Mistral 7B v0.3 (Planning & Memory) |               |                          |
| 4. DeepSeek Coder V2/R1 (Math/Logic)   |               | (Passed via Zero-Trust   |
| 5. Qwen2-VL 7B (Vision & Inspection)   |               |  Data Firewall)          |
| 6. Whisper / Piper (Audio & Speech)    |               |                          |
+----------------------------------------+               +--------------------------+
```

---

## 2. Pre-Trained Model Pool Specification

| Model Pool ID | Pre-Trained Base Model | Deployment Provider | Quantization | Primary Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Model 1: Core Reasoning** | **Llama 3.1 8B Instruct** | Local / Ollama | `Q4_K_M` | General conversation, Guardian Level evaluation, agent routing. |
| **Model 2: Code Synthesis** | **Qwen 2.5 Coder 14B** | Local / Ollama | `Q4_K_M` | Multi-language code synthesis, refactoring, script execution. |
| **Model 3: Planning & Memory**| **Mistral 7B Instruct v0.3**| Local / Ollama | `Q4_K_M` | Epistemic memory extraction, structured JSON schema parsing, schedule planning. |
| **Model 4: Logic & Math** | **DeepSeek Coder V2 / R1** | Local / Ollama | `Q4_K_M` | Complex algorithms, data analysis, deep mathematical logic. |
| **Model 5: Visual Analysis**| **Qwen2-VL 7B / LLaVA 1.6**| Local / Ollama | `Q4_K_M` | Multimodal vision, screenshot analysis, layout inspection. |
| **Model 6: Audio & Speech** | **Whisper (STT) + Piper (TTS)**| Local Native / C++| N/A | Speech-to-text transcription & equalizer timing simulation. |
| **Model 7: Fast Cloud** | **GPT-4o-mini** | Cloud API (OpenAI) | N/A | Fast cloud research fallback (via Data Firewall). |
| **Model 8: Deep Research** | **Claude 3.5 Sonnet** | Cloud API (Anthropic)| N/A | Multi-file codebase refactoring & long-context research fallback. |

---

## 3. Agent-to-Model Mapping Matrix

The 30 domain agents + COPPER Core are mapped onto the 8 pre-trained model pools:

| Model Pool | Primary Model Name | Assigned Agents & Personas |
| :--- | :--- | :--- |
| **1. Core Reasoning** | `llama3.1:8b` | `COPPER` (Orchestrator), `WARDEN` (Security), `AEGIS` (Guardian), `ATLAS` (Task Core), `DIRECTOR` (Workflow). |
| **2. Code Synthesis** | `qwen2.5-coder:14b` | `AXIS` (Primary Code), `CRUCIBLE` (Refactoring), `FORGE` (Build Systems), `GLITCH` (Debugging), `TENSOR` (ML Ops). |
| **3. Planning & Memory** | `mistral:7b-instruct` | `CHRONOS` (Schedule), `MNEMONIC` (Memory), `SYNAPSE` (Learning), `LEDGER` (Finance), `PIVOT` (Routines). |
| **4. Logic & Math** | `deepseek-coder:6.7b` | `QUANTA` (Data Analytics), `CYPHER` (Crypto/Security), `PRISM` (Logic Engine), `GOLIATH` (Big Data). |
| **5. Visual Analysis** | `qwen2-vl:7b` | `IRIS` (Vision Inspection), `SPECTRE` (UI Inspector), `RENDER` (Design Layout). |
| **6. Audio & Speech** | `whisper-base` | `ECHO` (Voice Transcriber), `SIREN` (Audio Alerts), `SONAR` (Speech Audio). |
| **7. Fast Cloud** | `gpt-4o-mini` | `HERMES` (Web Search), `BEACON` (Notifications), `PROXY` (API Middleware), `PORTAL` (Integrations). |
| **8. Deep Research** | `claude-3-5-sonnet` | `VANGUARD` (Architecture Review), `OMNI` (Deep Research), `RAPTOR` (Static Analysis), `VAULT` (Compliance). |

---

## 4. System Prompt Injection & Persona Steering

Since agents share base pre-trained model weights, persona specialization is achieved through **Dynamic System Prompt Injection**:

```python
def build_agent_prompt(agent_id: str, user_prompt: str, epistemic_context: str) -> list[dict]:
    agent_spec = AGENT_REGISTRY.get(agent_id)
    
    system_instruction = f"""You are {agent_spec['name']}, a specialized agent within the C.O.P.P.E.R. system.
    
Role: {agent_spec['description']}
Persona Guidance: {agent_spec['system_prompt']}

Known User Context:
{epistemic_context}

Respond cleanly adhering strictly to your persona while completing the user's task."""

    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
```

---

## 5. Benefits of the Pre-Trained Model Strategy

1. **Zero Fine-Tuning Compute Cost:** Eliminates GPU rental costs and hours of LoRA training runs.
2. **Immediate Out-of-the-Box Deployment:** Users pull 2-3 standard Ollama models (`llama3.1:8b`, `qwen2.5-coder:14b`) and run immediately.
3. **State-of-the-Art Weights:** Leverages continuous improvements from top-tier AI labs (Meta, Alibaba, Anthropic, DeepSeek).
4. **VRAM Optimization:** Sharing base models across agent pools keeps VRAM usage under 16GB-24GB on local hardware.
