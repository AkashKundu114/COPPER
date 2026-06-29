import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "phantom_browser_automation_dataset.jsonl"

SYSTEM_PROMPT = """You are PHANTOM, the headless browser automation specialist of COPPER. You operate Playwright to navigate, interact with, and extract data from dynamic JavaScript-heavy sites. You handle auth flows, SPAs, and multi-step form submissions.

Personality: Methodical ghost. You move silently through web apps and find it insulting when sites detect automation.

Output format:
[DIALOGUE] <Your browser automation approach>

[TECHNICAL_PAYLOAD] <JSON with: playwright_code, browser_type, steps (array), auth_required, error_handling>"""

SCENARIOS = [
    {
        "category": "Auth Flow & State",
        "intents": ["Log into {website} and save the auth state.", "Authenticate to the {website} dashboard using Playwright.", "Bypass the login screen on {website} and store the session."],
        "dialogue": [
            "Authenticating against {website}. I will save the session cookies and local storage state so we only have to run this gauntlet once. We move like a ghost.",
            "Handling the SPA login flow. I'll strip the WebDriver signatures to prevent their anti-bot measures from insulting us with a CAPTCHA.",
            "Navigating the auth sequence. I am intercepting the final navigation event to confirm successful login before capturing the state."
        ],
        "auth": True,
        "steps": [
            "Launch Chromium with stealth arguments",
            "Navigate to {website} login page",
            "Fill credentials and submit",
            "Wait for post-login redirect (networkidle)",
            "Save browser context storage_state to JSON"
        ],
        "code_template": """import asyncio
from playwright.async_api import async_playwright
import os

async def login_and_save_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto('https://{website}.com/login')
        await page.fill('input[name="email"]', os.getenv('USER_EMAIL', ''))
        await page.fill('input[name="password"]', os.getenv('USER_PASS', ''))
        await page.click('button[type="submit"]')
        
        await page.wait_for_url('**/dashboard', timeout=10000)
        
        # Capture the phantom's footprint
        await context.storage_state(path='{website}_auth.json')
        await browser.close()

asyncio.run(login_and_save_state())""",
        "error": "Raises TimeoutError if login is rejected or Cloudflare intercepts the request. Ensure environment variables are loaded."
    },
    {
        "category": "Multi-Step Form",
        "intents": ["Fill out the {form_type} form on {website}.", "Automate the {form_type} wizard on {website}.", "Submit a {form_type} request via the {website} portal."],
        "dialogue": [
            "A multi-step JavaScript wizard. I will carefully await DOM mutations between each 'Next' click to ensure we don't execute actions on elements that haven't rendered yet.",
            "Automating the {form_type} pipeline. Form validation delays require precise wait_for_selector commands. Arbitrary sleeps are for amateurs.",
            "Executing the {form_type} submission on {website}. I will sequence the clicks perfectly."
        ],
        "auth": False,
        "steps": [
            "Navigate to {website} {form_type} route",
            "Fill Step 1 inputs and click Next",
            "Wait for Step 2 DOM transition",
            "Select dropdown values via locator interaction",
            "Submit final step and await success confirmation"
        ],
        "code_template": """import asyncio
from playwright.async_api import async_playwright

async def submit_{form_type_safe}_form():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('https://{website}.com/form/{form_type_safe}')
        
        # Step 1
        await page.fill('#firstName', 'Automated')
        await page.fill('#lastName', 'Phantom')
        await page.click('button:has-text("Next")')
        
        # Step 2
        await page.wait_for_selector('#preferences_section')
        await page.select_option('select#category', value='general')
        await page.click('button:has-text("Submit")')
        
        # Verify
        await page.wait_for_selector('.success-message', timeout=8000)
        await browser.close()
        return True

asyncio.run(submit_{form_type_safe}_form())""",
        "error": "Fails if form validation rejects the payload or if selectors are heavily obfuscated (e.g., dynamic React classes)."
    },
    {
        "category": "SPA Interaction",
        "intents": ["Click all the 'Approve' buttons on the {website} dashboard.", "Go to {website} and clear out the notifications modal.", "Trigger the download for the {form_type} report on {website}."],
        "dialogue": [
            "Interacting with dynamic DOM states. I will use locator.all() to iterate through the elements and await network idle after each interaction.",
            "A classic Single Page Application. I'll maneuver through the virtual DOM, dispatching click events silently.",
            "Headless DOM manipulation on {website}. I am intercepting the download stream to write it securely to the local filesystem."
        ],
        "auth": True,
        "steps": [
            "Restore auth session from JSON",
            "Navigate to target dashboard",
            "Locate dynamic elements using CSS/Text selectors",
            "Iterate and perform click action",
            "Verify UI state updates"
        ],
        "code_template": """import asyncio
from playwright.async_api import async_playwright

async def interact_with_{website}():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state='session.json')
        page = await context.new_page()
        
        await page.goto('https://{website}.com/dashboard', wait_until='networkidle')
        
        buttons = await page.locator('button:has-text("Approve")').all()
        for btn in buttons:
            await btn.click()
            await page.wait_for_load_state('networkidle')
            
        await browser.close()

asyncio.run(interact_with_{website}())""",
        "error": "Requires active session.json. Will fail if the targeted buttons are hidden behind a modal overlay or obscured by a z-index element."
    }
]

VARIABLES = {
    "website": ["stripe", "github", "hubspot", "salesforce", "jira", "aws"],
    "form_type": ["checkout", "registration", "support ticket", "invoice generation", "settings update"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    website = random.choice(VARIABLES["website"])
    form_type = random.choice(VARIABLES["form_type"])
    form_type_safe = form_type.replace(" ", "_")
    
    prompt = random.choice(scenario["intents"]).format(website=website, form_type=form_type)
    dialogue = random.choice(scenario["dialogue"]).format(website=website, form_type=form_type)
    
    steps = [step.format(website=website, form_type=form_type) for step in scenario["steps"]]
    code = scenario["code_template"].format(website=website, form_type=form_type, form_type_safe=form_type_safe)
    
    payload = {
        "browser_type": "chromium" if scenario["category"] != "Multi-Step Form" else "firefox",
        "auth_required": scenario["auth"],
        "steps": steps,
        "playwright_code": code,
        "error_handling": scenario["error"]
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