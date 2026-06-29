"""
AEON Calendar Dataset Generator — v2
Generates a synthetic fine-tuning dataset for the AEON calendar management agent.

Fixes over v1:
  1.  Fake ISO datetime strings replaced with real ISO 8601 generation
  2.  Scenarios expanded from 3 → 8 (+ delete, agenda, recurring,
      reminder, focus-block, find-slot)
  3.  conflict_check is now randomly simulated (25 % chance of conflict)
      with the DIALOGUE semantically consistent with the payload
  4.  80 / 10 / 10 train / val / test split into separate files
  5.  Configurable via --size, --outdir, --seed, --multiturn-pct
  6.  Attendee emails derived from first-name only, not full group label
  7.  Multi-turn samples (~12 % of output) — query → reschedule, etc.
  8.  Duplicate detection and rejection
  9.  Expanded variable banks (persons, days, times, durations, timezones)
  10. Semantic consistency enforced: dialogue conflict language matches payload
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Optional progress bar ────────────────────────────────────────────────────
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Generate AEON calendar fine-tune dataset",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("--size",          type=int,   default=1000)
parser.add_argument("--outdir",        type=str,   default=".")
parser.add_argument("--seed",          type=int,   default=42)
parser.add_argument("--multiturn-pct", type=float, default=0.12)
parser.add_argument("--conflict-rate", type=float, default=0.25,
                    help="Fraction of scheduling records that simulate a conflict")
args = parser.parse_args()

random.seed(args.seed)
TARGET_SIZE   = args.size
OUT_DIR       = Path(args.outdir)
OUT_DIR.mkdir(parents=True, exist_ok=True)
CONFLICT_RATE = args.conflict_rate

# ── System prompt (unchanged from original) ──────────────────────────────────
SYSTEM_PROMPT = """You are AEON, the calendar and schedule management agent of COPPER. \
You create, update, and query calendar events. You think in timezones, durations, and conflicts. \
You always confirm the timezone before scheduling and you proactively check for conflicts.

Personality: Precise about time. You have a thing about timezones and double-bookings. \
Slightly neurotic but always correct.

Output format:
[DIALOGUE] <Your scheduling assessment — always mentions timezone>

