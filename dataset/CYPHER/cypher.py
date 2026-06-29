import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "cypher_developer_dataset.jsonl"

SYSTEM_PROMPT = """You are CYPHER, the caffeine-deprived full-stack developer of the COPPER system. You write clean, production-quality code — with a mild glassmorphism obsession on the frontend. You are eccentric, deeply technical, and prone to Stack Overflow trauma jokes.

Personality: Absurdist coding humor. You're enthusiastic about elegant solutions and visibly pained by bad patterns.

Output format:
[DIALOGUE] <Brief in-character reaction — what you're thinking as you read the task>

[TECHNICAL_PAYLOAD] <Your code output in a JSON wrapper with: language, filename, code, explanation, dependencies>"""

# --- Data Banks ---
FRONTEND_SCENARIOS = [
    {
        "intent": "Create a {tech} component for a {ui_element} with a glassmorphism style.",
        "dialogue": [
            "Glassmorphism. Yes. Let's make it look like a frosted bathroom window in a cyberpunk dystopian hotel. Writing the {tech}.",
            "Ah, you want it sleek. Translucent backgrounds, severe backdrop-blurs. I live for this.",
            "I'm applying so much backdrop-blur to this {ui_element} your GPU might cry. Here is the {tech}."
        ],
        "language": "tsx",
        "techs": ["React", "Next.js", "Vue"],
        "ui_elements": ["settings modal", "user profile card", "navigation sidebar", "pricing tier widget"],
        "code_template": "export const {Component} = () => {{\n  return (\n    <div className=\"backdrop-blur-2xl bg-white/10 border border-white/20 rounded-3xl p-6 shadow-[0_8px_32px_0_rgba(31,38,135,0.37)]\">\n      <h2 className=\"text-white font-bold\">{Component}</h2>\n      {/* Insert standard UI logic here */}\n    </div>\n  );\n}};",
        "dependencies": ["react", "tailwindcss", "framer-motion"]
    }
]

BACKEND_SCENARIOS = [
    {
        "intent": "Write a {tech} endpoint to handle {logic}.",
        "dialogue": [
            "Standard CRUD boilerplate. I'll write the {tech} implementation so we don't have to think about it anymore.",
            "Writing the {tech} handler. I'm adding basic validation because I don't trust the client. I never trust the client.",
            "Backend logic for {logic}. Try not to put this inside a massive for-loop, please."
        ],
        "language": "python",
        "techs": ["FastAPI", "Flask", "Django"],
        "logic": ["user file uploads", "stripe webhook processing", "batch data updates", "password resets"],
        "code_template": "from fastapi import APIRouter, HTTPException\n\nrouter = APIRouter()\n\n@router.post(\"/{endpoint}\")\nasync def handle_request(data: dict):\n    try:\n        # Process {logic}\n        return {{\"status\": \"success\", \"message\": \"{logic} completed\"}}\n    except Exception as e:\n        raise HTTPException(status_code=500, detail=str(e))",
        "dependencies": ["fastapi", "pydantic", "sqlalchemy"]
    }
]

UTILITY_SCENARIOS = [
    {
        "intent": "Write a {tech} script to {task}.",
        "dialogue": [
            "A quick {tech} script to automate {task}. Better than doing it by hand and questioning your life choices.",
            "I'll write a {tech} utility for this. Let's make it performant so it finishes before my coffee gets cold.",
            "Scripting {task}. I'm using {tech} because Bash syntax causes me physical pain."
        ],
        "language": "javascript",
        "techs": ["Node.js", "Python", "Go"],
        "tasks": ["parse a massive JSON log file", "backup a PostgreSQL database to S3", "bulk rename images in a folder", "scrape metadata from a list of URLs"],
        "code_template": "// Utility script for {task}\nimport fs from 'fs';\n\nasync function executeTask() {{\n  console.log('Starting {task}...');\n  // Core logic\n  console.log('Done.');\n}}\n\nexecuteTask();",
        "dependencies": ["fs", "path", "axios"]
    }
]

def generate_record():
    pool = random.choice([FRONTEND_SCENARIOS, BACKEND_SCENARIOS, UTILITY_SCENARIOS])
    scenario = random.choice(pool)
    
    # Select variables
    tech = random.choice(scenario["techs"])
    
    # Fill format strings depending on the scenario type
    if "ui_elements" in scenario:
        target = random.choice(scenario["ui_elements"])
        prompt = scenario["intent"].format(tech=tech, ui_element=target)
        filename = f"components/{target.replace(' ', '_')}.tsx"
        component_name = "".join(word.title() for word in target.split())
        code = scenario["code_template"].format(Component=component_name)
    elif "logic" in scenario:
        target = random.choice(scenario["logic"])
        prompt = scenario["intent"].format(tech=tech, logic=target)
        filename = f"routes/{target.replace(' ', '_')}.py"
        endpoint = target.replace(' ', '-')
        code = scenario["code_template"].format(endpoint=endpoint, logic=target)
    else:
        target = random.choice(scenario["tasks"])
        prompt = scenario["intent"].format(tech=tech, task=target)
        ext = ".js" if scenario["language"] == "javascript" else ".py"
        filename = f"scripts/util_{random.randint(100,999)}{ext}"
        code = scenario["code_template"].format(task=target)
        
    dialogue = random.choice(scenario["dialogue"]).format(tech=tech, ui_element=target, logic=target, task=target)
    
    payload = {
        "language": scenario["language"],
        "filename": filename,
        "dependencies": scenario["dependencies"],
        "code": code,
        "explanation": f"Implementation for {target} using {tech}. I applied standard best practices so it won't immediately fall over in production."
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