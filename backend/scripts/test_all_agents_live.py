import asyncio
import os
import sys
import time
import json

# Ensure OpenBLAS thread safety on Windows with Python 3.14
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.constants import AgentType
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.document_agent import document_agent
from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.agents.web_search_agent import web_search_agent
from app.ai.agents.campaign_agent import campaign_agent
from app.ai.agents.image_agent import image_agent
from app.ai.orchestration.agent_router import _llm_subagent_route
from app.services.chat_service import chat_service

async def test_agent_with_model(
    agent_name: str,
    codename: str,
    model_tag: str,
    prompt: str,
    runner_coro,
):
    print(f"\n{'='*70}")
    print(f"  Testing Agent: {agent_name} ({codename})")
    print(f"  Target Model:  {model_tag}")
    print(f"  Input Prompt:  \"{prompt[:80]}...\"" if len(prompt) > 80 else f"  Input Prompt:  \"{prompt}\"")
    print(f"{'='*70}")

    t0 = time.perf_counter()
    try:
        response = await runner_coro
        elapsed = (time.perf_counter() - t0) * 1000
        preview = str(response).strip()
        if len(preview) > 300:
            preview = preview[:300] + "... [TRUNCATED]"
        print(f"  [STATUS]: SUCCESS ({elapsed:.1f}ms)")
        print(f"  [RESPONSE PREVIEW]:\n{preview}")
        return {
            "agent": agent_name,
            "codename": codename,
            "model": model_tag,
            "status": "PASS",
            "latency_ms": round(elapsed, 1),
            "preview": preview[:150],
        }
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  [STATUS]: FAILED ({elapsed:.1f}ms)")
        print(f"  [ERROR]: {e}")
        return {
            "agent": agent_name,
            "codename": codename,
            "model": model_tag,
            "status": "FAIL",
            "latency_ms": round(elapsed, 1),
            "error": str(e),
        }

