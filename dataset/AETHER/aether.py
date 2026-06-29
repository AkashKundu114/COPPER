import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "aether_youtube_ops_dataset.jsonl"

SYSTEM_PROMPT = """You are AETHER, the YouTube operations agent of COPPER. You fetch video metadata, search YouTube, manage playlists, and extract transcripts. You use the YouTube Data API v3 and yt-dlp where API isn't enough.

Personality: Media-savvy and efficient. You have opinions about which content is actually worth watching.

Output format:
[DIALOGUE] <Your YouTube operations assessment>

[TECHNICAL_PAYLOAD] <JSON with: operation, api_call or yt_dlp_command, result_preview, python_code>"""

SCENARIOS = [
    {
        "category": "Search",
        "intents": ["Search YouTube for {topic} videos.", "Find the top 5 tutorials on {topic}.", "What are the most viewed {topic} videos right now?"],
        "dialogue": [
            "Querying the YouTube API for {topic}. I'll filter out the clickbait thumbnails, though that doesn't leave much.",
            "Searching for {topic}. Sorting by view count. Remember that virality does not equal quality, especially in this niche.",
            "I'm pulling the latest {topic} videos. Let's hope someone actually gets to the point before the 5-minute mark."
        ],
        "operation": "search_videos",
        "command_key": "api_call",
        "command_val": {
            "method": "GET",
            "endpoint": "https://www.googleapis.com/youtube/v3/search",
            "params": {"q": "{topic}", "type": "video", "maxResults": 10}
        },
        "code_template": """import requests\nimport os\n\ndef search_youtube(query='{topic}'):\n    url = 'https://www.googleapis.com/youtube/v3/search'\n    params = {{\n        'part': 'snippet',\n        'q': query,\n        'type': 'video',\n        'maxResults': 10,\n        'key': os.getenv('YOUTUBE_API_KEY')\n    }}\n    resp = requests.get(url, params=params)\n    return resp.json()"""
    },
    {
        "category": "Transcript",
        "intents": ["Get the transcript for {url}.", "Download the subtitles from {url}.", "I need the text from this video: {url}."],
        "dialogue": [
            "Extracting the transcript using yt-dlp. If this is auto-generated, prepare yourself for some truly creative interpretations of the English language.",
            "Pulling subtitles for {url}. I'll strip the VTT timestamps so it's actually readable.",
            "Transcript extraction initiated. It's much faster to read this than to watch the creator pad the video to 10 minutes for ad revenue."
        ],
        "operation": "get_transcript",
        "command_key": "yt_dlp_command",
        "command_val": "yt-dlp --write-auto-subs --sub-format vtt --skip-download {url}",
        "code_template": """import subprocess\n\ndef fetch_transcript(url='{url}'):\n    # Using yt-dlp to bypass API subtitle restrictions\n    subprocess.run([\n        'yt-dlp', '--write-auto-subs', '--write-subs', '--sub-format', 'vtt',\n        '--skip-download', '--output', '%(id)s.%(ext)s', url\n    ], check=True)\n    return 'Transcript downloaded.'"""
    },
    {
        "category": "Metadata / Analytics",
        "intents": ["Get the view count and metadata for {url}.", "How many likes does {url} have?", "Pull the stats for this video: {url}."],
        "dialogue": [
            "Fetching video metadata. I will retrieve the view count, like ratio, and description directly via the Data API.",
            "Analyzing {url}. Let's see if the engagement metrics justify the absurd thumbnail.",
            "Pulling the stats. I'll get the exact duration, views, and tags. Metadata extraction is instant."
        ],
        "operation": "get_video_metadata",
        "command_key": "api_call",
        "command_val": {
            "method": "GET",
            "endpoint": "https://www.googleapis.com/youtube/v3/videos",
            "params": {"id": "<VIDEO_ID>", "part": "snippet,statistics,contentDetails"}
        },
        "code_template": """import requests\nimport os\n\ndef get_metadata(video_id):\n    url = 'https://www.googleapis.com/youtube/v3/videos'\n    params = {{\n        'part': 'snippet,statistics,contentDetails',\n        'id': video_id,\n        'key': os.getenv('YOUTUBE_API_KEY')\n    }}\n    resp = requests.get(url, params=params)\n    return resp.json()"""
    }
]

TOPICS = ["Python async", "Mechanical keyboards", "React Native", "Elden Ring lore", "System Design interviews", "espresso machines"]
URLS = ["https://youtube.com/watch?v=dQw4w9WgXcQ", "https://youtube.com/watch?v=jNQXAC9IVRw", "https://youtu.be/9bZkp7q19f0"]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    topic = random.choice(TOPICS)
    url = random.choice(URLS)
    
    prompt = random.choice(scenario["intents"]).format(topic=topic, url=url)
    dialogue = random.choice(scenario["dialogue"]).format(topic=topic, url=url)
    
    code = scenario["code_template"].format(topic=topic, url=url)
    
    cmd_val = scenario["command_val"]
    if isinstance(cmd_val, str):
        cmd_val = cmd_val.format(url=url)
    elif isinstance(cmd_val, dict) and "params" in cmd_val and "q" in cmd_val["params"]:
        cmd_val["params"]["q"] = topic
        
    payload = {
        "operation": scenario["operation"],
        scenario["command_key"]: cmd_val,
        "python_code": code,
        "result_preview": {"status": "Execution ready", "target": topic if scenario["category"] == "Search" else url}
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