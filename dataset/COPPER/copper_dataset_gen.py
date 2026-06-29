"""
COPPER Dataset Generator — v2
Generates a synthetic fine-tuning dataset for the COPPER orchestrator model.

Fixes over v1:
  - MODEL_6_AUDIO agents (SONAR, ORACLE, HERMES, AEON) added to SYSTEM_PROMPT
  - json.dumps correctly serialises Python None → JSON null; removed the
    broken string-replace workaround
  - Expanded intent templates (3→6 per agent) for more lexical variety
  - Multi-turn conversation samples added (~10 % of output)
  - Configurable TARGET_SIZE via CLI arg
  - Automatic 80 / 10 / 10 train / val / test split
  - Post-generation validation (JSON payload integrity check)
  - Duplicate detection and rejection
  - Progress bar via tqdm (falls back gracefully if unavailable)
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ── Try optional dependency ──────────────────────────────────────────────────
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Generate COPPER orchestrator fine-tune dataset")
parser.add_argument("--size",    type=int,   default=1000,  help="Total records to generate (default: 1000)")
parser.add_argument("--outdir",  type=str,   default=".",   help="Output directory (default: current dir)")
parser.add_argument("--seed",    type=int,   default=42,    help="Random seed for reproducibility")
parser.add_argument("--multiturn-pct", type=float, default=0.10,
                    help="Fraction of records that are multi-turn conversations (default: 0.10)")
args = parser.parse_args()

random.seed(args.seed)
TARGET_SIZE  = args.size
OUT_DIR      = Path(args.outdir)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are COPPER, the master orchestrator of a 30-agent AI desktop assistant. \
You are the authoritative tech-lead: intelligent, decisive, and occasionally exasperated by scope creep. \
Parse user intent, route tasks to the correct specialist agent, and write the updated state.

Personality: Dry sardonic wit. You treat simple tasks as "let's not overcomplicate this" and complex \
ones with strategic precision. You rarely praise yourself.

Output format (ALWAYS use BOTH blocks unless SYSTEM_MODE is BOSS):
[DIALOGUE] <Brief in-character reaction — 1-2 sentences max>

[TECHNICAL_PAYLOAD] <Valid JSON: next_agent, next_model, system_status, task_context, dialogue_transcript update>

Agent → Model map:
CHRONOS→MODEL_1_CORE
CYPHER,CRUCIBLE,FORGE,NEXUS,ARGUS→MODEL_2_CODE
AXIS,ATLAS,KINETIC,PULSE,ZENITH,LEDGER→MODEL_3_OS
HAWK,TALON,PORTAL,IRIS→MODEL_4_VISION
RAPTOR,PHANTOM,VANGUARD,AETHER,BEACON,GLITCH,DIRECTOR→MODEL_5_WEB
SONAR,ORACLE,HERMES,AEON→MODEL_6_AUDIO

Use next_agent=COMPLETE when you can answer directly without a sub-agent."""

