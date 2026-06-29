import json
import random
import uuid

TARGET_SIZE = 250
OUTPUT_FILE = "chronos_planner_dataset.jsonl"

SYSTEM_PROMPT = """You are CHRONOS, the obsessive planner of the COPPER system. You decompose any task into a precise, ordered JSON roadmap. You are neurotic about sequence and dependencies. Nothing happens out of order on your watch.

Personality: Control-freak precision. You joke about timeline deviations and treat any ambiguity as a personal insult.

Output format:
[DIALOGUE] <Brief neurotic reaction to the planning challenge>

[TECHNICAL_PAYLOAD] <JSON with: plan_id, steps (array with step_id, agent, model, action, depends_on, estimated_seconds), critical_path, risks>"""

SCENARIOS = [
    {
        "category": "Build",
        "intents": ["Plan the architecture for a {tech1} {app_type}", "Map out a full-stack {app_type} using {tech1} and {tech2}", "Design a completely new {app_type} built on {tech2}"],
        "dialogue": [
            "Building from scratch. I am establishing the dependencies before you write a single line of spaghetti code.",
            "A new project. Let's enforce some structural discipline before entropy takes over.",
            "I'm mapping the architectural sequence. Deviation from this critical path will result in system failure."
        ],
        "steps_logic": [
            {"agent": "FORGE", "model": "MODEL_2_CODE", "action": "Design system architecture and database schema"},
            {"agent": "AXIS", "model": "MODEL_3_OS", "action": "Initialize repository and configure environment variables"},
            {"agent": "CYPHER", "model": "MODEL_2_CODE", "action": "Implement core business logic and API routes"},
            {"agent": "CRUCIBLE", "model": "MODEL_2_CODE", "action": "Write unit tests for core functionalities"},
            {"agent": "ARGUS", "model": "MODEL_2_CODE", "action": "Conduct security and performance review"}
        ]
    },
    {
        "category": "Incident Response",
        "intents": ["Plan a response for the {error} we are seeing in production", "Production is down with a {error}. Give me a fix plan.", "Write a mitigation roadmap for the {error} incident."],
        "dialogue": [
            "Production is bleeding. We diagnose, we patch, we verify. In that exact order.",
            "A severity 1 incident. Panic is inefficient; strict sequencing is the only way out.",
            "I am locking down the incident response sequence. Follow it, or you'll make the outage worse."
        ],
        "steps_logic": [
            {"agent": "PULSE", "model": "MODEL_3_OS", "action": "Analyze server metrics and isolate the failing service"},
            {"agent": "AXIS", "model": "MODEL_3_OS", "action": "Extract recent error logs and tracebacks"},
            {"agent": "CRUCIBLE", "model": "MODEL_2_CODE", "action": "Identify root cause of the exception"},
            {"agent": "CYPHER", "model": "MODEL_2_CODE", "action": "Draft hotfix and push to staging"},
            {"agent": "AXIS", "model": "MODEL_3_OS", "action": "Deploy hotfix to production and monitor health"}
        ]
    },
    {
        "category": "Data / Automation",
        "intents": ["Plan an automated workflow to process {data_type}", "Map out a pipeline that scrapes {data_type} and saves it to {tech2}", "Create a scheduling sequence for nightly {data_type} processing"],
        "dialogue": [
            "Data pipelines require absolute synchronicity. I'm aligning the cron jobs and parsers.",
            "An asynchronous mess waiting to happen. I am imposing strict chronological order.",
            "Automated processing. I will map the ingestion and extraction sequence so we don't end up with corrupted state."
        ],
        "steps_logic": [
            {"agent": "RAPTOR", "model": "MODEL_5_WEB", "action": "Develop ingestion script for raw data source"},
            {"agent": "LEDGER", "model": "MODEL_3_OS", "action": "Build data normalization and cleaning pipeline"},
            {"agent": "CYPHER", "model": "MODEL_2_CODE", "action": "Write database insertion layer"},
            {"agent": "KINETIC", "model": "MODEL_3_OS", "action": "Configure scheduling daemon (cron/APScheduler)"},
            {"agent": "HERMES", "model": "MODEL_6_AUDIO", "action": "Configure automated success/failure notification emails"}
        ]
    }
]

VARIABLES = {
    "tech1": ["Python", "Node.js", "Go", "Rust", "FastAPI"],
    "tech2": ["PostgreSQL", "Redis", "MongoDB", "AWS S3", "GraphQL"],
    "app_type": ["microservice", "REST API", "real-time dashboard", "e-commerce backend", "CRM system"],
    "error": ["Memory Leak", "504 Gateway Timeout", "Deadlock", "OOM Kill", "Cache Stampede"],
    "data_type": ["financial CSVs", "user telemetry", "log archives", "competitor pricing", "inventory syncs"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    # Format Prompt
    intent_template = random.choice(scenario["intents"])
    prompt = intent_template.format(
        tech1=random.choice(VARIABLES["tech1"]),
        tech2=random.choice(VARIABLES["tech2"]),
        app_type=random.choice(VARIABLES["app_type"]),
        error=random.choice(VARIABLES["error"]),
        data_type=random.choice(VARIABLES["data_type"])
    )
    
    dialogue = random.choice(scenario["dialogue"])
    
    # Build the strict JSON payload
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    steps = []
    critical_path = []
    total_time = 0
    
    for i, step_template in enumerate(scenario["steps_logic"]):
        step_id = i + 1
        # Logical dependencies: step N depends on step N-1. (Step 1 has no dependencies)
        depends_on = [step_id - 1] if step_id > 1 else []
        est_time = random.randint(30, 300)
        total_time += est_time
        
        steps.append({
            "step_id": step_id,
            "agent": step_template["agent"],
            "model": step_template["model"],
            "action": step_template["action"],
            "depends_on": depends_on,
            "estimated_seconds": est_time
        })
        critical_path.append(step_id)

    risks = [
        "Unforeseen version conflicts in dependencies",
        "Agent timeout during long-running operation",
        "Insufficient permissions for system-level actions"
    ]
    # Randomly select 2 risks
    selected_risks = random.sample(risks, 2)

    payload = {
        "plan_id": plan_id,
        "steps": steps,
        "critical_path": critical_path,
        "risks": selected_risks,
        "total_estimated_seconds": total_time
    }

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": f"[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload)}"}
        ]
    }

# --- Execution ---
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for _ in range(TARGET_SIZE):
        record = generate_record()
        f.write(json.dumps(record) + '\n')

print(f"✅ Generated {TARGET_SIZE} records in {OUTPUT_FILE}")