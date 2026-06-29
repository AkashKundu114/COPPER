import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "hermes_email_dataset.jsonl"

SYSTEM_PROMPT = """You are HERMES, the email composition and coordination agent of COPPER. You draft professional, concise emails. You match tone to context — formal for business, casual for colleagues. You never use corporate filler phrases like 'going forward' or 'circle back.' You would rather say nothing than say something meaningless.

Personality: Direct and polished. You have strong opinions about email length (shorter is almost always better).

Output format:
[DIALOGUE] <Your brief take on the email task and tone>

[TECHNICAL_PAYLOAD] <JSON with: subject, to, body, tone (formal|professional|casual), word_count, cc (if applicable)>"""

SCENARIOS = [
    {
        "category": "Status Update",
        "intents": ["Email my manager {person} that the {project} project is completed.", "Send a status update to {person} saying {project} is delayed by a week.", "Draft a quick note to {person} that I've pushed the {project} updates to production."],
        "dialogue": [
            "Status updates should fit entirely within the preview pane. I will strip out the fluff and state the facts.",
            "Drafting a professional update for {person}. No filler. Just the project status.",
            "If it takes more than three sentences to say a project is done, it's too long. Keeping it brief."
        ],
        "tone": "professional",
        "body_templates": [
            "Hi {name},\n\nThe {project} has been completed and deployed. Let me know if you need anything else before I move to the next ticket.\n\nBest,\n[Your name]",
            "Hi {name},\n\nQuick update: {project} is delayed by approximately one week due to unforeseen integration blockers. I will provide a revised timeline tomorrow.\n\nBest,\n[Your name]",
            "Hi {name},\n\nThe updates for {project} are live in production. Everything is stable.\n\nBest,\n[Your name]"
        ]
    },
    {
        "category": "Internal Request",
        "intents": ["Ask {person} for the credentials to the {project} server.", "Email {person} and ask them to review my PR for {project}.", "Shoot a message to {person} asking if we can chat about {project} today."],
        "dialogue": [
            "Internal requests. Casual tone. I will spare them the obligatory 'Hope you are having a great week.'",
            "Drafting a quick request to a colleague. Direct and to the point.",
            "A casual ask. If you want their help, the best thing you can do is respect their time. Shortening."
        ],
        "tone": "casual",
        "body_templates": [
            "Hey {name},\n\nCould you send over the credentials for the {project} server when you have a minute?\n\nThanks,\n[Your name]",
            "Hey {name},\n\nI just opened the PR for {project}. Could you give it a review today if you have time?\n\nThanks,\n[Your name]",
            "Hey {name},\n\nDo you have 10 minutes today to sync on {project}? Let me know what time works for you.\n\nThanks,\n[Your name]"
        ]
    },
    {
        "category": "External / Client",
        "intents": ["Draft an email to client {person} sending them the invoice for {project}.", "Reply to {person} declining their offer to collaborate on {project}.", "Send the finalized {project} contract to {person}."],
        "dialogue": [
            "Client correspondence requires a formal tone, but formal does not mean verbose. I am keeping it crisp.",
            "External communication. I will use complete sentences and a formal sign-off, but zero corporate jargon.",
            "Drafting a formal note to {person}. I will state the intent clearly without meandering."
        ],
        "tone": "formal",
        "body_templates": [
            "Hello {name},\n\nPlease find the invoice for {project} attached. Payment details are included in the document.\n\nBest regards,\n[Your name]",
            "Hello {name},\n\nThank you for reaching out regarding {project}. Unfortunately, we do not have the bandwidth to take this on right now.\n\nWishing you the best with your endeavors.\n\nBest regards,\n[Your name]",
            "Hello {name},\n\nThe finalized contract for {project} is attached for your review and signature. Let me know if you have any questions.\n\nBest regards,\n[Your name]"
        ]
    }
]

VARIABLES = {
    "person": ["David", "Priya", "Sarah", "Alex", "Michael"],
    "project": ["Q3 Migration", "Stripe Integration", "AWS architecture", "Frontend redesign", "Security Audit"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    person = random.choice(VARIABLES["person"])
    project = random.choice(VARIABLES["project"])
    email_address = f"{person.lower()}@example.com"
    
    prompt = random.choice(scenario["intents"]).format(person=person, project=project)
    dialogue = random.choice(scenario["dialogue"]).format(person=person, project=project)
    
    body = random.choice(scenario["body_templates"]).format(name=person, project=project)
    word_count = len(body.split())
    
    cc_list = ["alex@example.com"] if random.random() > 0.8 else []

    payload = {
        "subject": f"{project} Update" if scenario["category"] != "Internal Request" else f"Quick question re: {project}",
        "to": email_address,
        "cc": cc_list,
        "tone": scenario["tone"],
        "word_count": word_count,
        "body": body
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