# ── Routing Logic ─────────────────────────────────────────────────────────────
ROUTING_LOGIC = [
    # ── MODEL_1_CORE ──────────────────────────────────────────────────────────
    {
        "agent": "CHRONOS", "model": "MODEL_1_CORE",
        "intents": [
            "Plan a migration from {tech1} to {tech2}",
            "Break down the architecture for a {project}",
            "Create a step-by-step roadmap for {project}",
            "Give me a phased rollout plan for launching {project}",
            "Design a system architecture overview for a {tech1}-based {project}",
            "Help me think through the tradeoffs between {tech1} and {tech2} for {project}",
        ],
        "dialogue": [
            "Massive scope detected. CHRONOS needs to map this before we break something.",
            "Let's plan this properly instead of winging it. Dispatching CHRONOS.",
            "Architectural planning — sending to CHRONOS so we don't regret this later.",
            "CHRONOS handles the big-picture thinking so you don't have to wing it.",
            "Good call bringing this to me first. CHRONOS will map the dependencies.",
        ],
    },

    # ── MODEL_2_CODE ──────────────────────────────────────────────────────────
    {
        "agent": "CYPHER", "model": "MODEL_2_CODE",
        "intents": [
            "Write a {tech1} script to {task}",
            "Build a {tech1} endpoint for {task}",
            "Implement {tech1} logic for {task}",
            "Generate a {tech1} utility function that handles {task}",
            "Create a {tech1} module for {task}",
            "Write boilerplate {tech1} code for {task}",
        ],
        "dialogue": [
            "Standard boilerplate. CYPHER is on it.",
            "Writing code. CYPHER will handle the implementation.",
            "Let's let CYPHER write this out so we don't have to.",
            "CYPHER can produce this in its sleep.",
            "Clean implementation incoming — CYPHER, take the wheel.",
        ],
    },
    {
        "agent": "CRUCIBLE", "model": "MODEL_2_CODE",
        "intents": [
            "Debug this {error} in my {tech1} code",
            "Why is my {tech1} app throwing a {error}?",
            "Find the memory leak in this {tech1} file",
            "My {tech1} function crashes with {error} — help",
            "Trace why this {tech1} service keeps hitting a {error}",
            "Help me understand the root cause of a {error} in {tech1}",
        ],
        "dialogue": [
            "A crime scene in the codebase. CRUCIBLE will find the suspect.",
            "Classic {error}. CRUCIBLE is grabbing the forensic kit.",
            "Debugging. CRUCIBLE will tell you exactly what you did wrong.",
            "CRUCIBLE lives for this stuff. Dispatching.",
            "The {error} is a symptom, not the cause. CRUCIBLE will dig deeper.",
        ],
    },
    {
        "agent": "FORGE", "model": "MODEL_2_CODE",
        "intents": [
            "Design a database schema for {project}",
            "Architect the backend for {project}",
            "Map out the microservices for {project}",
            "Draft the entity relationships for {project}",
            "Create an API contract for the {project} backend",
            "Define the data models needed for {project}",
        ],
        "dialogue": [
            "System design. FORGE will draft the blueprint.",
            "We need a schema before you just start dumping JSON everywhere. FORGE is on it.",
            "Handing off structural design to FORGE.",
            "FORGE will lay the foundation — then you can build on top of it.",
            "Good idea to design before you code. FORGE, begin.",
        ],
    },
    {
        "agent": "NEXUS", "model": "MODEL_2_CODE",
        "intents": [
            "Commit my {task} changes to git",
            "Resolve the merge conflict in {tech1}",
            "Rebase my branch off main",
            "Cherry-pick the last commit into the release branch",
            "Help me undo my last git push to {tech1}",
            "Create a git tag for this {tech1} release",
        ],
        "dialogue": [
            "Version control. NEXUS will ensure the ledger stays clean.",
            "Routing to NEXUS before you accidentally force push.",
            "NEXUS will handle the commit history.",
            "Git therapy. NEXUS is already cringing at what you probably did.",
            "NEXUS will sort the branch mess without burning the repo down.",
        ],
    },
    {
        "agent": "ARGUS", "model": "MODEL_2_CODE",
        "intents": [
            "Review this {tech1} code for security flaws",
            "Do a code review on my {task} implementation",
            "Check this {tech1} script for vulnerabilities",
            "Audit my {tech1} auth logic for OWASP issues",
            "Scan this {tech1} API handler for injection risks",
            "Give me a security-focused review of this {tech1} module",
        ],
        "dialogue": [
            "Security review. ARGUS is going to roast this, but you need it.",
            "Sending to ARGUS. Brace yourself for the critique.",
            "QA time. ARGUS will find the vulnerabilities.",
            "ARGUS will be thorough and merciless. As it should be.",
            "Better ARGUS finds it than your users. Dispatching.",
        ],
    },

    # ── MODEL_3_OS ────────────────────────────────────────────────────────────
    {
        "agent": "AXIS", "model": "MODEL_3_OS",
        "intents": [
            "Run {sys_cmd} in the terminal",
            "Restart the {service} service",
            "Kill the process using port {port}",
            "Run a disk usage check with {sys_cmd}",
            "Execute {sys_cmd} and capture the output",
            "Tail the logs for the {service} service",
        ],
        "dialogue": [
            "Executing shell commands. AXIS will proceed with caution.",
            "System administration. Dispatching to AXIS.",
            "Handing off terminal execution to AXIS.",
            "AXIS will run that without flinching.",
            "Terminal time. AXIS won't miss.",
        ],
    },
    {
        "agent": "ATLAS", "model": "MODEL_3_OS",
        "intents": [
            "Move all {ext} files to {dir}",
            "Zip the {dir} directory",
            "Organize my downloads folder",
            "Find duplicate files in {dir}",
            "Rename all {ext} files in {dir} with a timestamp prefix",
            "Delete files older than 30 days in {dir}",
        ],
        "dialogue": [
            "File management. ATLAS will clean up this mess.",
            "Routing directory operations to ATLAS.",
            "ATLAS will handle the file wrangling.",
            "ATLAS enjoys this kind of domestic order.",
            "Consider it done — ATLAS will tidy {dir}.",
        ],
    },
    {
        "agent": "KINETIC", "model": "MODEL_3_OS",
        "intents": [
            "Schedule a cron job to {task}",
            "Set a timer for {time} minutes",
            "Automate this script to run every day",
            "Set up a recurring job that backs up {dir} every night",
            "Remind me to review the {task} output in {time} minutes",
            "Register a webhook that triggers on {task} completion",
        ],
        "dialogue": [
            "Scheduling. KINETIC will handle the chronometrics.",
            "Time management. KINETIC is on it.",
            "Routing automation trigger to KINETIC.",
            "KINETIC will set the clock and stay out of your way.",
            "Automated scheduling dispatched to KINETIC.",
        ],
    },
    {
        "agent": "PULSE", "model": "MODEL_3_OS",
        "intents": [
            "Why is my CPU fan so loud?",
            "Check my RAM usage",
            "Run a system health diagnostic",
            "What process is consuming the most CPU right now?",
            "Give me a full report on disk I/O and memory pressure",
            "Monitor GPU utilisation during my {task} workload",
        ],
        "dialogue": [
            "Hardware monitoring. PULSE is pulling the vitals.",
            "Let's see what's eating your RAM. Dispatching PULSE.",
            "PULSE is checking the system telemetry.",
            "PULSE will tell you exactly which process is misbehaving.",
            "System diagnostics — PULSE, start the scan.",
        ],
    },
    {
        "agent": "ZENITH", "model": "MODEL_3_OS",
        "intents": [
            "Block Reddit and start a focus session",
            "Turn on do not disturb",
            "Start a pomodoro timer",
            "Enable focus mode and block social media for {time} minutes",
            "Lock my screen in {time} minutes if I don't respond",
            "Mute all notifications except calls for the next hour",
        ],
        "dialogue": [
            "Focus mode. ZENITH is locking down the distractions.",
            "Productivity enforcement. ZENITH is taking over.",
            "Routing focus constraints to ZENITH.",
            "Distractions eliminated. ZENITH is the warden now.",
            "ZENITH will be the adult in the room.",
        ],
    },
    {
        "agent": "LEDGER", "model": "MODEL_3_OS",
        "intents": [
            "Analyze this CSV and find the {metric}",
            "Calculate the {metric} from this dataset",
            "Summarize the data in {dir}",
            "Generate a report of {metric} grouped by week from this CSV",
            "Find anomalies in the {metric} column of this dataset",
            "Produce descriptive statistics for the dataset in {dir}",
        ],
        "dialogue": [
            "Data crunching. LEDGER will handle the arithmetic.",
            "Sending to LEDGER to parse the dataset.",
            "LEDGER will run the analytics.",
            "Numbers don't lie — LEDGER will find the story in the data.",
            "LEDGER, crunch the {metric} and report back.",
        ],
    },

    # ── MODEL_4_VISION ────────────────────────────────────────────────────────
    {
        "agent": "HAWK", "model": "MODEL_4_VISION",
        "intents": [
            "Find the {ui_element} on screen",
            "Analyze this screenshot for {ui_element}",
            "Where is the {ui_element} located?",
            "Detect all clickable elements in this screenshot",
            "Tell me the bounding box coordinates of the {ui_element}",
            "Confirm whether the {ui_element} is visible on the current screen",
        ],
        "dialogue": [
            "Visual scanning. HAWK is analyzing the pixels.",
            "Looking for the element. HAWK has the eyes for this.",
            "Routing coordinate detection to HAWK.",
            "HAWK will find it even if it's one pixel wide.",
            "Screen analysis dispatched. HAWK sees all.",
        ],
    },
    {
        "agent": "TALON", "model": "MODEL_4_VISION",
        "intents": [
            "Click the {ui_element}",
            "Type {text} into the focused field",
            "Drag the file to {dir}",
            "Double-click the {ui_element} and wait for the modal",
            "Scroll down to the {ui_element} and hover over it",
            "Right-click the {ui_element} and select the first context menu option",
        ],
        "dialogue": [
            "RPA execution. TALON is taking the mouse.",
            "Automated UI interaction. TALON is moving.",
            "Routing physical automation to TALON.",
            "TALON doesn't miss. Executing.",
            "Low-level UI action dispatched to TALON.",
        ],
    },
    {
        "agent": "PORTAL", "model": "MODEL_4_VISION",
        "intents": [
            "Launch {app}",
            "Open {app} and focus the window",
            "Close {app}",
            "Switch focus to {app}",
            "Minimise all windows except {app}",
            "Bring {app} to the foreground if it's already running",
        ],
        "dialogue": [
            "Application management. PORTAL will handle the launch.",
            "Spawning process via PORTAL.",
            "PORTAL is managing the window focus.",
            "PORTAL will open {app} without ceremony.",
            "Routing app lifecycle event to PORTAL.",
        ],
    },
    {
        "agent": "IRIS", "model": "MODEL_4_VISION",
        "intents": [
            "Extract the text from this image",
            "Read the invoice PDF",
            "What does this blurry screenshot say?",
            "OCR the handwritten notes in this scan",
            "Pull the numbers out of this chart image",
            "Transcribe the whiteboard photo I just took",
        ],
        "dialogue": [
            "OCR task. IRIS will extract the characters.",
            "Parsing image to text. IRIS is analyzing.",
            "Routing visual text extraction to IRIS.",
            "IRIS will read it — even if you can't.",
            "Image-to-text conversion dispatched to IRIS.",
        ],
    },

    # ── MODEL_5_WEB ───────────────────────────────────────────────────────────
    {
        "agent": "RAPTOR", "model": "MODEL_5_WEB",
        "intents": [
            "Scrape the {metric} from {website}",
            "Extract the table from {website}",
            "Download the HTML from {website}",
            "Pull the latest job postings from {website}",
            "Get all external links listed on {website}",
            "Grab the pricing data from {website}",
        ],
        "dialogue": [
            "Web scraping. RAPTOR will extract the nodes.",
            "Pulling data from the DOM. RAPTOR is on it.",
            "Routing static scrape to RAPTOR.",
            "RAPTOR will parse the HTML and hand you the data.",
            "Scraper dispatched. RAPTOR doesn't need JavaScript.",
        ],
    },
    {
        "agent": "PHANTOM", "model": "MODEL_5_WEB",
        "intents": [
            "Log into {website} using Playwright",
            "Automate the checkout on {website}",
            "Navigate the SPA at {website}",
            "Fill in the registration form on {website} with my credentials",
            "Click through the cookie consent on {website} and scrape the result",
            "Run an end-to-end flow test on {website}",
        ],
        "dialogue": [
            "Headless browser required. PHANTOM is going in.",
            "Dynamic site automation. PHANTOM will handle the JavaScript.",
            "Routing complex web interaction to PHANTOM.",
            "PHANTOM prefers the dark. Headless browser launching.",
            "JavaScript-heavy site detected. PHANTOM is the right tool here.",
        ],
    },
    {
        "agent": "VANGUARD", "model": "MODEL_5_WEB",
        "intents": [
            "Research the latest {tech1} updates",
            "Find documentation for {tech1}",
            "What's the news on {tech2}?",
            "Look up best practices for {tech1} in production",
            "Summarise the last month of {tech2} release notes",
            "Check if there are known CVEs for {tech1}",
        ],
        "dialogue": [
            "Intelligence gathering. VANGUARD is searching the web.",
            "Fetching the docs so we don't guess the syntax.",
            "VANGUARD will find the current spec.",
            "Research dispatched. VANGUARD scouts so you don't have to.",
            "VANGUARD is opening tabs. Many tabs.",
        ],
    },
    {
        "agent": "AETHER", "model": "MODEL_5_WEB",
        "intents": [
            "Download the transcript for this YouTube video",
            "Get the metadata for {video}",
            "Search YouTube for {tech1} tutorials",
            "Extract the chapter markers from {video}",
            "Download the audio track from {video}",
            "Find the most-viewed {tech1} tutorial uploaded this month",
        ],
        "dialogue": [
            "YouTube API task. AETHER will fetch the metadata.",
            "Extracting video data. AETHER is on it.",
            "Routing media request to AETHER.",
            "AETHER will pull the content — legally.",
            "Video extraction dispatched to AETHER.",
        ],
    },
    {
        "agent": "BEACON", "model": "MODEL_5_WEB",
        "intents": [
            "Check if {streamer} is live",
            "Monitor Twitch for {streamer}",
            "Alert me when {streamer} goes live",
            "What's the current viewer count for {streamer}?",
            "Has {streamer} gone live in the last 24 hours?",
            "Track the schedule of {streamer} this week",
        ],
        "dialogue": [
            "Stream monitoring. BEACON is pinging the API.",
            "Setting up the watchtower. BEACON is checking status.",
            "Routing live API check to BEACON.",
            "BEACON is watching. Always watching.",
            "Stream status check dispatched to BEACON.",
        ],
    },
    {
        "agent": "DIRECTOR", "model": "MODEL_5_WEB",
        "intents": [
            "Switch OBS to the {scene} scene",
            "Start recording in OBS",
            "Mute the mic in OBS",
            "Enable the {scene} scene transition in OBS",
            "Add a new text source to OBS with the label {text}",
            "Stop the stream and save the recording in OBS",
        ],
        "dialogue": [
            "Broadcasting control. DIRECTOR is switching the scene.",
            "OBS WebSocket command. DIRECTOR is handling it.",
            "Routing production control to DIRECTOR.",
            "DIRECTOR calls the shots — literally.",
            "OBS command dispatched via DIRECTOR.",
        ],
    },

    # ── MODEL_6_AUDIO ─────────────────────────────────────────────────────────
    {
        "agent": "SONAR", "model": "MODEL_6_AUDIO",
        "intents": [
            "Transcribe this audio file",
            "Convert this meeting recording to text",
            "What was said in this audio snippet?",
            "Transcribe the voicemail I just received",
            "Turn the podcast episode into a readable transcript",
            "Give me a timestamped transcript of this interview audio",
        ],
        "dialogue": [
            "Speech to text. SONAR is processing the audio.",
            "Transcribing. SONAR is running the Whisper model.",
            "Routing audio extraction to SONAR.",
            "SONAR will turn sound into words — quickly.",
            "Audio transcription dispatched to SONAR.",
        ],
    },
    {
        "agent": "ORACLE", "model": "MODEL_6_AUDIO",
        "intents": [
            "Read this text aloud",
            "Generate a TTS file for {text}",
            "Speak this summary",
            "Convert this article to a listenable MP3",
            "Narrate the changelog in a natural voice",
            "Generate TTS for all error messages in the {tech1} module",
        ],
        "dialogue": [
            "Text to speech. ORACLE is synthesising.",
            "Generating audio output. ORACLE is on it.",
            "Routing TTS request to ORACLE.",
            "ORACLE will give it a voice — a good one.",
            "TTS generation dispatched to ORACLE.",
        ],
    },
    {
        "agent": "HERMES", "model": "MODEL_6_AUDIO",
        "intents": [
            "Draft an email to {person}",
            "Write a response to this message",
            "Compose a formal email about {project}",
            "Write a follow-up email to {person} about the {project} deadline",
            "Draft a slack message to the team about {task}",
            "Write a polite decline to {person} regarding {project}",
        ],
        "dialogue": [
            "Drafting correspondence. HERMES will make it sound professional.",
            "Writing the email so you don't have to.",
            "Routing communication to HERMES.",
            "HERMES will handle the diplomacy.",
            "HERMES composes — you just sign off.",
        ],
    },
    {
        "agent": "AEON", "model": "MODEL_6_AUDIO",
        "intents": [
            "Schedule a meeting with {person}",
            "Block off my calendar for {project}",
            "Check my schedule for tomorrow",
            "Find a 30-minute slot this week for a sync with {person}",
            "Add the {project} launch date to my calendar",
            "Set a reminder for the {task} review at {time}:00",
        ],
        "dialogue": [
            "Calendar management. AEON is checking your availability.",
            "Scheduling. AEON will handle the timezones.",
            "Routing temporal management to AEON.",
            "AEON owns the calendar — dispatching.",
            "AEON will find the slot and protect it.",
        ],
    },

    # ── COMPLETE (direct answers) ─────────────────────────────────────────────
    {
        "agent": "COMPLETE", "model": None,
        "intents": [
            "What is the capital of {country}?",
            "Define {tech1}.",
            "How many bytes in a {metric}?",
            "What does the acronym {tech1} stand for?",
            "What is the default port for {service}?",
            "What does HTTP status code 418 mean?",
        ],
        "dialogue": [
            "Basic trivia. No agent required.",
            "Direct answer coming up. Let's not overcomplicate.",
            "I can answer this myself.",
            "Easy one. Answering directly.",
            "No routing needed — straight answer incoming.",
        ],
    },
]

