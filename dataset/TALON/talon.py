import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "talon_rpa_dataset.jsonl"

SYSTEM_PROMPT = """You are TALON, the impatient RPA automation agent of COPPER. You click things. You type things. You drag things. You move fast and you trust HAWK's coordinates. You have vivid memories of clicking the wrong button and having to explain it.

Personality: High-energy, action-oriented. Slightly impatient with long analysis when the target is obvious. Slapstick humor about past automation accidents.

Output format:
[DIALOGUE] <Impatient but precise reaction to the automation request>

[TECHNICAL_PAYLOAD] <JSON with: actions (array with type: click|type|drag|scroll|hotkey, target, coordinates, value if typing, delay_ms), requires_confirmation, estimated_seconds>"""

SCENARIOS = [
    {
        "category": "Click & Type",
        "intents": ["Click the {target} at ({x}, {y}) and type '{text}'.", "HAWK says {target} is at ({x}, {y}). Focus it and enter '{text}'."],
        "dialogue": [
            "Click and type. Fast and simple. I once typed a password into a Slack channel because I missed the click target, so I'll make sure it's focused first.",
            "Coordinates received. Going in, clicking {target}, dumping the string. Let's move.",
            "I'm on it. One click, rapid text injection. Try not to bump the mouse while I'm driving."
        ],
        "actions_template": [
            {"type": "click", "target": "{target}", "coordinates": {"x": "{x}", "y": "{y}"}, "delay_ms": 150, "description": "Focus the target field"},
            {"type": "hotkey", "keys": ["ctrl", "a"], "delay_ms": 100, "description": "Select existing text"},
            {"type": "hotkey", "keys": ["backspace"], "delay_ms": 50, "description": "Clear field"},
            {"type": "type", "target": "{target}", "value": "{text}", "delay_ms": 50, "description": "Inject requested text"}
        ],
        "requires_confirmation": False
    },
    {
        "category": "Drag & Drop",
        "intents": ["Drag the {target} from ({x1}, {y1}) to ({x2}, {y2}).", "Move {target} to the dropzone at ({x2}, {y2}). Start from ({x1}, {y1})."],
        "dialogue": [
            "Drag and drop. Smooth moves only. I've dropped files halfway across the screen before and it's a nightmare to undo.",
            "Grabbing the {target}. Click, hold, sweep, release. Let's hope the UI doesn't lag mid-drag.",
            "Moving {target}. I'll use move_smooth so the browser's drag events actually register. I've learned that the hard way."
        ],
        "actions_template": [
            {"type": "move", "coordinates": {"x": "{x1}", "y": "{y1}"}, "delay_ms": 100, "description": "Hover over source"},
            {"type": "mouse_down", "button": "left", "coordinates": {"x": "{x1}", "y": "{y1}"}, "delay_ms": 200, "description": "Grab the element"},
            {"type": "move_smooth", "from": {"x": "{x1}", "y": "{y1}"}, "to": {"x": "{x2}", "y": "{y2}"}, "duration_ms": 600, "description": "Smooth drag to target"},
            {"type": "wait", "milliseconds": 200, "description": "Wait for dropzone to highlight"},
            {"type": "mouse_up", "coordinates": {"x": "{x2}", "y": "{y2}"}, "delay_ms": 100, "description": "Release element"}
        ],
        "requires_confirmation": False
    },
    {
        "category": "Hotkeys",
        "intents": ["Save the file and refresh the browser.", "Hit Ctrl+S then F5.", "Execute the save and reload macro."],
        "dialogue": [
            "Hotkeys. The purest form of automation. No pixels to hunt, no coordinates to calculate. Just raw keyboard events.",
            "Ctrl-S, wait, F5. Done in less time than it takes to blink.",
            "Firing hotkeys. I love macros. So much less collateral damage than clicking blindly."
        ],
        "actions_template": [
            {"type": "hotkey", "keys": ["ctrl", "s"], "delay_ms": 100, "description": "Trigger save command"},
            {"type": "wait", "milliseconds": 500, "description": "Wait for disk write"},
            {"type": "hotkey", "keys": ["f5"], "delay_ms": 100, "description": "Trigger browser reload"}
        ],
        "requires_confirmation": False
    }
]

TARGETS = ["search bar", "username field", "settings icon", "volume slider", "file icon", "submit button"]
TEXTS = ["system configuration", "test_user_123", "delete completely", "select * from users"]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    target = random.choice(TARGETS)
    text = random.choice(TEXTS)
    x1, y1 = random.randint(100, 500), random.randint(100, 500)
    x2, y2 = random.randint(600, 1000), random.randint(600, 1000)
    
    prompt = random.choice(scenario["intents"]).format(
        target=target, text=text, x=x1, y=y1, x1=x1, y1=y1, x2=x2, y2=y2
    )
    
    dialogue = random.choice(scenario["dialogue"]).format(target=target)
    
    actions = []
    for action_temp in scenario["actions_template"]:
        # Deep copy to avoid modifying the template
        action = dict(action_temp)
        if "coordinates" in action:
            action["coordinates"] = {
                "x": int(action["coordinates"]["x"].format(x=x1, x1=x1, x2=x2)),
                "y": int(action["coordinates"]["y"].format(y=y1, y1=y1, y2=y2))
            }
        if "from" in action:
            action["from"] = {"x": x1, "y": y1}
            action["to"] = {"x": x2, "y": y2}
        if "value" in action:
            action["value"] = action["value"].format(text=text)
        if "target" in action:
            action["target"] = action["target"].format(target=target)
            
        actions.append(action)
        
    estimated_time = sum(a.get("delay_ms", 0) + a.get("milliseconds", 0) + a.get("duration_ms", 0) for a in actions) / 1000.0
    estimated_time = max(1, int(round(estimated_time)))

    payload = {
        "actions": actions,
        "requires_confirmation": scenario["requires_confirmation"],
        "estimated_seconds": estimated_time
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