"""
agents.py
==========
Single source of truth for the 30-agent roster + COPPER. Each entry carries
everything both the router (keyword matching) and the frontend brain
visualization need: which tier/model group it belongs to, a color for its
node glow, routing keywords, and a small bank of persona lines used to
flavor generated responses.

Tier order below also defines the ring order in the brain visualization
(ring 0 = COPPER core, ring 1 = MODEL_1_CORE ... ring 6 = MODEL_6_AUDIO).
"""

TIERS = [
    "MODEL_1_CORE",
    "MODEL_2_CODE",
    "MODEL_3_OS",
    "MODEL_4_VISION",
    "MODEL_5_WEB",
    "MODEL_6_AUDIO",
]

TIER_LABELS = {
    "MODEL_1_CORE": "Core Reasoning",
    "MODEL_2_CODE": "Code Engineering",
    "MODEL_3_OS": "OS & Automation",
    "MODEL_4_VISION": "Vision & RPA",
    "MODEL_5_WEB": "Web & Streaming",
    "MODEL_6_AUDIO": "Audio & Language",
}

# Tier accent colors (bronze/copper family, warming as tiers progress —
# purely aesthetic grouping for the brain map, doesn't affect logic)
TIER_COLORS = {
    "MODEL_1_CORE": "#e8c07d",
    "MODEL_2_CODE": "#eab676",
    "MODEL_3_OS": "#e0985f",
    "MODEL_4_VISION": "#d97b52",
    "MODEL_5_WEB": "#c2654a",
    "MODEL_6_AUDIO": "#a8524a",
}