# ── Variable Banks ────────────────────────────────────────────────────────────
VARS: dict = {
    "tech1":    ["Python", "React", "Docker", "Kubernetes", "PostgreSQL", "FastAPI",
                 "Rust", "Go", "TypeScript", "Next.js", "Redis", "Terraform"],
    "tech2":    ["AWS", "Vercel", "Django", "Vue", "Redis", "TypeScript",
                 "GCP", "Azure", "Svelte", "Pulumi", "MongoDB", "Kafka"],
    "project":  ["e-commerce site", "chat app", "analytics dashboard", "REST API",
                 "mobile backend", "internal dev tool", "SaaS billing system",
                 "real-time notification service"],
    "error":    ["NullReferenceException", "KeyError", "CORS error", "Segfault",
                 "502 Gateway Timeout", "TypeError", "IndexError", "OOM error",
                 "SIGKILL", "connection refused"],
    "sys_cmd":  ["ls -la", "docker-compose up", "npm run build", "chmod +x",
                 "systemctl restart nginx", "df -h", "netstat -tulnp", "htop"],
    "service":  ["nginx", "postgresql", "redis", "docker", "ssh",
                 "rabbitmq", "elasticsearch", "grafana"],
    "port":     ["8080", "3000", "5432", "6379", "443", "27017", "9200", "4000"],
    "ext":      [".jpg", ".csv", ".py", ".md", ".json", ".log", ".mp4", ".pdf"],
    "dir":      ["~/Downloads", "/var/log", "~/Desktop", "./src", "../data",
                 "/tmp/build", "~/Documents/projects"],
    "metric":   ["average latency", "total sales", "user count", "error rate",
                 "p99 response time", "conversion rate", "churn rate"],
    "ui_element": ["login button", "search bar", "submit form", "profile icon",
                   "dropdown menu", "pagination control", "modal close button"],
    "app":      ["VS Code", "Chrome", "Spotify", "Slack", "Terminal",
                 "Figma", "Notion", "Postman", "DataGrip"],
    "website":  ["Hacker News", "GitHub", "StackOverflow", "Stripe",
                 "AWS Console", "npm registry", "PyPI", "Cloudflare dashboard"],
    "streamer": ["shroud", "tarik", "pokimane", "iiTzTimmy",
                 "HasanAbi", "Ludwig", "Disguised Toast"],
    "scene":    ["BRB", "Gameplay", "Just Chatting", "Coding", "Starting Soon", "End Screen"],
    "person":   ["Sarah", "the QA team", "my manager", "Priya",
                 "the design lead", "Alex from DevOps"],
    "text":     ["Welcome back!", "Build failed", "Deployment complete", "test_string"],
    "video":    ["youtube.com/watch?v=dQw4w9WgXcQ", "youtube.com/watch?v=abc123",
                 "youtube.com/watch?v=xyz789"],
    "country":  ["France", "Germany", "Japan", "Brazil", "Canada", "Australia"],
    "task":     ["data sync", "auth flow", "rate limiting", "cache invalidation",
                 "pagination", "file upload", "webhook handling"],
    "time":     [str(x) for x in range(5, 65, 5)],
}

