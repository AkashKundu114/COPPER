import asyncio
import json
import sys

from app.ai.agents.campaign_agent import campaign_agent
from app.ai.llm.model_manager import model_manager
from app.ai.orchestration.agent_router import route_message, route_message_detailed
from app.core.constants import AgentType
from app.services.chat_service import chat_service


async def run_smoke_test():
    print("================================================================")
    print("      CAMPAIGN INTELLIGENCE AGENT (DELTA) SMOKE TEST")
    print("================================================================\n")

    # 1. Perspective Model & Agent Metadata
    target_model = campaign_agent.get_target_model()
    manifest_info = model_manager.manifest.get("core_agents", {}).get("campaign_intelligence", {})

    print("[Step 1] Verifying Agent & Perspective Model Resolution:")
    print(f"  • Agent Name:        {campaign_agent.name}")
    print(f"  • Agent Type:        {campaign_agent.agent_type.value}")
    print(f"  • Codename:          {manifest_info.get('agent_codename', 'DELTA')}")
    print(f"  • Perspective Model: {target_model}")
    print(f"  • Manifest Model:    {manifest_info.get('name', 'N/A')}")
    print(f"  • Model File:        {manifest_info.get('file', 'N/A')}")
    print(f"  • Quantization:      {manifest_info.get('quantization', 'N/A')}")
    print(f"  • Model Role:        {manifest_info.get('role', 'N/A')}")
    assert target_model == "deepseek-r1:14b", f"Expected deepseek-r1:14b, got {target_model}"
    print("  -> PASSED: Perspective model resolution verified.\n")

    # 2. Router Smoke Test
    test_queries = [
        "How are my campaigns performing?",
        "Which campaign is underperforming?",
        "Optimize my budget",
        "What happened to my CTR?",
        "Alert me about problems",
    ]

    print("[Step 2] Testing Cascade Router Intent Dispatch:")
    for q in test_queries:
        res = await route_message_detailed(q)
        print(f"  • Query: \"{q}\"")
        print(f"    -> Agent: {res.agent.value} | Confidence: {res.confidence*100:.1f}% | Stage: {res.route_stage} | Risk: {res.cascade_risk}")
        assert res.agent == AgentType.CAMPAIGN_INTELLIGENCE
    print("  -> PASSED: All 5 ad-tech queries routed to CAMPAIGN_INTELLIGENCE.\n")

    # 3. Direct Agent Execution
    print("[Step 3] Testing Direct Agent Intelligence Execution:")
    resp_raw = await campaign_agent.run("How are my campaigns performing?")
    resp_json = json.loads(resp_raw)
    print(f"  • Summary: {resp_json.get('summary')}")
    print(f"  • Key Metrics: {resp_json.get('metrics')}")
    print(f"  • Detected Anomalies: {len(resp_json.get('anomalies', []))} active alerts")
    print(f"  • Top Recommendations: {resp_json.get('recommendations')[:2]}")
    assert "summary" in resp_json
    assert "metrics" in resp_json
    assert "anomalies" in resp_json
    assert "recommendations" in resp_json
    assert "charts_data" in resp_json
    print("  -> PASSED: Agent produced structured JSON with full analytics telemetry.\n")

    # 4. Streaming Execution
    print("[Step 4] Testing Agent Streaming Yield:")
    chunks = []
    async for chunk in campaign_agent.stream("Optimize my budget"):
        chunks.append(chunk)
    streamed_text = "".join(chunks)
    streamed_json = json.loads(streamed_text)
    total_budget = streamed_json["metrics"].get("total_daily_budget")
    imp_pct = streamed_json["metrics"].get("improvement_percent")
    print(f"  • Streamed Valid JSON: True ({len(streamed_text)} chars)")
    print(f"  • Portfolio Daily Budget: ${total_budget:,.2f}")
    print(f"  • Optimization Improvement: +{imp_pct:.1f}%")
    print("  -> PASSED: Streaming generator output validated.\n")

    # 5. End-to-End ChatService Smoke Test
    print("[Step 5] Testing End-to-End ChatService Pipeline:")
    chat_result = await chat_service.process_message(session_id="smoke-test-session", message="How are my campaigns performing?")
    agent_val = chat_result.get("agent_type")
    if hasattr(agent_val, "value"):
        agent_val = agent_val.value
    elif str(agent_val).startswith("AgentType."):
        agent_val = str(agent_val).split(".", 1)[1].lower()
    assert agent_val in (AgentType.CAMPAIGN_INTELLIGENCE.value, "campaign_intelligence")

    chat_payload = json.loads(chat_result.get("response", "{}"))
    print(f"  • Run-rate Spend: ${chat_payload['metrics'].get('daily_spend_run_rate'):,.2f}")
    print(f"  • Blended ROAS:   {chat_payload['metrics'].get('overall_roas')}x")
    print(f"  • Blended CTR:    {chat_payload['metrics'].get('average_ctr') * 100:.2f}%")
    print("  -> PASSED: End-to-end ChatService execution successful.\n")

    print("================================================================")
    print("   ALL 5 SMOKE TEST PHASES PASSED WITH ZERO ERRORS!")
    print("================================================================")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