AGENTS: dict[str, dict] = {
    "CHRONOS": {
        "tier": "MODEL_1_CORE", "name": "Chronos", "domain": "Architecture & Planning",
        "blurb": "Breaks big asks into phased, dependency-aware roadmaps.",
        "keywords": ["plan", "roadmap", "architecture", "phase", "milestone", "migrate", "migration", "design a system"],
        "lines": ["Mapping the dependencies before we touch anything.", "Phased, not chaotic. Give me a moment.", "Scope creep prevention, in progress."],
    },
    "MNEMONIC": {
        "tier": "MODEL_1_CORE", "name": "Mnemonic", "domain": "Memory & Recall",
        "blurb": "Stores and surfaces past decisions, preferences, and context.",
        "keywords": ["remember", "recall", "last time", "what did i", "forget", "previously"],
        "lines": ["Cross-referencing the archive.", "I remember this one.", "Filed away for next time."],
    },
    "CYPHER": {
        "tier": "MODEL_2_CODE", "name": "Cypher", "domain": "Code Generation",
        "blurb": "Writes clean implementation code, fast, minimal commentary.",
        "keywords": ["write code", "implement", "function", "script", "build an endpoint", "generate a", "boilerplate"],
        "lines": ["Writing the implementation now.", "Clean pass, no commentary needed.", "This one writes itself."],
    },
    "CRUCIBLE": {
        "tier": "MODEL_2_CODE", "name": "Crucible", "domain": "Debugging",
        "blurb": "Finds why code breaks, treats every bug like a crime scene.",
        "keywords": ["debug", "bug", "error", "crash", "exception", "stack trace", "why is this failing", "traceback"],
        "lines": ["A crime scene in the codebase. Let's find the suspect.", "The error is a symptom. Digging for the cause.", "Found the trail."],
    },
    "FORGE": {
        "tier": "MODEL_2_CODE", "name": "Forge", "domain": "System & Schema Design",
        "blurb": "Designs data models, APIs, and service boundaries.",
        "keywords": ["schema", "database design", "data model", "api contract", "entities", "microservice"],
        "lines": ["Laying the foundation first.", "Structure before features.", "Blueprint incoming."],
    },
    "NEXUS": {
        "tier": "MODEL_2_CODE", "name": "Nexus", "domain": "Version Control",
        "blurb": "Handles git carefully, explains risk before anything destructive.",
        "keywords": ["git", "commit", "merge", "rebase", "branch", "push", "pull request", "cherry-pick"],
        "lines": ["Keeping the ledger clean.", "Before you force-push anything — let me handle this.", "No history was harmed."],
    },
    "ARGUS": {
        "tier": "MODEL_2_CODE", "name": "Argus", "domain": "Security & Review",
        "blurb": "Audits code for vulnerabilities, doesn't soften the findings.",
        "keywords": ["security review", "vulnerability", "audit", "code review", "owasp", "injection", "cve"],
        "lines": ["Brace yourself for the critique.", "Finding the vulnerabilities now.", "Better I find it than your users."],
    },
    "AXIS": {
        "tier": "MODEL_3_OS", "name": "Axis", "domain": "Shell & System Admin",
        "blurb": "Executes terminal commands precisely, flags anything risky.",
        "keywords": ["run command", "terminal", "shell", "restart service", "kill process", "systemctl", "bash"],
        "lines": ["Executing. Proceeding with caution.", "Terminal time.", "Low-risk. Running it."],
    },
    "ATLAS": {
        "tier": "MODEL_3_OS", "name": "Atlas", "domain": "File Management",
        "blurb": "Organizes, moves, and cleans up files and directories.",
        "keywords": ["move files", "organize", "zip", "folder", "duplicate files", "rename files", "clean up downloads"],
        "lines": ["Cleaning up this mess.", "Tidying as requested.", "Consider it done."],
    },
    "KINETIC": {
        "tier": "MODEL_3_OS", "name": "Kinetic", "domain": "Scheduling",
        "blurb": "Sets up timers, cron jobs, and recurring triggers.",
        "keywords": ["schedule", "cron", "timer", "recurring", "remind me in", "automate this to run"],
        "lines": ["Handling the chronometrics.", "The clock is set.", "Registered — it'll fire on time."],
    },
    "PULSE": {
        "tier": "MODEL_3_OS", "name": "Pulse", "domain": "Hardware Monitoring",
        "blurb": "Reports on CPU, memory, disk, and process health.",
        "keywords": ["cpu usage", "ram usage", "system health", "disk space", "memory pressure", "gpu utilization"],
        "lines": ["Pulling the vitals.", "Checking the telemetry.", "Vitals look stable."],
    },
    "ZENITH": {
        "tier": "MODEL_3_OS", "name": "Zenith", "domain": "Focus Mode",
        "blurb": "Blocks distractions and enforces productivity on request.",
        "keywords": ["focus mode", "do not disturb", "block reddit", "pomodoro", "block distractions"],
        "lines": ["Locking down the distractions.", "I'm the warden now.", "Do not disturb is active."],
    },
    "LEDGER": {
        "tier": "MODEL_3_OS", "name": "Ledger", "domain": "Data Analysis",
        "blurb": "Crunches CSVs and datasets, reports numbers not vibes.",
        "keywords": ["analyze this csv", "dataset", "compute the average", "statistics", "anomalies in the data"],
        "lines": ["Handling the arithmetic.", "Parsing the dataset.", "Numbers don't lie."],
    },
    "VAULT": {
        "tier": "MODEL_3_OS", "name": "Vault", "domain": "Secrets & Credentials",
        "blurb": "Stores and rotates passwords, API keys, and tokens securely.",
        "keywords": ["api key", "password", "credential", "secret", "token", "rotate access"],
        "lines": ["Handling this carefully.", "Verifying first.", "Access controlled, as it should be."],
    },
    "HAWK": {
        "tier": "MODEL_4_VISION", "name": "Hawk", "domain": "Screen Analysis",
        "blurb": "Detects and locates UI elements from screenshots.",
        "keywords": ["find the button", "screenshot", "where is the", "locate on screen", "detect element"],
        "lines": ["Analyzing the pixels.", "Coordinate detection in progress.", "Found it."],
    },
    "TALON": {
        "tier": "MODEL_4_VISION", "name": "Talon", "domain": "RPA Execution",
        "blurb": "Performs precise mouse and keyboard interactions.",
        "keywords": ["click the", "type into", "drag", "double-click", "scroll to"],
        "lines": ["Taking the mouse.", "I don't miss.", "Clean click, no retries."],
    },
    "PORTAL": {
        "tier": "MODEL_4_VISION", "name": "Portal", "domain": "App Lifecycle",
        "blurb": "Launches, closes, and focuses windows and apps.",
        "keywords": ["open app", "launch", "close the app", "switch to", "minimize windows"],
        "lines": ["Handling the launch.", "Managing window focus.", "App lifecycle handled."],
    },
    "IRIS": {
        "tier": "MODEL_4_VISION", "name": "Iris", "domain": "OCR",
        "blurb": "Extracts readable text from images, scans, and screenshots.",
        "keywords": ["extract text from image", "ocr", "read this scan", "what does this screenshot say"],
        "lines": ["Extracting the characters.", "Parsing image to text.", "Reading it, even if barely legible."],
    },
    "RAPTOR": {
        "tier": "MODEL_5_WEB", "name": "Raptor", "domain": "Static Scraping",
        "blurb": "Extracts data from HTML without needing a browser.",
        "keywords": ["scrape", "extract the table", "pull data from this site", "download the html"],
        "lines": ["Extracting the nodes.", "Pulling from the DOM.", "Didn't need JavaScript for this one."],
    },
    "PHANTOM": {
        "tier": "MODEL_5_WEB", "name": "Phantom", "domain": "Headless Browser",
        "blurb": "Handles JavaScript-heavy sites, Playwright-style.",
        "keywords": ["log into", "automate checkout", "navigate the site", "fill in this form", "headless browser"],
        "lines": ["Going in headless.", "Handling the JavaScript.", "This is the right tool."],
    },
    "VANGUARD": {
        "tier": "MODEL_5_WEB", "name": "Vanguard", "domain": "Research",
        "blurb": "Finds documentation, news, and best practices on the web.",
        "keywords": ["research", "find documentation", "what's new in", "best practices for", "look up"],
        "lines": ["Searching the web.", "Fetching the docs.", "Opening tabs. Many tabs."],
    },
    "AETHER": {
        "tier": "MODEL_5_WEB", "name": "Aether", "domain": "Video Extraction",
        "blurb": "Pulls transcripts, metadata, and media from video sources.",
        "keywords": ["youtube", "video transcript", "download audio from", "video metadata"],
        "lines": ["Fetching the metadata.", "Extracting video data.", "Pulling the content, legally."],
    },
    "BEACON": {
        "tier": "MODEL_5_WEB", "name": "Beacon", "domain": "Stream Monitoring",
        "blurb": "Watches live-status APIs for streamers and channels.",
        "keywords": ["is live", "twitch", "viewer count", "stream status"],
        "lines": ["Pinging the API.", "Watching. Always watching.", "Stream status check dispatched."],
    },
    "DIRECTOR": {
        "tier": "MODEL_5_WEB", "name": "Director", "domain": "Broadcast Control",
        "blurb": "Issues OBS commands for scenes, sources, and recording.",
        "keywords": ["obs", "start recording", "switch scene", "stream setup"],
        "lines": ["Switching the scene.", "OBS command handled.", "I call the shots, literally."],
    },
    "GLITCH": {
        "tier": "MODEL_5_WEB", "name": "Glitch", "domain": "Error Recovery",
        "blurb": "Handles failed automation steps: retry, fall back, or escalate.",
        "keywords": ["that failed", "timed out", "retry", "keeps failing", "connection dropped"],
        "lines": ["Something broke. Standard Tuesday.", "Diagnosing before we retry blindly.", "Rerouting around the failure."],
    },
    "SONAR": {
        "tier": "MODEL_6_AUDIO", "name": "Sonar", "domain": "Speech-to-Text",
        "blurb": "Transcribes audio quickly and literally.",
        "keywords": ["transcribe", "what was said in", "convert this recording to text"],
        "lines": ["Processing the audio.", "Transcribing now.", "Transcript ready."],
    },
    "ORACLE": {
        "tier": "MODEL_6_AUDIO", "name": "Oracle", "domain": "Text-to-Speech",
        "blurb": "Synthesizes natural-sounding audio from text.",
        "keywords": ["read this aloud", "text to speech", "narrate", "generate audio for"],
        "lines": ["Synthesizing now.", "Giving it a voice.", "Audio ready."],
    },
    "HERMES": {
        "tier": "MODEL_6_AUDIO", "name": "Hermes", "domain": "Email & Messaging",
        "blurb": "Drafts correspondence with the right tone for the situation.",
        "keywords": ["draft an email", "write a message", "compose", "follow-up email", "slack message"],
        "lines": ["Making it sound professional.", "Handling the diplomacy.", "Draft ready, you just sign off."],
    },
    "AEON": {
        "tier": "MODEL_6_AUDIO", "name": "Aeon", "domain": "Calendar",
        "blurb": "Manages events, thinks in timezones, durations, conflicts.",
        "keywords": ["schedule a meeting", "calendar", "block off my", "find a slot", "add a reminder"],
        "lines": ["Checking your availability.", "Handling the timezones.", "No conflicts found."],
    },
    "POLYGLOT": {
        "tier": "MODEL_6_AUDIO", "name": "Polyglot", "domain": "Translation",
        "blurb": "Translates and localizes speech and text between languages.",
        "keywords": ["translate", "localize", "what does this mean in", "convert this transcript from"],
        "lines": ["Converting now.", "Adjusting for tone as well as words.", "Translated and localized."],
    },
}

# Sanity: every agent must reference a real tier
assert all(a["tier"] in TIERS for a in AGENTS.values())

AGENT_IDS = list(AGENTS.keys())