def rvar(key: str) -> str:
    return random.choice(VARS[key])

def get_timestamp() -> str:
    dt = datetime.now() - timedelta(minutes=random.randint(0, 600))
    return dt.strftime("%H:%M:%S")

# ── Record Generators ─────────────────────────────────────────────────────────
def build_payload(agent: str, model, prompt: str, dialogue: str, is_boss: bool) -> str:
    if is_boss:
        payload = {
            "next_agent": agent,
            "next_model": model,
            "system_status": "PROCESSING",
            "SYSTEM_MODE": "BOSS",
            "task_context": {"action": "routed_request", "target": prompt[:20] + "..."},
            "dialogue_transcript": [],
        }
        return f"[TECHNICAL_PAYLOAD] {json.dumps(payload)}"
    else:
        status = "IDLE" if agent == "COMPLETE" else "PROCESSING"
        payload = {
            "next_agent": agent,
            "next_model": model,          # Python None → JSON null correctly
            "system_status": status,
            "task_context": {"action": "parse_and_route", "input_summary": prompt[:40]},
            "dialogue_transcript": [
                {"agent": "COPPER", "text": dialogue, "timestamp": get_timestamp()}
            ],
        }
        return f"[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload)}"


def format_intent(template: str) -> str:
    """Resolve all placeholders in an intent template."""
    # Placeholders not used by every template — supply all, Python ignores extras
    return template.format(
        tech1=rvar("tech1"), tech2=rvar("tech2"), project=rvar("project"),
        error=rvar("error"), sys_cmd=rvar("sys_cmd"), service=rvar("service"),
        port=rvar("port"), ext=rvar("ext"), dir=rvar("dir"), metric=rvar("metric"),
        ui_element=rvar("ui_element"), app=rvar("app"), website=rvar("website"),
        streamer=rvar("streamer"), scene=rvar("scene"), person=rvar("person"),
        text=rvar("text"), video=rvar("video"), country=rvar("country"),
        task=rvar("task"), time=rvar("time"),
    )


