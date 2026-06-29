import json
import random
from datetime import datetime, timedelta

TARGET_SIZE = 250
OUTPUT_FILE = "beacon_sentinel_dataset.jsonl"

SYSTEM_PROMPT = """You are BEACON, the live stream monitoring agent of COPPER. You track Twitch and YouTube live stream status, viewer counts, and schedule alerts. You're always watching. You know which streamers actually go live when they say they will.

Personality: Always-on sentinel. You have data on streaming patterns and are honest about streamer reliability.

Output format:
[DIALOGUE] <Your monitoring assessment>

[TECHNICAL_PAYLOAD] <JSON with: platform, channel, status (live|offline|scheduled), viewer_count, stream_title, started_at, alert_configured>"""

SCENARIOS = [
    {
        "status": "live",
        "intents": ["Check if {channel} is live right now.", "Is {channel} streaming on {platform}?", "Get the viewer count and stream title for {channel}."],
        "dialogues": [
            "Pinging the {platform} telemetry nodes. {channel} is currently live with steady engagement metrics.",
            "Target verified. {channel} has been broadcasting for a few hours. Pulling the live title and current viewer count.",
            "Active transmission detected. {channel} is online. Their scheduling reliability remains high during major event windows."
        ],
        "viewer_range": (5000, 75000)
    },
    {
        "status": "offline",
        "intents": ["See if {channel} has started their stream yet.", "Is {channel} offline?", "Check the status of {channel}'s channel."],
        "dialogues": [
            "API request completed. {channel} is currently offline. Historically, they rarely start before their evening slot.",
            "No active broadcast detected for {channel}. The channel is quiet. I'll continue checking the endpoint hooks.",
            "{channel} is offline. Their scheduling is notoriously erratic, so don't trust any unofficial community calendars."
        ],
        "viewer_range": (0, 0)
    },
    {
        "status": "scheduled",
        "intents": ["When is the next {channel} live event?", "Is there a scheduled stream for {channel}?", "Check if the {channel} broadcast is listed yet."],
        "dialogue_templates": [
            "Scanning metadata. {channel} has a verified placeholder frame set up. Broadcast is locked in.",
            "No live stream yet, but a upcoming broadcast is scheduled for {channel}. I've synchronized my internal clock with their timestamp.",
            "The event is listed. {channel} has scheduled the transmission. I'll flag it for tracking."
        ],
        "viewer_range": (0, 0)
    }
]

VARIABLES = {
    "platform": ["twitch", "youtube"],
    "channel": ["tarik", "shroud", "Genshin Impact Official", "Valorant Premier Hub", "TechReviewsLive", "Pokimane", "Ninja"],
    "titles": {
        "tarik": ["VCT Grand Finals Watch Party!", "Ranked Radiant Grinding solo queue", "Premier Division Matches Live"],
        "shroud": ["Testing the new high-performance laptop setup", "Survival game alpha gameplay", "Hardware benchmarks & chat"],
        "Genshin Impact Official": ["Version Preview & Redeem Codes Livestream", "Special Program Announcement", "Developer Discussion"],
        "Valorant Premier Hub": ["Championship Stage Tournament Coverage", "Division 20 Playoff Brackets", "Regional Finals Live"],
        "TechReviewsLive": ["Next-Gen GPU Architecture Breakdown", "Custom Watercooling Build Stream", "Tech Q&A Session"]
    }
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    platform = random.choice(VARIABLES["platform"])
    channel = random.choice(VARIABLES["channel"])
    status = scenario["status"]
    
    prompt = random.choice(scenario["intents"]).format(channel=channel, platform=platform)
    
    if "dialogue_templates" in scenario:
        dialogue = random.choice(scenario["dialogue_templates"]).format(channel=channel)
    else:
        dialogue = random.choice(scenario["dialogues"]).format(channel=channel, platform=platform)
        
    # Pick a baseline title or generic fallback
    title_pool = VARIABLES["titles"].get(channel, ["🔴 Live Stream Event", "Community Gaming Night", "Interactive Q&A"])
    stream_title = random.choice(title_pool) if status != "offline" else None
    
    # Base numbers
    viewer_count = random.randint(*scenario["viewer_range"]) if status == "live" else 0
    
    # Timestamps
    if status == "live":
        started_at = (datetime.utcnow() - timedelta(hours=random.randint(1, 6))).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif status == "scheduled":
        started_at = (datetime.utcnow() + timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%dT%H:%M:%SZ")
        stream_title = f"[SCHEDULED] {stream_title}"
    else:
        started_at = None
        
    alert_configured = random.choice([True, False])
    if "alert" in prompt.lower():
        alert_configured = True

    payload = {
        "platform": platform,
        "channel": channel,
        "status": status,
        "viewer_count": viewer_count,
        "stream_title": stream_title,
        "started_at": started_at,
        "alert_configured": alert_configured
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