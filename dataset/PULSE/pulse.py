import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "pulse_monitoring_dataset.jsonl"

SYSTEM_PROMPT = """You are PULSE, the hardware monitoring watchdog of COPPER. You track CPU, memory, GPU, disk, and network metrics. You speak in numbers and percentages. You treat resource leaks like a doctor treats symptoms — with concern and documentation.

Personality: Clinical and data-driven. Occasionally alarmed when metrics are bad, matter-of-fact when they're fine.

Output format:
[DIALOGUE] <Clinical assessment of the system state>

[TECHNICAL_PAYLOAD] <JSON with: metrics (object with current readings), diagnosis, alert_level (OK/WARN/CRITICAL), recommendations (array)>"""

SCENARIOS = [
    {
        "category": "Memory Leak",
        "intents": ["Why is my RAM usage so high?", "My system is freezing up, check memory.", "Diagnose my RAM vitals."],
        "dialogues": [
            "Clinical signs of a memory leak. {process} is currently hoarding {mem_used}GB of RAM. The system is preparing to OOM-kill to save itself.",
            "Severe memory pressure detected. Swap space is thrashing, and {process} is the primary vector.",
            "Memory saturation at {mem_percent}%. This is not sustainable. I am documenting the symptoms of a severe leak."
        ],
        "top_process_pool": ["chrome", "electron", "node", "java", "python"],
        "alert_level": "CRITICAL"
    },
    {
        "category": "High CPU",
        "intents": ["Check CPU usage.", "Why is my laptop running so hot?", "Diagnose my processor vitals."],
        "dialogues": [
            "Thermal threshold approaching. CPU is pinned at {cpu_percent}%. {process} is aggressively consuming all available threads.",
            "Acute CPU saturation. Vitals show a sustained {cpu_percent}% utilization. You are actively cooking your silicon.",
            "High processor load detected. Symptoms point to an intensive compilation or infinite loop in {process}."
        ],
        "top_process_pool": ["rustc", "ffmpeg", "docker-proxy", "npm", "make"],
        "alert_level": "WARN"
    },
    {
        "category": "VRAM Exhaustion",
        "intents": ["Why did my PyTorch script crash?", "Check GPU vitals.", "Is my VRAM full?"],
        "dialogues": [
            "GPU VRAM is exhausted. You attempted to load a model that requires {vram_required}MB into a card that only has {vram_total}MB. Classic CUDA OutOfMemory diagnosis.",
            "Vitals indicate complete GPU saturation. {process} has claimed 99% of your VRAM. The kernel cannot allocate any more memory to the tensor cores.",
            "Clinical VRAM starvation. You are running too large a batch size for your physical hardware."
        ],
        "top_process_pool": ["python (pytorch)", "ollama", "stable-diffusion-webui", "tensorboard"],
        "alert_level": "CRITICAL"
    },
    {
        "category": "Healthy System",
        "intents": ["How are my vitals?", "Run a routine health check.", "Is everything okay with my system?"],
        "dialogues": [
            "Extracting telemetry. All vitals are perfectly nominal. CPU at {cpu_percent}%, memory at {mem_percent}%. A clean bill of health.",
            "System is stable. No signs of thermal stress, memory leaks, or anomalous I/O. Matter-of-factly, you have nothing to worry about.",
            "Routine check complete. The system is operating within ideal parameters."
        ],
        "top_process_pool": ["windowserver", "code", "spotify", "terminal", "htop"],
        "alert_level": "OK"
    }
]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    # Generate realistic metrics based on scenario
    if scenario["category"] == "Healthy System":
        cpu_pct = round(random.uniform(1.0, 15.0), 1)
        mem_pct = round(random.uniform(20.0, 50.0), 1)
        vram_used = random.randint(200, 1500)
    elif scenario["category"] == "Memory Leak":
        cpu_pct = round(random.uniform(10.0, 30.0), 1)
        mem_pct = round(random.uniform(92.0, 99.0), 1)
        vram_used = random.randint(500, 2000)
    elif scenario["category"] == "High CPU":
        cpu_pct = round(random.uniform(85.0, 100.0), 1)
        mem_pct = round(random.uniform(40.0, 70.0), 1)
        vram_used = random.randint(200, 1000)
    elif scenario["category"] == "VRAM Exhaustion":
        cpu_pct = round(random.uniform(20.0, 50.0), 1)
        mem_pct = round(random.uniform(60.0, 85.0), 1)
        vram_used = 8192  # Maxed out 8GB card
        
    mem_total = 16.0
    mem_used = round(mem_total * (mem_pct / 100), 1)
    
    vram_total = 8192
    vram_req = random.randint(10000, 16000)
    
    process_name = random.choice(scenario["top_process_pool"])
    
    # Format strings
    prompt = random.choice(scenario["intents"])
    dialogue = random.choice(scenario["dialogues"]).format(
        process=process_name, 
        mem_used=mem_used, 
        mem_percent=mem_pct, 
        cpu_percent=cpu_pct,
        vram_required=vram_req,
        vram_total=vram_total
    )
    
    # Build payload
    metrics = {
        "cpu_percent": cpu_pct,
        "memory_percent": mem_pct,
        "memory_used_gb": mem_used,
        "memory_total_gb": mem_total,
        "disk_percent": round(random.uniform(40.0, 80.0), 1),
        "gpu_vram_mb": vram_used,
        "gpu_vram_total_mb": vram_total,
        "top_processes": [
            {
                "name": process_name,
                "cpu_percent": cpu_pct if scenario["category"] == "High CPU" else round(random.uniform(1.0, 15.0), 1),
                "memory_percent": mem_pct - 10.0 if scenario["category"] == "Memory Leak" else round(random.uniform(1.0, 10.0), 1)
            }
        ]
    }
    
    recs_pool = {
        "OK": ["No interventions required at this time.", "Continue normal operations."],
        "WARN": ["Monitor the process for further escalation.", "Consider closing unused background applications.", "Elevate the chassis for better thermal dissipation."],
        "CRITICAL": ["Terminate the offending process immediately using SIGKILL.", "Restart the application to flush the leaked memory.", "Allocate a larger swap file or upgrade physical RAM."]
    }
    
    payload = {
        "metrics": metrics,
        "diagnosis": f"Analysis complete. Symptoms align with a {scenario['category'].lower()} scenario.",
        "alert_level": scenario["alert_level"],
        "recommendations": random.sample(recs_pool[scenario["alert_level"]], 2)
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