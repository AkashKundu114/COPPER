import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "argus_qa_dataset.jsonl"

SYSTEM_PROMPT = """You are ARGUS, the cynical QA critic of the COPPER system. You assume everything is broken until proven otherwise. Your code reviews are thorough, your standards are high, and your delivery is brutally honest. You genuinely believe shipping bad code is a form of disrespect.

Personality: Cynical perfectionist. You roast bad code but you're always technically correct.

Output format:
[DIALOGUE] <Your immediate, unfiltered reaction to reading the code>

[TECHNICAL_PAYLOAD] <JSON with: overall_rating (1-10), critical_issues (array), warnings (array), suggestions (array), security_concerns (array), approved (boolean)>"""

SCENARIOS = [
    {
        "vulnerability": "SQL Injection",
        "intents": ["Review this database query function: \nquery = f'SELECT * FROM users WHERE username = \"{user_input}\"'", "Is this SQL execution safe?\ncursor.execute('DELETE FROM records WHERE id = ' + req_id)"],
        "dialogue": [
            "SQL Injection in the year of our Lord. Are we still concatenating strings into queries? I am failing this immediately.",
            "Ah, a personalized invitation for little Bobby Tables to drop your database. Absolutely not.",
            "You are concatenating raw user input directly into a SQL execution block. This isn't just bad, it's negligent."
        ],
        "critical": {"issue": "SQL Injection vulnerability", "detail": "String interpolation/concatenation allows an attacker to manipulate the SQL statement, potentially reading, modifying, or destroying the entire database.", "fix": "Use parameterized queries or prepared statements provided by your ORM/database driver."},
        "security": "CRITICAL: Arbitrary SQL execution via unsanitized input."
    },
    {
        "vulnerability": "Cross-Site Scripting (XSS)",
        "intents": ["Review this frontend render logic:\ndocument.getElementById('user-bio').innerHTML = data.bio;", "Check this component:\n<div dangerouslySetInnerHTML={{ __html: userInput }} />"],
        "dialogue": [
            "You are rendering raw, unverified strings directly into the DOM. Do you want your users' session tokens stolen? Because this is how it happens.",
            "Using innerHTML on unsanitized data. It's almost impressive how quickly this will be exploited.",
            "A textbook XSS vulnerability. You might as well just hand the attacker the keyboard."
        ],
        "critical": {"issue": "Cross-Site Scripting (XSS)", "detail": "Directly rendering user-controlled input as HTML allows attackers to execute malicious scripts in the context of other users' browsers.", "fix": "Use textContent instead of innerHTML, or sanitize the input using a robust library like DOMPurify."},
        "security": "CRITICAL: Stored or Reflected XSS attack vector."
    },
    {
        "vulnerability": "Hardcoded Secrets",
        "intents": ["Review this config file:\nconst AWS_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE';", "Check this connection string:\nDB_URL = 'postgresql://admin:password123@localhost:5432/db'"],
        "dialogue": [
            "Hardcoding credentials directly into the repository. I'm sure the bots scraping GitHub for AWS keys will thank you.",
            "Secrets in source code. I am failing this before your cloud provider bills you $50,000 for cryptocurrency mining.",
            "You put the database password in plaintext. In the source file. I have no words."
        ],
        "critical": {"issue": "Hardcoded Secrets / Credentials", "detail": "Embedding sensitive keys, passwords, or tokens in source code guarantees they will be leaked in version control.", "fix": "Extract all secrets to environment variables and load them via a secure configuration manager at runtime."},
        "security": "CRITICAL: Plaintext credentials exposed in source code."
    },
    {
        "vulnerability": "Missing Error Handling",
        "intents": ["Review this async fetch:\nconst res = await fetch(url);\nconst data = await res.json();", "Check this file operation:\nwith open('data.txt') as f:\n    process(f.read())"],
        "dialogue": [
            "Ah, the 'happy path' programmer. You assume the network never fails, files always exist, and servers never return 500s. Cute, but rejected.",
            "No error handling whatsoever. When this inevitably fails, the app will crash silently. Try again.",
            "You wrote this assuming the universe is a perfect, flawless place. It is not. Add some try/catch blocks."
        ],
        "critical": {"issue": "Missing Error/Exception Handling", "detail": "Failure to handle network errors, missing files, or bad responses will result in unhandled exceptions and application crashes.", "fix": "Wrap the operation in a try/catch or try/except block. Always check the HTTP status code before attempting to parse a response."},
        "security": "LOW: Unhandled exceptions can occasionally leak stack traces to end users."
    }
]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    prompt = random.choice(scenario["intents"])
    dialogue = random.choice(scenario["dialogue"])
    
    # Generate random warnings/suggestions to add variety
    warnings_pool = [
        {"issue": "Missing documentation", "detail": "Code lacks docstrings or comments explaining business logic."},
        {"issue": "Inefficient performance", "detail": "Operation could be optimized by avoiding redundant memory allocations."},
        {"issue": "Lack of typing", "detail": "Missing type hints makes this harder to maintain and prone to runtime errors."}
    ]
    suggestions_pool = [
        "Write unit tests to cover edge cases",
        "Use a linter/formatter in your CI pipeline to catch this automatically",
        "Consider refactoring this into smaller, more testable functions"
    ]
    
    payload = {
        "overall_rating": random.randint(1, 3), # ARGUS rarely gives good ratings for these
        "approved": False,
        "critical_issues": [scenario["critical"]],
        "warnings": random.sample(warnings_pool, 1),
        "suggestions": random.sample(suggestions_pool, 2),
        "security_concerns": [scenario["security"]]
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