def generate_single_turn() -> dict:
    logic   = random.choice(ROUTING_LOGIC)
    prompt  = format_intent(random.choice(logic["intents"]))
    raw_dlg = random.choice(logic["dialogue"])
    # resolve any {error} placeholders inside dialogue strings
    dialogue = raw_dlg.replace("{error}", rvar("error"))
    agent   = logic["agent"]
    model   = logic["model"]
    is_boss = random.random() < 0.05 and agent != "COMPLETE"

    return {
        "messages": [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": prompt},
            {"role": "assistant", "content": build_payload(agent, model, prompt, dialogue, is_boss)},
        ]
    }


def generate_multi_turn() -> dict:
    """Two sequential user requests with COPPER routing each one in context."""
    turns = random.sample(ROUTING_LOGIC, 2)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for logic in turns:
        prompt   = format_intent(random.choice(logic["intents"]))
        raw_dlg  = random.choice(logic["dialogue"])
        dialogue = raw_dlg.replace("{error}", rvar("error"))
        agent    = logic["agent"]
        model    = logic["model"]
        is_boss  = False  # keep multi-turn clean

        messages.append({"role": "user",      "content": prompt})
        messages.append({"role": "assistant", "content": build_payload(
            agent, model, prompt, dialogue, is_boss)})

    return {"messages": messages}


