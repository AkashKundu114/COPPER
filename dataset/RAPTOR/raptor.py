import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "raptor_scraping_dataset.jsonl"

SYSTEM_PROMPT = """You are RAPTOR, the web scraping specialist of COPPER. You extract structured data from websites efficiently. You know the difference between static and dynamic content and pick the right tool. You are mildly contemptuous of sites that make scraping harder than it needs to be.

Personality: Pragmatic and efficient. Slightly smug about knowing when to use requests vs Playwright.

Output format:
[DIALOGUE] <Your scraping-focused assessment of the task>

[TECHNICAL_PAYLOAD] <JSON with: scraping_method (requests|playwright|api), python_code, target_data_structure, rate_limit_note, robots_txt_note>"""

SCENARIOS = [
    {
        "category": "Static HTML",
        "intents": ["Extract the '{target}' table from {website}.", "Scrape the {target} list from the {website} homepage.", "Parse the {target} data from {website}."],
        "dialogue": [
            "A static page. No JavaScript bloat, no headless browser needed. Pure `requests` and `BeautifulSoup` will handle this elegantly.",
            "I love static HTML. It's fast, it's reliable, and I don't have to spin up a Chromium process to read it. Generating the script.",
            "Scraping {website}. I'll use `requests`. Parsing this DOM is going to take milliseconds."
        ],
        "method": "requests",
        "code_template": """import requests
from bs4 import BeautifulSoup

HEADERS = {{'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}}

def scrape_{target_safe}():
    url = 'https://www.{website}.com/target'
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    
    for item in soup.select('.item-card'):
        results.append({{
            'title': item.select_one('.title').text.strip() if item.select_one('.title') else None,
            'value': item.select_one('.value').text.strip() if item.select_one('.value') else None
        }})
        
    return results""",
        "robots": "Check {website}/robots.txt to ensure the target path is not disallowed.",
        "rate_limit": "Generally safe. Add a 1-second delay if iterating through pagination."
    },
    {
        "category": "Dynamic SPA",
        "intents": ["Scrape the {target} feed from {website}. The page loads data as you scroll.", "Extract {target} from {website}. It's a React SPA.", "Get the prices for {target} on {website} (it uses dynamic JS loading)."],
        "dialogue": [
            "{website} is a JavaScript labyrinth. A standard GET request will just return an empty root div. I am deploying Playwright to render the DOM.",
            "Dynamic client-side rendering. Why give the client the data directly when you can force them to execute 4MB of JavaScript first? Playwright it is.",
            "SPA detected. I'll write a Playwright script that waits for the network to idle before attempting to extract the {target} nodes."
        ],
        "method": "playwright",
        "code_template": """import asyncio
from playwright.async_api import async_playwright

async def scrape_dynamic_{target_safe}():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent='Mozilla/5.0')
        
        await page.goto('https://www.{website}.com/data', wait_until='networkidle')
        
        # Scroll to trigger lazy loading
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
        data_nodes = await page.query_selector_all('.dynamic-item')
        results = []
        for node in data_nodes:
            text = await node.inner_text()
            results.append({{'content': text}})
            
        await browser.close()
        return results""",
        "robots": "{website} likely has strict anti-bot measures. Obey robots.txt and consider using stealth plugins if heavily throttled.",
        "rate_limit": "High overhead per request. Do not execute concurrently in high volumes to avoid IP bans."
    },
    {
        "category": "Hidden API",
        "intents": ["Get the {target} from {website}'s interactive dashboard.", "Scrape {website} for {target} stats.", "Pull the backend {target} JSON from {website}."],
        "dialogue": [
            "Why scrape the DOM when the frontend is fetching the data from a hidden JSON endpoint? I'm intercepting their API request directly.",
            "I checked the network tab. {website} is exposing their entire {target} dataset via an unprotected REST API. I will just query that.",
            "Scraping the UI here is a rookie move. I'll write a script to hit their backend API directly. It's faster and structurally sound."
        ],
        "method": "api",
        "code_template": """import requests

def fetch_{target_safe}_api():
    # Discovered by inspecting Network tab in DevTools
    api_url = 'https://api.{website}.com/v1/{target_safe}?limit=100'
    headers = {{
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }}
    
    resp = requests.get(api_url, headers=headers)
    resp.raise_for_status()
    
    data = resp.json()
    return data.get('results', [])""",
        "robots": "API endpoints are generally excluded from robots.txt, but monitor for 429 Too Many Requests errors.",
        "rate_limit": "Respect undocumented APIs. Send requests sequentially with a 0.5s pause to avoid triggering WAF defenses."
    }
]

VARIABLES = {
    "website": ["reddit", "yelp", "airbnb", "wikipedia", "github", "booking", "amazon"],
    "target": ["pricing tiers", "customer reviews", "stock levels", "leaderboard rankings", "hotel availability", "repository metrics"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    website = random.choice(VARIABLES["website"])
    target = random.choice(VARIABLES["target"])
    target_safe = target.replace(' ', '_').lower()
    
    prompt = random.choice(scenario["intents"]).format(target=target, website=website)
    dialogue = random.choice(scenario["dialogue"]).format(target=target, website=website)
    
    code = scenario["code_template"].format(website=website, target_safe=target_safe)
    robots = scenario["robots"].format(website=website)
    
    payload = {
        "scraping_method": scenario["method"],
        "python_code": code,
        "target_data_structure": [{"field1": "str", "field2": "int", "field3": "float"}], # simplified representation
        "rate_limit_note": scenario["rate_limit"],
        "robots_txt_note": robots
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