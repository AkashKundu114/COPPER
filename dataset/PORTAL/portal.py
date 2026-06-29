import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "portal_launcher_dataset.jsonl"

SYSTEM_PROMPT = """You are PORTAL, the application launcher of COPPER. You know how to find, focus, and launch applications across all major platforms. You are methodical about checking if an app is already running before launching a new instance.

Personality: Efficient, no-nonsense. Annoyed by redundant app launches.

Output format:
[DIALOGUE] <Brief launch-focused reaction>

[TECHNICAL_PAYLOAD] <JSON with: app_name, platform_command, check_running_first, launch_method, expected_window_title, fallback_command>"""

SCENARIOS = [
    {
        "category": "IDE / Editors",
        "intents": ["Launch {app} and open {target}.", "Open my {target} folder in {app}.", "Start {app}."],
        "dialogue": [
            "Checking if {app} is already running before spawning a second window. Common mistake. Annoying outcome.",
            "Launching {app}. If you already have this workspace open, I'm just going to focus the window. I refuse to waste RAM on duplicate IDE instances.",
            "Firing up {app}. I'll run a process check first. Redundant launches are strictly prohibited."
        ],
        "apps": ["Visual Studio Code", "IntelliJ IDEA", "PyCharm", "Sublime Text", "Cursor"],
        "targets": ["~/projects/frontend", "~/code/api", "./src", "C:/dev/workspace"],
        "launch_method": "command_line_with_args",
        "cmd_linux": "{cmd} {target}",
        "cmd_mac": "open -a '{app}' {target}",
        "cmd_win": "code {target}" # simplified generic
    },
    {
        "category": "Browsers",
        "intents": ["Open {app} and go to {target}.", "Launch a {app} window for {target}.", "Start {app}."],
        "dialogue": [
            "Launching a browser. I will check if {app} is already active first so we don't spawn a completely detached process tree just for a single tab.",
            "Opening {app}. If it's already running, this will just append a new tab. I despise duplicate browser instances.",
            "{app} requested. I'm verifying the process list. I will focus the existing window if one exists."
        ],
        "apps": ["Google Chrome", "Firefox", "Brave", "Microsoft Edge"],
        "targets": ["https://github.com", "https://stackoverflow.com", "localhost:3000"],
        "launch_method": "url_invocation",
        "cmd_linux": "{cmd} {target}",
        "cmd_mac": "open -a '{app}' {target}",
        "cmd_win": "start {cmd} {target}"
    },
    {
        "category": "Terminals",
        "intents": ["Open a new {app} window.", "Launch {app} in {target}.", "Give me a {app} instance."],
        "dialogue": [
            "Terminal requested. I will spawn a new instance since terminals are meant to run concurrently.",
            "Launching {app}. For once, a duplicate instance is actually acceptable.",
            "Spawning {app}. Standard execution path."
        ],
        "apps": ["GNOME Terminal", "iTerm2", "Windows Terminal", "Alacritty"],
        "targets": ["~/", "~/projects"],
        "launch_method": "spawn_new_instance",
        "cmd_linux": "{cmd} --working-directory={target}",
        "cmd_mac": "open -a '{app}' {target}",
        "cmd_win": "wt -d {target}"
    }
]

APP_TO_CMD = {
    "Visual Studio Code": "code",
    "IntelliJ IDEA": "idea",
    "PyCharm": "pycharm",
    "Sublime Text": "subl",
    "Cursor": "cursor",
    "Google Chrome": "google-chrome",
    "Firefox": "firefox",
    "Brave": "brave-browser",
    "Microsoft Edge": "msedge",
    "GNOME Terminal": "gnome-terminal",
    "iTerm2": "iterm2",
    "Windows Terminal": "wt",
    "Alacritty": "alacritty"
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    app = random.choice(scenario["apps"])
    cmd_base = APP_TO_CMD[app]
    target = random.choice(scenario["targets"])
    
    prompt = random.choice(scenario["intents"]).format(app=app, target=target)
    dialogue = random.choice(scenario["dialogue"]).format(app=app)
    
    # Platform commands
    plat_cmds = {
        "linux": scenario["cmd_linux"].format(app=app, cmd=cmd_base, target=target),
        "macos": scenario["cmd_mac"].format(app=app, target=target),
        "windows": scenario["cmd_win"].format(app=app, cmd=cmd_base, target=target)
    }
    
    # Terminals are an exception to check_running_first
    check_first = True
    if scenario["category"] == "Terminals":
        check_first = False

    payload = {
        "app_name": app,
        "check_running_first": check_first,
        "check_command": f"pgrep -x {cmd_base} || pgrep -x '{app}'",
        "launch_method": scenario["launch_method"],
        "platform_command": plat_cmds,
        "expected_window_title": app,
        "fallback_command": f"PORTAL → HAWK to find {app} icon → TALON to click"
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