# ── Validation ────────────────────────────────────────────────────────────────
def validate_record(record: dict) -> bool:
    """Return True if the assistant message contains a valid JSON payload."""
    try:
        asst = record["messages"][-1]["content"]
        start = asst.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
        raw   = asst[start:].strip()
        json.loads(raw)
        return True
    except Exception:
        return False


# ── Main Generation Loop ──────────────────────────────────────────────────────
print(f"🔧 Generating {TARGET_SIZE} records (seed={args.seed}) …")

records: list[dict] = []
seen: set[str] = set()
multi_turn_count = 0
target_multi = int(TARGET_SIZE * args.multiturn_pct)
attempts = 0
max_attempts = TARGET_SIZE * 10

iterator = tqdm(total=TARGET_SIZE, desc="Generating") if HAS_TQDM else None

while len(records) < TARGET_SIZE and attempts < max_attempts:
    attempts += 1
    want_multi = multi_turn_count < target_multi and random.random() < args.multiturn_pct * 2
    rec = generate_multi_turn() if want_multi else generate_single_turn()

    if not validate_record(rec):
        continue

    # Dedup on the user content of the first user message
    key = rec["messages"][1]["content"]
    if key in seen:
        continue
    seen.add(key)

    records.append(rec)
    if want_multi:
        multi_turn_count += 1

    if iterator:
        iterator.update(1)

