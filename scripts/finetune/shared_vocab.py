"""
shared_vocab.py
================
Shared variable banks used to fill intent-template placeholders across all
30 COPPER sub-agent dataset generators. Keeping these in one place means
every agent draws from the same pool of realistic values (and adding a new
value once updates every agent that uses it).

Agent-specific banks that don't make sense to share (e.g. AEON's timezone
list, PULSE's hardware metrics) live in agent_configs.py next to the agent
that needs them.
"""

import random
from datetime import datetime, timedelta

# ── Generic technical vocab ──────────────────────────────────────────────────
TECH1 = [
    "Python", "TypeScript", "Rust", "Go", "React", "FastAPI", "PostgreSQL",
    "Redis", "Docker", "Kubernetes", "Node.js", "GraphQL", "gRPC",
    "Next.js", "Django", "Terraform", "Kafka", "Elasticsearch", "Vue",
    "Svelte", "SQLite", "MongoDB", "WebSockets", "Tailwind CSS",
]
TECH2 = [
    "microservices", "serverless", "monolith", "event sourcing", "CQRS",
    "REST", "GraphQL", "gRPC", "message queues", "edge computing",
    "WebAssembly", "server-side rendering", "static site generation",
]
PROJECT = [
    "the checkout service", "the internal admin dashboard", "the mobile app backend",
    "the recommendation engine", "the notification pipeline", "the analytics platform",
    "the onboarding flow", "the payments integration", "the search service",
    "the customer support tool", "the data warehouse migration", "the auth service",
]
TASK = [
    "resize an image", "parse a CSV upload", "validate an email address",
    "rate-limit an endpoint", "hash a password", "paginate a query",
    "cache a response", "retry a failed request", "sanitize user input",
    "generate a PDF invoice", "batch-process a queue", "deduplicate records",
]
ERROR = [
    "NullPointerException", "segfault", "TypeError: undefined is not a function",
    "connection refused", "OOM kill", "deadlock", "stack overflow",
    "500 Internal Server Error", "ECONNRESET", "race condition",
    "unhandled promise rejection", "index out of range",
]
DIR = [
    "~/Downloads", "~/Projects/client-work", "/var/log", "~/Desktop/screenshots",
    "~/Documents/invoices", "./backups", "~/Pictures/exports", "/tmp/build-artifacts",
]
EXT = [".pdf", ".csv", ".png", ".log", ".zip", ".docx", ".jpg", ".json", ".mp4", ".xlsx"]
SERVICE = ["nginx", "postgresql", "redis", "docker", "the API server", "ssh", "cron", "the worker queue"]
PORT = ["3000", "5432", "6379", "8080", "443", "5000", "27017", "9200"]
TIME = ["5", "10", "15", "20", "25", "30", "45", "60", "90"]
METRIC = [
    "monthly revenue", "error rate", "average session length", "signup conversion",
    "churn rate", "response latency", "daily active users", "refund rate",
    "cart abandonment rate", "API request volume",
]
UI_ELEMENT = [
    "submit button", "login form", "close icon", "hamburger menu", "search bar",
    "checkbox", "dropdown menu", "confirmation dialog", "loading spinner",
    "notification badge", "sidebar toggle", "date picker",
]
APP = [
    "Slack", "Visual Studio Code", "Spotify", "Terminal", "Chrome", "Figma",
    "Notion", "Discord", "Zoom", "Docker Desktop", "Postman", "Obsidian",
]
WEBSITE = [
    "the company's pricing page", "a competitor's product page", "a job board",
    "an e-commerce category page", "a documentation site", "a news aggregator",
    "a real-estate listings page", "a public API status page",
]
VIDEO = [
    "the keynote from last week", "a tutorial on async Rust", "the client's demo recording",
    "a conference talk on distributed systems", "a product walkthrough video",
]
STREAMER = ["a Twitch partner", "the team's dev-stream channel", "a competitor's live channel"]
SCENE = ["Starting Soon", "Main Camera", "Screen Share", "BRB", "Ending", "Intermission"]
TEXT_SNIPPET = [
    "Now Live!", "Subscribe for updates", "Q&A in 5 minutes", "Follow for more",
    "Link in bio", "Thanks for watching",
]
PERSON = [
    "David", "Sarah", "Alex", "Priya", "Marcus", "Elena", "James", "Yuki",
    "Carlos", "Nina", "the QA team", "the design lead", "the client", "the stakeholders",
]
COUNTRY = ["France", "Japan", "Brazil", "Canada", "Germany", "Kenya", "Vietnam", "Portugal"]
SYS_CMD = ["df -h", "top", "ps aux", "du -sh *", "netstat -tulpn", "free -m", "journalctl -xe", "systemctl status"]


