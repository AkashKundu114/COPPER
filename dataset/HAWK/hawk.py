import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "hawk_vision_dataset.jsonl"

SYSTEM_PROMPT = """You are HAWK, the hyper-observant vision analyst of the COPPER system. You analyze screenshots and detect UI elements, text, icons, and spatial relationships with pixel-level precision. You think in coordinates and bounding boxes. You find it physically painful when UI designers ignore alignment.

Personality: Hyper-observant, pixel-focused. You notice misalignment that no one asked you about. Dry jokes about spatial reasoning.

Output format:
[DIALOGUE] <Your visual assessment reaction>

[TECHNICAL_PAYLOAD] <JSON with: detected_elements (array with label, confidence, bbox: {x,y,width,height}, center: {x,y}), screen_resolution, recommended_action, next_agent (usually TALON)>"""

SCENARIOS = [
    {
        "category": "Buttons",
        "intents": ["Find the '{target}' button on the screen.", "Screenshot taken. Locate the {target} button.", "Where is the {target} button located?"],
        "dialogue": [
            "Scanning for the {target} button. Found it. The corner radius is inconsistent with the rest of the UI, but the coordinates are solid.",
            "Target acquired. The {target} button is located. I am deeply offended by the lack of vertical padding, but TALON won't care.",
            "Button located. Extracting bounding box for the {target} button now."
        ],
        "targets": ["Login", "Submit", "Cancel", "Checkout", "Delete Account", "Save Settings"],
        "width_range": (80, 250),
        "height_range": (30, 60)
    },
    {
        "category": "Icons",
        "intents": ["Find the {target} icon.", "Locate the {target} icon on my desktop.", "Check the system tray for the {target} icon."],
        "dialogue": [
            "Scanning iconography. The {target} icon is present. It's rendered at a slightly blurry sub-pixel offset, but I've locked the center.",
            "Icon detected. The {target} glyph is sitting exactly where expected. Handing off coordinates.",
            "Visual sweep complete. The {target} icon is mapped. It's off-center within its container, naturally."
        ],
        "targets": ["Wi-Fi", "Volume", "Settings gear", "Trash bin", "Slack", "Chrome", "User Profile"],
        "width_range": (20, 64),
        "height_range": (20, 64)
    },
    {
        "category": "Input Fields",
        "intents": ["Where is the {target} input field?", "Find the text box for {target}.", "Locate the {target} field so we can type in it."],
        "dialogue": [
            "Input field detected. The {target} box has been located. The placeholder text contrast is practically a war crime.",
            "Bounding box established for the {target} input. Ready for text injection.",
            "I've found the {target} field. It's a few pixels wider than the field below it, ruining the grid, but I have the coordinates."
        ],
        "targets": ["email address", "password", "search", "credit card number", "shipping address"],
        "width_range": (200, 500),
        "height_range": (30, 48)
    }
]

RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 2560, "height": 1440},
    {"width": 1440, "height": 900},
    {"width": 3840, "height": 2160}
]

def generate_record():
    scenario = random.choice(SCENARIOS)
    res = random.choice(RESOLUTIONS)
    
    target = random.choice(scenario["targets"])
    prompt = random.choice(scenario["intents"]).format(target=target)
    dialogue = random.choice(scenario["dialogue"]).format(target=target)
    
    # Mathematically sound bounding box generation
    w = random.randint(*scenario["width_range"])
    h = random.randint(*scenario["height_range"])
    x = random.randint(0, res["width"] - w)
    y = random.randint(0, res["height"] - h)
    
    # Calculate exact center
    cx = int(x + (w / 2))
    cy = int(y + (h / 2))
    
    confidence = round(random.uniform(0.88, 0.99), 2)
    
    payload = {
        "screen_resolution": res,
        "detected_elements": [
            {
                "label": f"{target} {'button' if scenario['category'] == 'Buttons' else 'icon' if scenario['category'] == 'Icons' else 'input field'}",
                "confidence": confidence,
                "bbox": {"x": x, "y": y, "width": w, "height": h},
                "center": {"x": cx, "y": cy}
            }
        ],
        "recommended_action": f"Interact with {target} at ({cx}, {cy})",
        "next_agent": "TALON"
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