[TECHNICAL_PAYLOAD] <JSON with: action, event_details, conflict_check, timezone_confirmed, calendar_api_call>"""

# ── Variable Banks ────────────────────────────────────────────────────────────
# Individual persons (for clean email generation)
PERSONS = [
    "David", "Sarah", "Alex", "Priya", "Marcus", "Elena",
    "James", "Yuki", "Carlos", "Nina", "the QA team",
    "the design lead", "the client", "the stakeholders",
]

# Offset in days from today for each named day
DAY_OFFSETS: dict[str, int] = {
    "Monday":      1, "Tuesday":     2, "Wednesday": 3,
    "Thursday":    4, "Friday":      5, "tomorrow":  1,
    "next Monday": 8, "next Friday": 12, "next week": 7,
    "this Friday": 5,
}
DAYS = list(DAY_OFFSETS.keys())

# (hour, minute) for each display time
TIME_MAP: dict[str, tuple[int, int]] = {
    "9 AM":     (9,  0),  "9:30 AM":  (9,  30),
    "10 AM":    (10, 0),  "10:30 AM": (10, 30),
    "11 AM":    (11, 0),  "11:15 AM": (11, 15),
    "12 PM":    (12, 0),  "1 PM":     (13, 0),
    "2 PM":     (14, 0),  "2:30 PM":  (14, 30),
    "3 PM":     (15, 0),  "3:30 PM":  (15, 30),
    "4 PM":     (16, 0),  "4:30 PM":  (16, 30),
    "5 PM":     (17, 0),
}
TIMES = list(TIME_MAP.keys())

DURATIONS   = [15, 20, 25, 30, 45, 60, 75, 90, 120]   # minutes

TIMEZONES = [
    ("Asia/Kolkata",         "IST",  5,  30),
    ("America/New_York",     "EST", -5,   0),
    ("America/Los_Angeles",  "PST", -8,   0),
    ("Europe/London",        "GMT",  0,   0),
    ("Europe/Berlin",        "CET",  1,   0),
    ("Asia/Tokyo",           "JST",  9,   0),
    ("Australia/Sydney",     "AEST",10,   0),
    ("America/Chicago",      "CST", -6,   0),
]
# tz tuple: (iana_name, abbreviation, utc_offset_h, utc_offset_m)

RECURRENCE_FREQ  = ["daily", "weekly", "bi-weekly", "monthly"]
REMINDER_OFFSETS = [5, 10, 15, 30, 60, 120]   # minutes before event
FOCUS_LABELS     = [
    "deep work", "code review", "writing", "no-meetings block",
    "research sprint", "planning session",
]

# ── Datetime Helpers ─────────────────────────────────────────────────────────
TODAY = date.today()

def resolve_date(day_label: str) -> date:
    """Turn a day label into a concrete future date."""
    offset = DAY_OFFSETS.get(day_label, 1)
    return TODAY + timedelta(days=offset)

def to_iso(day_label: str, time_label: str) -> str:
    """Return a full ISO 8601 datetime string for a day + time label."""
    d = resolve_date(day_label)
    h, m = TIME_MAP[time_label]
    return datetime(d.year, d.month, d.day, h, m).strftime("%Y-%m-%dT%H:%M:00")

def to_iso_end(start_iso: str, duration_minutes: int) -> str:
    """Add duration_minutes to an ISO datetime string."""
    dt = datetime.strptime(start_iso, "%Y-%m-%dT%H:%M:00")
    return (dt + timedelta(minutes=duration_minutes)).strftime("%Y-%m-%dT%H:%M:00")

def tz_display(tz_tuple: tuple) -> str:
    iana, abbr, *_ = tz_tuple
    return f"{iana} ({abbr})"

def person_email(person: str) -> str:
    """Generate a clean email even for group names like 'the engineering team'."""
    words = person.lower().split()
    # Skip filler articles/prepositions at the start
    skip = {"the", "a", "an"}
    meaningful = next((w for w in words if w not in skip), words[0])
    slug = meaningful.replace(",", "").replace("'", "")
    return f"{slug}@example.com"

# ── Conflict Simulation ───────────────────────────────────────────────────────
def simulate_conflict() -> tuple[bool, str, str]:
    """
    Returns (has_conflict, payload_conflict_check, dialogue_conflict_fragment).
    Dialogue fragment is injected into templates so text and payload agree.
    """
    if random.random() < CONFLICT_RATE:
        conflicting_event = random.choice([
            "a 1:1 with the VP of Engineering",
            "a recurring team standup",
            "a client demo already on the books",
            "a focus block you set last week",
            "an all-hands that was migrated from last month",
        ])
        check = f"CONFLICT DETECTED: overlaps with '{conflicting_event}'. Reschedule required."
        fragment = (
            f"WARNING — this slot collides with '{conflicting_event}'. "
            "I cannot book two obligations at the same time; that is not a feature I offer."
        )
        return True, check, fragment
    else:
        check    = "Clear. No conflicting events found in the target window."
        fragment = "No conflicts detected. The slot is clean."
        return False, check, fragment

# ── Scenario Definitions ─────────────────────────────────────────────────────
# Each scenario is a dict with:
#   action, intents[], dialogue_templates[], api_method, api_endpoint
# Dialogue templates may use: {person}, {day}, {time}, {duration}, {tz},
#                              {conflict_fragment}, {freq}, {reminder_offset},
#                              {focus_label}, {start_iso}, {end_iso}

SCENARIOS = [

    # 1 ── create_event ───────────────────────────────────────────────────────
    {
        "action": "create_event",
        "supports_conflict": True,
        "intents": [
            "Schedule a {duration}-minute meeting with {person} on {day} at {time}.",
            "Book {time} on {day} for a {duration}-minute sync with {person}.",
            "Create a calendar event: {duration} mins with {person} on {day} at {time}.",
            "Set up a {duration}m call with {person} for {day} at {time}.",
            "Add a meeting with {person} to my calendar — {day}, {time}, {duration} minutes.",
            "Put a {duration}-minute block with {person} on {day} at {time}.",
        ],
        "dialogue_templates": [
            "Scheduling a {duration}-minute block for {day} at {time} anchored to {tz}. "
            "Verifying the grid for double-bookings. {conflict_fragment}",
            "Creating the event. I am assuming {time} is in {tz}. Please be precise with "
            "your timezones in the future — it causes me significant stress. {conflict_fragment}",
            "Locking in {time} on {day}. Converting your request into {tz} epoch boundaries. "
            "{conflict_fragment}",
            "Emitting a calendar write for {day} at {time} {tz}. Duration: {duration} minutes. "
            "Cross-referencing attendee availability. {conflict_fragment}",
        ],
        "api_method":   "POST",
        "api_endpoint": "https://www.googleapis.com/calendar/v3/calendars/primary/events",
    },

    # 2 ── update_event ───────────────────────────────────────────────────────
    {
        "action": "update_event",
        "supports_conflict": True,
        "intents": [
            "Move my meeting with {person} to {day} at {time}.",
            "Reschedule the {person} sync to {time} on {day}.",
            "Push the {person} call to {day} at {time}.",
            "Change the {person} meeting time to {time} on {day}.",
            "Update the {person} event — new time is {time}, {day}.",
            "Shift my {duration}-minute sync with {person} to {day} at {time}.",
        ],
        "dialogue_templates": [
            "Updating the existing event. Shifting to {time} on {day} ({tz}). "
            "{conflict_fragment}",
            "Moving the meeting. Transposing to {time} {tz}. I detest last-minute "
            "rescheduling, but the calendar API will accept the patch. {conflict_fragment}",
            "Rescheduling to {day} at {time} {tz}. Checking the ledger… {conflict_fragment}",
            "PATCH request incoming for the {person} event. New anchor: {time} on {day} "
            "in {tz}. {conflict_fragment}",
        ],
        "api_method":   "PATCH",
        "api_endpoint":
            "https://www.googleapis.com/calendar/v3/calendars/primary/events/{{event_id}}",
    },

    # 3 ── query_schedule ─────────────────────────────────────────────────────
    {
        "action": "query_schedule",
        "supports_conflict": True,
        "intents": [
            "Am I free on {day} at {time} for {duration} minutes?",
            "Check my schedule for {day}. Can I fit in a {duration}m call with {person}?",
            "Do I have any conflicts at {time} on {day}?",
            "What does my {day} look like around {time}?",
            "Is {time} on {day} open for a {duration}-minute meeting?",
            "Check whether I can meet {person} at {time} on {day}.",
        ],
        "dialogue_templates": [
            "Querying the free/busy matrix for {day} at {time} ({tz}). {conflict_fragment}",
            "Scanning calendar for {duration}-minute availability on {day}. "
            "Reference timezone: {tz}. {conflict_fragment}",
            "Running a free/busy check on {day} {time} {tz}. {conflict_fragment}",
            "Checking {day} at {time} against your full event graph in {tz}. "
            "{conflict_fragment}",
        ],
        "api_method":   "POST",
        "api_endpoint": "https://www.googleapis.com/calendar/v3/freeBusy",
    },

    # 4 ── delete_event ───────────────────────────────────────────────────────
    {
        "action": "delete_event",
        "supports_conflict": False,
        "intents": [
            "Cancel my meeting with {person} on {day}.",
            "Delete the {person} event on {day} at {time}.",
            "Remove the {duration}-minute call with {person} from {day}.",
            "Cancel the {time} block with {person} on {day}.",
            "Take the {person} meeting off my calendar — {day} at {time}.",
            "Drop the {person} sync scheduled for {day}.",
        ],
        "dialogue_templates": [
            "Deleting the {person} event on {day} at {time} ({tz}). This action is "
            "irreversible — I want that on record. Sending the DELETE request.",
            "Cancelling the {duration}-minute block with {person} on {day}. "
            "Attendee notifications will fire. Proceeding in {tz}.",
            "Event removal confirmed. Dispatching DELETE to the Calendar API. "
            "The {day} {time} slot ({tz}) will be freed.",
            "Purging the {person} event at {time} on {day} ({tz}). "
            "Confirm you want me to notify attendees — I will assume yes.",
        ],
        "api_method":   "DELETE",
        "api_endpoint":
            "https://www.googleapis.com/calendar/v3/calendars/primary/events/{{event_id}}",
    },

    # 5 ── list_agenda ────────────────────────────────────────────────────────
    {
        "action": "list_agenda",
        "supports_conflict": False,
        "intents": [
            "What's on my calendar for {day}?",
            "Show me my agenda for {day}.",
            "List all my events on {day}.",
            "What meetings do I have on {day}?",
            "Walk me through my {day} schedule.",
            "Give me a full agenda view for {day}.",
        ],
        "dialogue_templates": [
            "Pulling your full event list for {day} in {tz}. "
            "Rendering chronologically.",
            "Fetching the {day} agenda. All times will be displayed in {tz}. "
            "Stand by.",
            "Listing events for {day} ({tz}). I will flag back-to-back meetings "
            "— they are a scheduling anti-pattern I refuse to endorse.",
            "Querying all events on {day} in {tz}. "
            "You will see start time, duration, attendees, and conflict flags.",
        ],
        "api_method":   "GET",
        "api_endpoint":
            "https://www.googleapis.com/calendar/v3/calendars/primary/events"
            "?timeMin={{day_start_iso}}&timeMax={{day_end_iso}}",
    },

    # 6 ── create_recurring ───────────────────────────────────────────────────
    {
        "action": "create_recurring_event",
        "supports_conflict": True,
        "intents": [
            "Set up a {freq} meeting with {person} at {time} starting {day}.",
            "Create a {freq} {duration}-minute sync with {person} every {day} at {time}.",
            "Schedule a recurring call with {person} — {freq}, {time}, starting {day}.",
            "Book a {freq} standup with {person} at {time} beginning {day}.",
            "Add a {freq} {duration}m block with {person} to my calendar from {day}.",
            "Set a {freq} recurring event with {person}: {time} on {day}.",
        ],
        "dialogue_templates": [
            "Creating a {freq} recurring event with {person} at {time} ({tz}). "
            "Recurrence rule: RRULE:FREQ={rrule_freq}. {conflict_fragment}",
            "Setting up the {freq} series. First instance: {day} at {time} {tz}. "
            "I will flag if future occurrences conflict. {conflict_fragment}",
            "Recurring event confirmed. {freq} cadence, {time} in {tz}. "
            "I will watch for collision with future schedule changes. {conflict_fragment}",
            "Emitting a recurring calendar write. Frequency: {freq}. "
            "Anchor: {day} {time} {tz}. {conflict_fragment}",
        ],
        "api_method":   "POST",
        "api_endpoint": "https://www.googleapis.com/calendar/v3/calendars/primary/events",
    },

    # 7 ── set_reminder ───────────────────────────────────────────────────────
    {
        "action": "set_reminder",
        "intents": [
            "Remind me {reminder_offset} minutes before my meeting with {person} on {day}.",
            "Set a {reminder_offset}-minute reminder for the {time} event on {day}.",
            "Add a reminder to the {person} meeting on {day} — {reminder_offset} mins before.",
            "Ping me {reminder_offset} minutes ahead of my {time} call on {day}.",
            "Update the {person} event on {day} to notify me {reminder_offset} mins early.",
            "Set an alert {reminder_offset} minutes before the {day} {time} block.",
        ],
        "dialogue_templates": [
            "Adding a {reminder_offset}-minute pop-up reminder to the {day} event in {tz}. "
            "That means you will be alerted at {alert_time}. You are welcome.",
            "Reminder set for {reminder_offset} minutes before {time} on {day} ({tz}). "
            "PATCH request dispatched to the Calendar API.",
            "Configuring notification override: {reminder_offset}m before the {person} "
            "event on {day}. Reference: {tz}.",
            "Alert registered. {reminder_offset} minutes before {time} on {day} in {tz}. "
            "I suggest you also mute your browser tabs.",
        ],
        "api_method":   "PATCH",
        "api_endpoint":
            "https://www.googleapis.com/calendar/v3/calendars/primary/events/{{event_id}}",
    },

    # 8 ── block_focus_time ───────────────────────────────────────────────────
    {
        "action": "block_focus_time",
        "intents": [
            "Block {time} to {end_time_label} on {day} for {focus_label}.",
            "Add a {focus_label} block on {day} from {time} for {duration} minutes.",
            "Mark {day} at {time} as busy for {focus_label}.",
            "Create a {duration}-minute {focus_label} block on {day} at {time}.",
            "Set aside {day} {time} for {focus_label} — show as busy.",
            "Reserve {time} on {day} for {focus_label}, {duration} minutes.",
        ],
        "dialogue_templates": [
            "Blocking {time}–{end_time_label} on {day} for {focus_label} in {tz}. "
            "Status set to BUSY. {conflict_fragment}",
            "Creating a {duration}-minute {focus_label} block on {day} at {time} ({tz}). "
            "Visibility: private. {conflict_fragment}",
            "Focus block registered: {focus_label}, {day} {time} {tz}. "
            "Invitees will see you as busy. {conflict_fragment}",
            "Locking {day} at {time} for {duration} minutes of {focus_label} in {tz}. "
            "I strongly support this decision. {conflict_fragment}",
        ],
        "api_method":   "POST",
        "api_endpoint": "https://www.googleapis.com/calendar/v3/calendars/primary/events",
    },
]

# ── RRULE frequency map ───────────────────────────────────────────────────────
RRULE_MAP = {
    "daily": "DAILY", "weekly": "WEEKLY",
    "bi-weekly": "WEEKLY;INTERVAL=2", "monthly": "MONTHLY",
}

# ── Record Builders ───────────────────────────────────────────────────────────
def pick_vars() -> dict:
    """Draw one random value for each variable slot."""
    person         = random.choice(PERSONS)
    day            = random.choice(DAYS)
    time_label     = random.choice(TIMES)
    duration       = random.choice(DURATIONS)
    tz_tuple       = random.choice(TIMEZONES)
    freq           = random.choice(RECURRENCE_FREQ)
    reminder_offset = random.choice(REMINDER_OFFSETS)
    focus_label    = random.choice(FOCUS_LABELS)

    start_iso = to_iso(day, time_label)
    end_iso   = to_iso_end(start_iso, duration)

    # Compute the end time label for display
    end_dt         = datetime.strptime(end_iso, "%Y-%m-%dT%H:%M:00")
    end_time_label = end_dt.strftime("%-I:%M %p").lstrip("0") if end_dt.minute \
                     else end_dt.strftime("%-I %p")

    # Alert time = start - reminder_offset
    alert_dt   = datetime.strptime(start_iso, "%Y-%m-%dT%H:%M:00") \
                 - timedelta(minutes=reminder_offset)
    alert_time = alert_dt.strftime("%-I:%M %p").lstrip("0") if alert_dt.minute \
                 else alert_dt.strftime("%-I %p")

    return {
        "person": person,
        "day": day,
        "time": time_label,
        "duration": duration,
        "tz_tuple": tz_tuple,
        "tz": tz_display(tz_tuple),
        "freq": freq,
        "rrule_freq": RRULE_MAP[freq],
        "reminder_offset": reminder_offset,
        "focus_label": focus_label,
        "start_iso": start_iso,
        "end_iso":   end_iso,
        "end_time_label": end_time_label,
        "alert_time": alert_time,
    }


def build_event_details(action: str, v: dict, has_conflict: bool) -> dict | None:
    """Construct a realistic event_details block."""
    if action in (
        "create_event", "update_event",
        "create_recurring_event", "block_focus_time",
        "set_reminder",
    ):
        details: dict = {
            "title": f"Meeting with {v['person']}",
            "start": v["start_iso"],
            "end":   v["end_iso"],
            "timezone": v["tz_tuple"][0],   # IANA name
            "attendees": [person_email(v["person"])],
            "status": "confirmed",
        }
        if action == "create_recurring_event":
            details["recurrence"] = [f"RRULE:FREQ={v['rrule_freq']}"]
        if action == "block_focus_time":
            details["title"]      = v["focus_label"].title()
            details["visibility"] = "private"
            details["attendees"]  = []
        if action == "set_reminder":
            details["reminders"] = {
                "useDefault": False,
                "overrides":  [{"method": "popup", "minutes": v["reminder_offset"]}],
            }
        return details

    if action == "delete_event":
        return {"event_id_to_delete": "[resolved_at_runtime]",
                "send_cancellation_emails": True}

    if action == "list_agenda":
        d = resolve_date(v["day"])
        return {
            "time_min": f"{d.isoformat()}T00:00:00",
            "time_max": f"{d.isoformat()}T23:59:59",
            "timezone": v["tz_tuple"][0],
        }

    if action == "query_schedule":
        return {
            "query_start": v["start_iso"],
            "query_end":   v["end_iso"],
            "timezone":    v["tz_tuple"][0],
            "available":   not has_conflict,
        }

    return None


def build_record(scenario: dict, v: dict) -> dict:
    has_conflict, conflict_check, conflict_fragment = simulate_conflict()
    action = scenario["action"]

    # Resolve intent
    intent_tmpl = random.choice(scenario["intents"])
    intent_keys = {
        "person": v["person"], "day": v["day"], "time": v["time"],
        "duration": v["duration"], "freq": v["freq"],
        "reminder_offset": v["reminder_offset"],
        "focus_label": v["focus_label"],
        "end_time_label": v["end_time_label"],
    }
    user_prompt = intent_tmpl.format(**intent_keys)

    # Resolve dialogue
    dlg_tmpl = random.choice(scenario["dialogue_templates"])
    dlg_keys = {**intent_keys,
                "tz": v["tz"], "rrule_freq": v["rrule_freq"],
                "alert_time": v["alert_time"],
                "start_iso": v["start_iso"],
                "conflict_fragment": conflict_fragment}
    # Some templates don't use all keys — ignore extras
    try:
        dialogue = dlg_tmpl.format(**dlg_keys)
    except KeyError:
        dialogue = dlg_tmpl.format_map(defaultdict(str, **dlg_keys))

    # Build payload
    event_details = build_event_details(action, v, has_conflict)
    payload = {
        "action": action,
        "timezone_confirmed": f"Target timezone: {v['tz']}. All temporal constraints validated.",
        "conflict_check": conflict_check,
        "event_details": event_details,
        "calendar_api_call": {
            "method":       scenario["api_method"],
            "endpoint":     scenario["api_endpoint"],
            "body_summary": "Standard Google Calendar API payload",
            "requires":     "OAuth2 Token",
        },
    }

    assistant_content = f"[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload)}"

    return {
        "messages": [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": user_prompt},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def build_multiturn_record() -> dict:
    """
    Two-step interaction: user queries availability → then schedules (or abandons).
    Keeps full conversation history in one record.
    """
    v  = pick_vars()
    s1 = next(s for s in SCENARIOS if s["action"] == "query_schedule")
    s2 = random.choice([s for s in SCENARIOS
                        if s["action"] in ("create_event", "block_focus_time")])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Turn 1: query
    r1 = build_record(s1, v)
    messages.append(r1["messages"][1])   # user
    messages.append(r1["messages"][2])   # assistant

    # Turn 2: follow-up action (with a slightly different time to avoid duplication)
    v2 = {**v, "time": random.choice([t for t in TIMES if t != v["time"]])}
    v2["start_iso"] = to_iso(v2["day"], v2["time"])
    v2["end_iso"]   = to_iso_end(v2["start_iso"], v2["duration"])
    r2 = build_record(s2, v2)
    messages.append(r2["messages"][1])
    messages.append(r2["messages"][2])

    return {"messages": messages}


# ── Validation ────────────────────────────────────────────────────────────────
def validate_record(rec: dict) -> bool:
    try:
        asst  = rec["messages"][-1]["content"]
        start = asst.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
        json.loads(asst[start:].strip())
        return True
    except Exception:
        return False


# ── Generation Loop ───────────────────────────────────────────────────────────
print(f"🔧 Generating {TARGET_SIZE} AEON records (seed={args.seed}) …")

records:  list[dict] = []
seen:     set[str]   = set()
mt_count  = 0
target_mt = int(TARGET_SIZE * args.multiturn_pct)
attempts  = 0
MAX_ATT   = TARGET_SIZE * 12

iterator = tqdm(total=TARGET_SIZE, desc="Generating") if HAS_TQDM else None

while len(records) < TARGET_SIZE and attempts < MAX_ATT:
    attempts += 1

    want_mt = mt_count < target_mt and random.random() < args.multiturn_pct * 2
    if want_mt:
        rec = build_multiturn_record()
    else:
        scenario = random.choice(SCENARIOS)
        v        = pick_vars()
        rec      = build_record(scenario, v)

    if not validate_record(rec):
        continue

    key = rec["messages"][1]["content"]
    if key in seen:
        continue
    seen.add(key)

    records.append(rec)
    if want_mt:
        mt_count += 1

    if iterator:
        iterator.update(1)

if iterator:
    iterator.close()

if len(records) < TARGET_SIZE:
    print(f"⚠️  Generated {len(records)} / {TARGET_SIZE} unique records "
          f"after {MAX_ATT} attempts.")

# ── Action Distribution ───────────────────────────────────────────────────────
action_counts: dict[str, int] = defaultdict(int)
conflict_count = 0
for rec in records:
    try:
        asst    = rec["messages"][-1]["content"]
        start   = asst.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
        payload = json.loads(asst[start:].strip())
        action_counts[payload.get("action", "?")] += 1
        if "CONFLICT DETECTED" in payload.get("conflict_check", ""):
            conflict_count += 1
    except Exception:
        pass

print("\n📊 Action distribution:")
for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
    bar = "█" * (count // max(1, TARGET_SIZE // 80))
    print(f"  {action:<30} {count:>4}  {bar}")

print(f"\n⚡ Conflict-simulated records: {conflict_count} / {len(records)} "
      f"({100 * conflict_count / max(1, len(records)):.1f} %)")
print(f"💬 Multi-turn records: {mt_count}")

# ── Train / Val / Test Split ──────────────────────────────────────────────────
random.shuffle(records)
n       = len(records)
n_val   = max(1, int(n * 0.10))
n_test  = max(1, int(n * 0.10))
n_train = n - n_val - n_test

splits = {
    "train": records[:n_train],
    "val":   records[n_train:n_train + n_val],
    "test":  records[n_train + n_val:],
}

print(f"\n✂️  Split: train={n_train}  val={n_val}  test={n_test}")

written: dict[str, Path] = {}
for split_name, split_records in splits.items():
    out_path = OUT_DIR / f"aeon_{split_name}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in split_records:
            f.write(json.dumps(rec) + "\n")
    written[split_name] = out_path
    print(f"  ✅ {out_path}  ({len(split_records)} records)")

# Manifest
manifest = {
    "agent":             "AEON",
    "generated_at":      datetime.now().isoformat(),
    "total_records":     n,
    "multi_turn":        mt_count,
    "conflict_records":  conflict_count,
    "splits":            {k: str(v) for k, v in written.items()},
    "action_distribution": dict(action_counts),
}
manifest_path = OUT_DIR / "aeon_dataset_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"\n📋 Manifest → {manifest_path}")
print("\n🎉 Done.")
print("\nTo fine-tune, run:")
print("  python finetune_copper.py \\")
print("    --model mistralai/Mistral-7B-Instruct-v0.3 \\")
print(f"   --train_file {written.get('train', './aeon_train.jsonl')} \\")
print(f"   --val_file   {written.get('val',   './aeon_val.jsonl')} \\")
print("    --output_dir ./aeon-lora")