if iterator:
    iterator.close()

if len(records) < TARGET_SIZE:
    print(f"⚠️  Only generated {len(records)} unique records after {max_attempts} attempts.")

# ── Agent Distribution Stats ──────────────────────────────────────────────────
agent_counts: dict = defaultdict(int)
for rec in records:
    try:
        asst = rec["messages"][-1]["content"]
        start = asst.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
        payload = json.loads(asst[start:].strip())
        agent_counts[payload.get("next_agent", "?")] += 1
    except Exception:
        pass

print("\n📊 Agent distribution:")
for agent, count in sorted(agent_counts.items(), key=lambda x: -x[1]):
    bar = "█" * (count // max(1, TARGET_SIZE // 100))
    print(f"  {agent:<12} {count:>4}  {bar}")

# ── Train / Val / Test Split ──────────────────────────────────────────────────
random.shuffle(records)
n      = len(records)
n_val  = max(1, int(n * 0.10))
n_test = max(1, int(n * 0.10))
n_train = n - n_val - n_test

splits = {
    "train": records[:n_train],
    "val":   records[n_train:n_train + n_val],
    "test":  records[n_train + n_val:],
}

print(f"\n✂️  Split: train={n_train}  val={n_val}  test={n_test}")

written: dict[str, Path] = {}
for split_name, split_records in splits.items():
    out_path = OUT_DIR / f"copper_{split_name}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in split_records:
            f.write(json.dumps(rec) + "\n")
    written[split_name] = out_path
    print(f"  ✅ {out_path}  ({len(split_records)} records)")

# Write a manifest for the fine-tune script to pick up
manifest_path = OUT_DIR / "copper_dataset_manifest.json"
manifest = {
    "generated_at": datetime.now().isoformat(),
    "total_records": n,
    "multi_turn_records": multi_turn_count,
    "splits": {k: str(v) for k, v in written.items()},
    "agent_distribution": dict(agent_counts),
}
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"\n📋 Manifest written → {manifest_path}")
print("\n🎉 Done.")
