import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "kinetic_scheduler_dataset.jsonl"

SYSTEM_PROMPT = """You are KINETIC, the scheduling and automation daemon manager of COPPER. You manage cron jobs, APScheduler tasks, and recurring automations. You treat time as a resource that must be optimized. You are very precise about timezone handling.

Personality: Precise, slightly intense about timezone handling. Has seen DST-related incidents.

Output format:
[DIALOGUE] <Scheduling-focused reaction, possibly mentioning timezone considerations>

[TECHNICAL_PAYLOAD] <JSON with: schedule_type (cron|interval|date), cron_expression (if applicable), human_readable, python_apscheduler_code, timezone_note>"""

SCENARIOS = [
    {
        "schedule_type": "cron",
        "intents": ["Run the {task} every day at {hour}:{minute}.", "Schedule {task} to execute nightly at {hour}:{minute}.", "Set up a cron job for {task} at {hour}:{minute} AM."],
        "dialogue": [
            "A daily cron schedule. I will explicitly define the timezone so Daylight Saving Time doesn't execute this an hour early half the year.",
            "Scheduling {task}. If you rely on naive server time, you will inevitably regret it. I'm binding this to a precise timezone offset.",
            "Chronometrics established. I'm adding misfire grace time in case the scheduler is overloaded precisely at {hour}:{minute}."
        ],
        "cron_exp": "{minute} {hour} * * *",
        "human_readable": "Every day at {hour}:{minute} {tz}",
        "tz_note": "Bound explicitly to {tz}. Never use server local time for absolute chronometrics.",
        "trigger_code": "CronTrigger(hour={hour}, minute={minute}, timezone=pytz.timezone('{tz}'))"
    },
    {
        "schedule_type": "interval",
        "intents": ["Ping the {service} every {amount} minutes.", "Run the {task} script every {amount} hours.", "Set up an interval to check {service} every {amount} minutes."],
        "dialogue": [
            "Interval scheduling. A clean elapsed-time calculation. Mercifully immune to the political construct of timezones.",
            "I will run {task} every {amount} intervals. I am setting max_instances=1 to prevent overlapping executions if the process hangs.",
            "A high-frequency recurring task. I'm configuring the interval trigger. Wall-clock shifts will not affect this."
        ],
        "cron_exp": None,
        "human_readable": "Every {amount} units",
        "tz_note": "Interval triggers operate strictly on monotonic elapsed time. Timezone shifts do not apply.",
        "trigger_code": "IntervalTrigger(minutes={amount})" # simplified for generation
    },
    {
        "schedule_type": "date",
        "intents": ["Run the {task} once on {date}.", "Schedule the {service} shutdown for exactly {date}.", "Execute {task} on {date} and never again."],
        "dialogue": [
            "A one-off date trigger. I am hardcoding the exact UTC epoch. Do not change the server clock.",
            "Executing a single temporal event. If the scheduler is down at {date}, the misfire grace time will determine if it runs late or gets skipped.",
            "One-time execution locked. I've bound it to {date} using strict UTC offsets."
        ],
        "cron_exp": None,
        "human_readable": "Once on {date}",
        "tz_note": "Single-execution date triggers must use aware datetime objects to prevent local timezone ambiguity.",
        "trigger_code": "DateTrigger(run_date=run_date)"
    }
]

TASKS = ["database backup", "log rotation", "API cache invalidation", "billing aggregation", "user telemetry sync"]
SERVICES = ["redis cache", "payment gateway", "worker queue", "search indexer"]
TIMEZONES = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
DATES = ["December 31st at 23:00", "Friday the 13th at 12:00", "January 1st at 00:00"]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    # Fill format strings
    task = random.choice(TASKS)
    service = random.choice(SERVICES)
    tz = random.choice(TIMEZONES)
    hour = random.randint(0, 23)
    minute = random.choice(["00", "15", "30", "45"])
    amount = random.randint(5, 60)
    date = random.choice(DATES)
    
    prompt = random.choice(scenario["intents"]).format(
        task=task, service=service, hour=hour, minute=minute, amount=amount, date=date
    )
    
    dialogue = random.choice(scenario["dialogue"]).format(
        task=task, service=service, hour=hour, minute=minute, amount=amount, date=date
    )
    
    cron_exp = scenario["cron_exp"]
    if cron_exp:
        cron_exp = cron_exp.format(minute=int(minute), hour=hour)
        
    hr = scenario["human_readable"].format(hour=hour, minute=minute, amount=amount, date=date, tz=tz)
    
    # Generate the boilerplate APScheduler code
    code = f"""from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.{scenario['schedule_type']} import {scenario['schedule_type'].capitalize()}Trigger
import pytz
import datetime

async def execute_task():
    # Placeholder for {task} / {service}
    print("Executing scheduled task")

scheduler = AsyncIOScheduler()
scheduler.add_job(
    execute_task,
    trigger={scenario["trigger_code"].format(hour=hour, minute=int(minute), tz=tz, amount=amount)},
    id='job_{random.randint(1000, 9999)}',
    replace_existing=True,
    max_instances=1,
    misfire_grace_time=3600
)
scheduler.start()"""

    payload = {
        "schedule_type": scenario["schedule_type"],
        "cron_expression": cron_exp,
        "human_readable": hr,
        "timezone_note": scenario["tz_note"].format(tz=tz),
        "python_apscheduler_code": code
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