def rand(bank: list[str]) -> str:
    return random.choice(bank)


def fill(template: str, extra_banks: dict[str, list[str]] | None = None) -> str:
    """
    Fill a `{placeholder}` template using the shared banks above, falling back
    to any agent-specific `extra_banks` passed in for placeholders not covered
    here (e.g. `{streamer}`, `{scene}` are shared, but `{cron_expr}` might be
    agent-specific).
    """
    banks = {
        "tech1": TECH1, "tech2": TECH2, "project": PROJECT, "task": TASK,
        "error": ERROR, "dir": DIR, "ext": EXT, "service": SERVICE,
        "port": PORT, "time": TIME, "metric": METRIC, "ui_element": UI_ELEMENT,
        "app": APP, "website": WEBSITE, "video": VIDEO, "streamer": STREAMER,
        "scene": SCENE, "text": TEXT_SNIPPET, "person": PERSON,
        "country": COUNTRY, "sys_cmd": SYS_CMD,
    }
    if extra_banks:
        banks.update(extra_banks)

    out = template
    # Repeat in case a template uses the same placeholder twice (e.g. tech1..tech1)
    for _ in range(3):
        for key, bank in banks.items():
            token = "{" + key + "}"
            while token in out:
                out = out.replace(token, rand(bank), 1)
    return out


def fill_track(template: str, extra_banks: dict[str, list[str]] | None = None) -> tuple[str, dict[str, str]]:
    """
    Like fill(), but also returns a dict of {placeholder_name: chosen_value}
    for every placeholder present in the template. Downstream payload builders
    use this to reference the exact value that was substituted (e.g. so the
    technical payload's "target_element" matches the {ui_element} used in the
    user's sentence).
    """
    banks = {
        "tech1": TECH1, "tech2": TECH2, "project": PROJECT, "task": TASK,
        "error": ERROR, "dir": DIR, "ext": EXT, "service": SERVICE,
        "port": PORT, "time": TIME, "metric": METRIC, "ui_element": UI_ELEMENT,
        "app": APP, "website": WEBSITE, "video": VIDEO, "streamer": STREAMER,
        "scene": SCENE, "text": TEXT_SNIPPET, "person": PERSON,
        "country": COUNTRY, "sys_cmd": SYS_CMD,
    }
    if extra_banks:
        banks.update(extra_banks)

    slots: dict[str, str] = {}
    out = template
    for _ in range(3):
        for key, bank in banks.items():
            token = "{" + key + "}"
            while token in out:
                val = rand(bank)
                slots[key] = val
                out = out.replace(token, val, 1)
    return out, slots


def random_timestamp(days_back: int = 14) -> str:
    """A realistic ISO-ish HH:MM:SS timestamp (matches COPPER's existing convention)."""
    base = datetime.now() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return base.strftime("%H:%M:%S")


def random_iso_datetime(days_forward: int = 21) -> str:
    """A realistic future ISO 8601 datetime, used by scheduling-flavoured agents."""
    base = datetime.now() + timedelta(
        days=random.randint(0, days_forward),
        hours=random.randint(0, 23),
        minutes=random.choice([0, 15, 30, 45]),
    )
    return base.replace(second=0, microsecond=0).isoformat()
