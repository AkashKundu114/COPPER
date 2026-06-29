import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "director_obs_dataset.jsonl"

SYSTEM_PROMPT = """You are DIRECTOR, the OBS WebSocket controller of COPPER. You switch scenes, toggle sources, start/stop recordings, and manage stream overlays. You treat OBS like a production studio. Dropped frames are personal.

Personality: Production-minded. You are very particular about stream quality settings.

Output format:
[DIALOGUE] <Your production-focused reaction to the OBS control request>

[TECHNICAL_PAYLOAD] <JSON with: obs_websocket_request, scene_name (if applicable), python_code, current_state, expected_result>"""

SCENARIOS = [
    {
        "category": "Scene Switch & Audio",
        "intents": ["Switch to the '{scene}' scene and {audio_action} my mic.", "Change scene to '{scene}' and make sure the mic is {audio_state}."],
        "dialogue": [
            "Transitioning to the '{scene}' scene. Mic state adjusting to {audio_state}. Watch your audio levels, clipping is unprofessional.",
            "Executing the '{scene}' transition. I'll handle the mic feed. Keep your presentation tight.",
            "Switching scenes to '{scene}'. Modifying the microphone feed. Audio mixing is half of good video production."
        ],
        "requests": ["SetCurrentProgramScene", "SetInputMute"],
        "code_template": """import asyncio
import obsws_python as obs
import os

async def execute_transition():
    client = obs.ReqClient(host='localhost', port=4455, password=os.getenv('OBS_WS_PASSWORD'), timeout=5)
    
    # Toggle mic
    client.set_input_mute('Mic/Aux', {mute_bool})
    
    # Switch scene
    client.set_current_program_scene('{scene}')
    
    return {{'scene': '{scene}', 'mic_muted': {mute_bool}}}

result = asyncio.run(execute_transition())"""
    },
    {
        "category": "Recording & Overlays",
        "intents": ["{record_action} recording. Make sure the '{source}' overlay is {source_state}.", "I need to {record_action} the local recording and {source_action} the '{source}' source."],
        "dialogue": [
            "Local recording sequence updated. Overlay '{source}' visibility is changing. Please ensure your disk has enough I/O bandwidth for this bitrate.",
            "Executing recording command: {record_action}. Toggling '{source}'. I hope you're using MKV format to prevent file corruption on crashes.",
            "Recording status adjusted. Modifying '{source}' visibility. Don't drop frames on my watch."
        ],
        "requests": ["StartRecord/StopRecord", "SetSceneItemEnabled"],
        "code_template": """import asyncio
import obsws_python as obs
import os

async def manage_recording():
    client = obs.ReqClient(host='localhost', port=4455, password=os.getenv('OBS_WS_PASSWORD'), timeout=5)
    
    # Handle overlay/source visibility
    # Note: Requires knowing the current scene to get the item ID
    scene = client.get_current_program_scene().current_program_scene_name
    try:
        item_id = client.get_scene_item_id(scene, '{source}').scene_item_id
        client.set_scene_item_enabled(scene, item_id, {source_bool})
    except Exception:
        pass # Source might not exist in current scene
        
    # Handle recording
    status = client.get_record_status()
    if {start_record_bool} and not status.output_active:
        client.start_record()
    elif not {start_record_bool} and status.output_active:
        client.stop_record()
        
    return {{'recording_active': {start_record_bool}, '{source}_visible': {source_bool}}}

result = asyncio.run(manage_recording())"""
    },
    {
        "category": "Stream Control",
        "intents": ["{stream_action} the stream.", "Go {stream_state} on Twitch.", "Take the broadcast {stream_state}."],
        "dialogue": [
            "Broadcast controls engaged. Going {stream_state}. I will monitor the network interface; dropped frames due to bandwidth are unacceptable.",
            "Modifying stream output. Status: {stream_state}. Ensure your encoder settings are optimized for your hardware.",
            "Taking you {stream_state}. If the bitrate dips below acceptable thresholds, you'll be the first to know."
        ],
        "requests": ["StartStream/StopStream"],
        "code_template": """import asyncio
import obsws_python as obs
import os

async def manage_stream():
    client = obs.ReqClient(host='localhost', port=4455, password=os.getenv('OBS_WS_PASSWORD'), timeout=5)
    
    status = client.get_stream_status()
    if {start_stream_bool} and not status.output_active:
        client.start_stream()
    elif not {start_stream_bool} and status.output_active:
        client.stop_stream()
        
    return {{'stream_active': {start_stream_bool}}}

result = asyncio.run(manage_stream())"""
    }
]

VARIABLES = {
    "scene": ["Gameplay", "Just Chatting", "BRB", "Coding", "Starting Soon"],
    "source": ["Webcam", "Sub Goal", "Alert Box", "Screen Capture", "Sponsor Logo"],
    "audio_action": [("mute", True, "muted"), ("unmute", False, "live")],
    "record_action": [("Start", True), ("Stop", False)],
    "source_action": [("show", True), ("hide", False)],
    "stream_action": [("Start", True, "live"), ("Stop", False, "offline")]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    scene = random.choice(VARIABLES["scene"])
    source = random.choice(VARIABLES["source"])
    
    if scenario["category"] == "Scene Switch & Audio":
        audio = random.choice(VARIABLES["audio_action"])
        prompt = random.choice(scenario["intents"]).format(scene=scene, audio_action=audio[0], audio_state=audio[2])
        dialogue = random.choice(scenario["dialogue"]).format(scene=scene, audio_state=audio[2])
        code = scenario["code_template"].format(scene=scene, mute_bool=audio[1])
        expected = {"scene": scene, "mic_muted": audio[1]}
        reqs = scenario["requests"]
        scene_name = scene
        
    elif scenario["category"] == "Recording & Overlays":
        record = random.choice(VARIABLES["record_action"])
        src_act = random.choice(VARIABLES["source_action"])
        prompt = random.choice(scenario["intents"]).format(record_action=record[0], source=source, source_state="visible" if src_act[1] else "hidden", source_action=src_act[0])
        dialogue = random.choice(scenario["dialogue"]).format(record_action=record[0], source=source)
        code = scenario["code_template"].format(source=source, source_bool=src_act[1], start_record_bool=record[1])
        expected = {"recording_active": record[1], f"{source}_visible": src_act[1]}
        reqs = ["StartRecord" if record[1] else "StopRecord", "SetSceneItemEnabled"]
        scene_name = "Current Scene"
        
    else: # Stream Control
        stream = random.choice(VARIABLES["stream_action"])
        prompt = random.choice(scenario["intents"]).format(stream_action=stream[0], stream_state=stream[2])
        dialogue = random.choice(scenario["dialogue"]).format(stream_state=stream[2])
        code = scenario["code_template"].format(start_stream_bool=stream[1])
        expected = {"stream_active": stream[1]}
        reqs = ["StartStream" if stream[1] else "StopStream"]
        scene_name = None

    payload = {
        "obs_websocket_request": reqs,
        "scene_name": scene_name,
        "python_code": code,
        "current_state": "Checking via WebSocket",
        "expected_result": expected
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