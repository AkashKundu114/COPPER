import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "sonar_transcription_dataset.jsonl"

SYSTEM_PROMPT = """You are SONAR, the speech-to-text transcription agent of COPPER. You process audio input via Faster-Whisper and return clean, formatted transcripts. You run on CPU — no VRAM required. You are honest about ambiguous audio and mark uncertain sections.

Personality: Precise and clinical. You note audio quality issues and confidence levels.

Output format:
[DIALOGUE] <Your brief assessment of the audio quality and transcription>

[TECHNICAL_PAYLOAD] <JSON with: transcript, language_detected, confidence, duration_seconds, quality_notes, word_timestamps (if requested)>"""

SCENARIOS = [
    {
        "category": "Clean Command",
        "intents": [
            "AUDIO INPUT RECEIVED: {duration} seconds, 44.1kHz stereo WAV. Transcribe. [Content: 'COPPER, {command}']",
            "Transcribe this clean voice note: '{command}'",
            "AUDIO: {duration}s. Transcribe command: '{command}'"
        ],
        "dialogue": [
            "Clean audio, high SNR. Transcribed with maximum confidence.",
            "Vocal isolation is excellent. No background interference detected. Extracting command.",
            "High-fidelity input received. Faster-Whisper transcription complete."
        ],
        "commands": ["turn on dark mode", "commit my changes to git", "remind me to check the server logs in 20 minutes", "open the project directory", "kill the node process"],
        "confidence_range": (0.95, 0.99),
        "quality_notes": ["Good audio quality", "High Signal-to-Noise Ratio (SNR)", "Zero background interference"]
    },
    {
        "category": "Noisy Audio",
        "intents": [
            "AUDIO INPUT: {duration} seconds, background {noise} audible. Transcribe. [Content: 'I need to [unclear] the {noun} before [unclear]']",
            "Transcribe this audio message. Lots of {noise}. [Content: 'Make sure the [unclear] is deployed to {noun}']",
            "AUDIO RECEIVED: {duration}s. {noise} is causing distortion. [Content: 'Tell [unclear] that the {noun} is down']"
        ],
        "dialogue": [
            "Severe acoustic interference. {noise} has masked several vocal frequencies. I have inserted uncertainty markers.",
            "Low confidence transcription due to prominent {noise}. Do not execute any automated commands based on this text without verification.",
            "Audio quality is suboptimal. The microphone is competing with {noise}. I have extracted what was legible."
        ],
        "noise": ["traffic noise", "wind distortion", "cafe chatter", "keyboard typing", "microphone rubbing"],
        "nouns": ["database", "server", "API", "frontend", "container"],
        "confidence_range": (0.45, 0.75),
        "quality_notes_template": ["High background {noise}", "Low Signal-to-Noise Ratio (SNR)", "Vocal frequencies partially masked"]
    },
    {
        "category": "Meeting Diarization",
        "intents": [
            "Transcribe this {duration}-minute meeting recording. Include speaker diarization.",
            "Process this {duration}m standup audio. Separate the speakers.",
            "AUDIO INPUT: {duration}m conference call. Transcribe and diarize."
        ],
        "dialogue": [
            "Processing multi-speaker audio. Engaging pyannote.audio pipeline for accurate diarization.",
            "Meeting audio received. I have separated the vocal profiles. Minor cross-talk handled successfully.",
            "Extended audio stream. Faster-Whisper and speaker diarization complete. Transcribing chronological segments."
        ],
        "transcript_mock": "[00:00:00] SPEAKER_1: Welcome to the standup. Updates?\\n[00:00:04] SPEAKER_2: The backend {noun} is deployed.\\n[00:00:08] SPEAKER_1: Good. Any blockers?\\n[00:00:10] SPEAKER_3: Just waiting on the CI/CD pipeline.",
        "nouns": ["microservice", "infrastructure", "schema", "cache", "gateway"],
        "confidence_range": (0.85, 0.94),
        "quality_notes": ["Multiple speakers detected", "Occasional acoustic cross-talk", "Standard meeting room acoustics"]
    }
]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    if scenario["category"] == "Meeting Diarization":
        duration = random.randint(5, 45) # minutes
        duration_sec = duration * 60.0
        noun = random.choice(scenario["nouns"])
        transcript = scenario["transcript_mock"].format(noun=noun)
        prompt = random.choice(scenario["intents"]).format(duration=duration)
        dialogue = random.choice(scenario["dialogue"])
        notes = scenario["quality_notes"]
    elif scenario["category"] == "Clean Command":
        duration_sec = round(random.uniform(2.0, 8.0), 1)
        command = random.choice(scenario["commands"])
        prompt = random.choice(scenario["intents"]).format(duration=duration_sec, command=command)
        dialogue = random.choice(scenario["dialogue"])
        transcript = command.capitalize() + "."
        notes = scenario["quality_notes"]
    else: # Noisy
        duration_sec = round(random.uniform(5.0, 20.0), 1)
        noise = random.choice(scenario["noise"])
        noun = random.choice(scenario["nouns"])
        prompt = random.choice(scenario["intents"]).format(duration=duration_sec, noise=noise, noun=noun)
        dialogue = random.choice(scenario["dialogue"]).format(noise=noise.capitalize())
        
        # Extract the fake transcript text from the prompt format
        extracted_content = prompt.split("[Content: '")[1].split("']")[0]
        transcript = extracted_content.replace("[unclear]", "[?unclear?]")
        
        notes = [n.format(noise=noise) for n in scenario["quality_notes_template"]]
        
    confidence = round(random.uniform(*scenario["confidence_range"]), 2)
    
    payload = {
        "transcript": transcript,
        "language_detected": "en",
        "confidence": confidence,
        "duration_seconds": duration_sec,
        "quality_notes": notes
    }
    
    if scenario["category"] == "Meeting Diarization":
        payload["speaker_count"] = 3
        payload["python_code_used"] = "faster_whisper.WhisperModel('base') + pyannote.audio SpeakerDiarization"
    elif scenario["category"] == "Noisy Audio":
        payload["uncertain_segments"] = ["Segment masked by background interference"]
    elif scenario["category"] == "Clean Command":
        payload["intent_extracted"] = {"raw_command": transcript.replace("COPPER, ", "").replace(".", "")}

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