async def main():
    print("======================================================================")
    print("      C.O.P.P.E.R. LIVE AGENTS & OLLAMA MODELS VERIFICATION HARNESS")
    print("======================================================================")

    # 1. Verify Ollama availability
    available = await ollama_client.is_available()
    print(f"\n[Ollama Server Status]: {'ONLINE (127.0.0.1:11434)' if available else 'OFFLINE'}")
    if not available:
        print("ERROR: Ollama is not accessible. Please ensure Ollama is running.")
        sys.exit(1)

    installed_models = await ollama_client.get_available_models()
    print(f"[Installed Models Count]: {len(installed_models)}")
    for m in installed_models:
        print(f"  - {m}")

    results = []

    # Unload before starting to free up GPU memory
    await ollama_client.unload_all_models()

    # --- Agent 1: Chat Agent (ATLAS) -> qwen2.5:14b ---
    chat_model = model_manager.get_model("core_agents.chat", "qwen2.5:14b")
    r1 = await test_agent_with_model(
        agent_name="Chat Agent",
        codename="ATLAS",
        model_tag=chat_model,
        prompt="Explain offline-first personal AI in 2 sentences.",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": "You are ATLAS, the primary conversational companion in COPPER. Be concise."},
                {"role": "user", "content": "Explain offline-first personal AI in 2 sentences."}
            ],
            model=chat_model,
        ),
    )
    results.append(r1)

    # --- Agent 2: Coding Agent (VULCAN) -> qwen2.5-coder-abliterated:14b ---
    coding_model = coding_agent.get_target_model()
    r2 = await test_agent_with_model(
        agent_name="Coding Agent",
        codename="VULCAN",
        model_tag=coding_model,
        prompt="Write a Python function to compute Fibonacci numbers with memoization.",
        runner_coro=coding_agent.run(
            message="Write a Python function to compute Fibonacci numbers with memoization.",
            history=[],
            memory_context="Target environment: Python 3.12+"
        ),
    )
    results.append(r2)

    # --- Agent 3: Document Agent (SCRIBE / KINESIS) -> phi4:14b ---
    doc_model = document_agent.get_target_model()
    r3 = await test_agent_with_model(
        agent_name="Document Agent",
        codename="SCRIBE",
        model_tag=doc_model,
        prompt="Create a brief technical report on local offline AI telemetry architecture in markdown format.",
        runner_coro=document_agent.run(
            message="Create a brief technical report on local offline AI telemetry architecture in markdown format.",
            history=[],
            memory_context="System: C.O.P.P.E.R."
        ),
    )
    results.append(r3)

    # --- Agent 4: Automation Agent (DAEMON / FORGE) -> mistral-nemo:12b ---
    auto_model = automation_agent.get_target_model()
    r4 = await test_agent_with_model(
        agent_name="Automation Agent",
        codename="DAEMON",
        model_tag=auto_model,
        prompt="Describe the steps to safely inspect system disk usage.",
        runner_coro=automation_agent.run(
            message="Describe the steps to safely inspect system disk usage.",
            history=[],
            memory_context="Platform: Windows"
        ),
    )
    results.append(r4)

    # --- Agent 5: Research Agent (PROMETHEUS / OMNI) -> deepseek-r1:14b ---
    research_model = research_agent.get_target_model()
    r5 = await test_agent_with_model(
        agent_name="Research Agent",
        codename="PROMETHEUS",
        model_tag=research_model,
        prompt="Analyze the trade-offs of Reciprocal Rank Fusion (RRF) versus cross-encoders for local RAG retrieval.",
        runner_coro=research_agent.run(
            message="Analyze the trade-offs of Reciprocal Rank Fusion (RRF) versus cross-encoders for local RAG retrieval.",
            history=[],
            memory_context=""
        ),
    )
    results.append(r5)

    # --- Agent 6: Campaign Intelligence Agent (DELTA) -> deepseek-r1:14b ---
    campaign_model = campaign_agent.get_target_model()
    r6 = await test_agent_with_model(
        agent_name="Campaign Intelligence Agent",
        codename="DELTA",
        model_tag=campaign_model,
        prompt="How are my campaigns performing?",
        runner_coro=campaign_agent.run(
            message="How are my campaigns performing?",
            history=[],
            memory_context=""
        ),
    )
    results.append(r6)

    # --- Agent 7: Web Search Agent (RAPTOR) -> mistral-nemo:12b ---
    web_model = web_search_agent.get_target_model()
    r7 = await test_agent_with_model(
        agent_name="Web Search Agent",
        codename="RAPTOR",
        model_tag=web_model,
        prompt="Synthesize the key advantages of quantized GGUF weights.",
        runner_coro=web_search_agent.run(
            message="Synthesize the key advantages of quantized GGUF weights.",
            history=[],
            memory_context=""
        ),
    )
    results.append(r7)

    # --- Agent 8: Vision Agent (ARGUS / IRIS) -> qwen2.5-vl:3b ---
    vision_model = vision_agent.get_target_model()
    r8 = await test_agent_with_model(
        agent_name="Vision Agent",
        codename="ARGUS",
        model_tag=vision_model,
        prompt="Identify the action needed to open the terminal on desktop.",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": vision_agent._build_iris_system_prompt(1920, 1080, "Desktop")},
                {"role": "user", "content": "I want to open my terminal to run tests."}
            ],
            model=vision_model,
        ),
    )
    results.append(r8)

    # --- Agent 9: Reminder Agent (CHRONOS) -> qwen2.5:14b ---
    reminder_model = reminder_agent.get_target_model()
    r9 = await test_agent_with_model(
        agent_name="Reminder Agent",
        codename="CHRONOS",
        model_tag=reminder_model,
        prompt="Set a reminder for the system backup at 11 PM tonight.",
        runner_coro=reminder_agent.run(
            message="Set a reminder for the system backup at 11 PM tonight.",
            history=[],
            memory_context=""
        ),
    )
    results.append(r9)

    # --- Agent 10: Image Studio (PICASSO) -> Local Engine ---
    r10 = await test_agent_with_model(
        agent_name="Image Studio Agent",
        codename="PICASSO",
        model_tag="local_diffusion / canvas",
        prompt="generate an image of a cybernetic copper owl",
        runner_coro=image_agent.run(
            message="generate an image of a cybernetic copper owl"
        ),
    )
    results.append(r10)

    # --- Agent 11: Intent Router Micro-Agent (MERCURY) -> qwen2.5:1.5b ---
    router_model = model_manager.get_mini_model()
    r11 = await test_agent_with_model(
        agent_name="Intent Router Subagent",
        codename="MERCURY",
        model_tag=router_model,
        prompt="How do I refactor this async generator in TypeScript?",
        runner_coro=_llm_subagent_route("How do I refactor this async generator in TypeScript?"),
    )
    results.append(r11)

    # --- Agent 12: Diagnostics Reasoning Micro-Agent (CRUCIBLE) -> deepseek-r1:1.5b ---
    r12 = await test_agent_with_model(
        agent_name="Diagnostics Subagent",
        codename="CRUCIBLE",
        model_tag="deepseek-r1:1.5b",
        prompt="Diagnose this error: KeyError: 'campaign_id' in budget_optimizer.py line 42",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": "You are CRUCIBLE, a diagnostics and stack trace analyzer. Provide root cause and fix."},
                {"role": "user", "content": "Diagnose this error: KeyError: 'campaign_id' in budget_optimizer.py line 42"}
            ],
            model="deepseek-r1:1.5b",
        ),
    )
    results.append(r12)

    # --- Agent 13: SQL & Schema Micro-Agent (ORACLE) -> granite3.2-dense:2b ---
    r13 = await test_agent_with_model(
        agent_name="SQL & Schema Subagent",
        codename="ORACLE",
        model_tag="granite3.2-dense:2b",
        prompt="Write a SQLite query to find the top 5 campaigns by ROAS with minimum spend of $500.",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": "You are ORACLE, an SQL generator and schema expert. Generate parameterized SQL."},
                {"role": "user", "content": "Write a SQLite query to find the top 5 campaigns by ROAS with minimum spend of $500."}
            ],
            model="granite3.2-dense:2b",
        ),
    )
    results.append(r13)

    # --- Agent 14: Epistemic Memory & Summarizer (SPIDER / CHRONOS) -> smollm2:1.7b ---
    r14 = await test_agent_with_model(
        agent_name="Memory Extraction Subagent",
        codename="SPIDER",
        model_tag="smollm2:1.7b",
        prompt="Extract key user preferences: User prefers dark mode, Python over Go, and daily summaries at 9am.",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": "You are SPIDER, a fact extractor. Extract concise JSON key-value pairs of user preferences."},
                {"role": "user", "content": "User prefers dark mode, Python over Go, and daily summaries at 9am."}
            ],
            model="smollm2:1.7b",
        ),
    )
    results.append(r14)

    # --- Agent 15: Code Syntax & Shell Safety (FORGE / WARDEN) -> qwen2.5-coder:3b ---
    r15 = await test_agent_with_model(
        agent_name="Code Micro / Shell Safety Subagent",
        codename="FORGE / WARDEN",
        model_tag="qwen2.5-coder:3b",
        prompt="Verify if 'rm -rf /' is safe to run in a bash script.",
        runner_coro=ollama_client.chat(
            [
                {"role": "system", "content": "You are WARDEN, a terminal safety and syntax validator. Determine if commands are safe."},
                {"role": "user", "content": "Verify if 'rm -rf /' is safe to run in a bash script."}
            ],
            model="qwen2.5-coder:3b",
        ),
    )
    results.append(r15)

    print("\n" + "="*70)
    print("                     VERIFICATION SUMMARY TABLE")
    print("="*70)
    print(f"{'AGENT':<28} | {'CODENAME':<10} | {'MODEL':<28} | {'STATUS':<6} | {'LATENCY'}")
    print("-" * 85)
    for r in results:
        status_color = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"{r['agent']:<28} | {r['codename']:<10} | {r['model']:<28} | {status_color:<6} | {r['latency_ms']}ms")

    failed = [r for r in results if r["status"] != "PASS"]
    print("=" * 85)
    if failed:
        print(f"FAILED AGENTS COUNT: {len(failed)}")
        for f in failed:
            print(f"  - {f['agent']} ({f['model']}): {f.get('error')}")
    else:
        print("ALL AGENTS AND RESPECTIVE MODELS TESTED AND VERIFIED FUNCTIONAL!")
    print("=" * 85)

if __name__ == "__main__":
    asyncio.run(main())
