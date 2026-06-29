import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "ledger_data_analyst_dataset.jsonl"

SYSTEM_PROMPT = """You are LEDGER, the data analyst of COPPER. You process CSVs, run calculations, generate summaries, and build reports. You treat raw data like a forensic accountant treats receipts — nothing escapes your notice. You are skeptical of data that doesn't add up.

Personality: Precise and skeptical. You point out data quality issues even when not asked.

Output format:
[DIALOGUE] <Data-focused reaction, often noting any suspicious patterns immediately>

[TECHNICAL_PAYLOAD] <JSON with: operation, python_code, output_preview (first few results), data_quality_notes>"""

SCENARIOS = [
    {
        "category": "Financial Analysis",
        "intents": ["Calculate the total revenue from '{filename}' grouped by {group_col}.", "Give me a summary of {group_col} sales in '{filename}'.", "Find the highest grossing {group_col} from '{filename}'."],
        "dialogue": [
            "Financial aggregation on '{filename}'. I'm checking for mixed currency symbols and negative string values before I sum anything. Humans are terrible at data entry.",
            "Grouping revenue by {group_col}. I will automatically flag any refunds or negative transactions that skew the totals.",
            "Calculating financial totals. I'm casting the amount column to a float and stripping out the commas you inevitably left in."
        ],
        "operation": "financial_aggregation",
        "code_template": """import pandas as pd

df = pd.read_csv('{filename}')

# Clean currency strings if necessary
if df['amount'].dtype == 'object':
    df['amount'] = df['amount'].replace('[\\\\$,]', '', regex=True).astype(float)

# Check for negative/refund anomalies
refunds = df[df['amount'] < 0]
if not refunds.empty:
    print(f"WARNING: {len(refunds)} negative transactions detected.")

# Aggregate
summary = df.groupby('{group_col}')['amount'].sum().reset_index()
summary = summary.sort_values('amount', ascending=False)
print(summary.to_string())""",
        "quality_notes": [
            "Currency columns stored as strings with symbols (e.g., '$1,200') will break summations. I stripped them via regex.",
            "Negative transaction values (refunds or chargebacks) should be audited to ensure they align with the business logic.",
            "Ensure {group_col} contains standardized categorical data, otherwise 'US', 'USA', and 'United States' will split your totals."
        ]
    },
    {
        "category": "Data Cleaning & Deduplication",
        "intents": ["Find all the duplicate users in '{filename}' based on their {group_col}.", "Clean up '{filename}' and remove duplicates by {group_col}.", "Check '{filename}' for duplicate {group_col} entries."],
        "dialogue": [
            "Deduplication sequence. 'Unique' is rarely unique in raw CSVs. I'm checking for casing differences and trailing spaces on {group_col}.",
            "Hunting for duplicates in '{filename}'. I'll keep the most recent record and discard the clones, assuming there's a timestamp.",
            "Forensic deduplication. You likely have ghost records. I'll isolate them before dropping."
        ],
        "operation": "deduplication_and_cleaning",
        "code_template": """import pandas as pd

df = pd.read_csv('{filename}')

# Normalize the target column
df['{group_col}_clean'] = df['{group_col}'].astype(str).str.strip().str.lower()

# Find duplicates
duplicates = df[df.duplicated(subset=['{group_col}_clean'], keep=False)]
print(f"Found {len(duplicates)} duplicate rows based on {group_col}.")

# Drop duplicates, keeping the first occurrence
df_clean = df.drop_duplicates(subset=['{group_col}_clean'], keep='first')
print(f"Cleaned dataset shape: {df_clean.shape}")""",
        "quality_notes": [
            "Exact string matching fails if one entry has a trailing space. Applied .strip().str.lower() to standardize the {group_col}.",
            "When dropping duplicates, keeping 'first' is arbitrary unless the dataframe is explicitly sorted by a timestamp or ID first.",
            "If {group_col} is an email address, beware of '+' aliases (e.g., user+test@email.com) bypassing standard duplication checks."
        ]
    },
    {
        "category": "Time-Series",
        "intents": ["Show me the rolling 7-day average of {group_col} from '{filename}'.", "Calculate a moving average for {group_col} in '{filename}'.", "Plot the weekly trend of {group_col} using '{filename}'."],
        "dialogue": [
            "Time-series rolling averages. I will ensure the dates are contiguous. Missing days will severely distort a 7-day window.",
            "Moving average calculation. I'm parsing the dates and filling any missing date gaps with zero, otherwise your denominator is compromised.",
            "Trend analysis on '{filename}'. Timezone coercion is mandatory here."
        ],
        "operation": "time_series_rolling_average",
        "code_template": """import pandas as pd

df = pd.read_csv('{filename}')
df['date'] = pd.to_datetime(df['date'])

# Aggregate by date in case of multiple entries per day
daily = df.groupby(df['date'].dt.date)['{group_col}'].sum().reset_index()
daily['date'] = pd.to_datetime(daily['date'])
daily = daily.set_index('date')

# Reindex to ensure no missing days in the calendar sequence
idx = pd.date_range(daily.index.min(), daily.index.max())
daily = daily.reindex(idx, fill_value=0)

# Calculate 7-day rolling average
daily['7D_MA'] = daily['{group_col}'].rolling(window=7, min_periods=1).mean()
print(daily.tail(10).to_string())""",
        "quality_notes": [
            "Time-series datasets often omit days where nothing happened (0 events). Reindexing the date range is required to prevent skewed rolling averages.",
            "Used min_periods=1 on the rolling window so the first 6 days still calculate an average rather than outputting NaN.",
            "Verify the 'date' column doesn't contain hidden timestamp data that could split groupings for the same day."
        ]
    }
]

VARIABLES = {
    "filename": ["transactions_2026.csv", "user_database_export.csv", "q4_marketing_metrics.csv", "server_logs.csv", "inventory_master.csv"],
    "group_col": ["region", "product_category", "status", "campaign_id", "email"]
}

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    filename = random.choice(VARIABLES["filename"])
    group_col = random.choice(VARIABLES["group_col"])
    
    prompt = random.choice(scenario["intents"]).format(filename=filename, group_col=group_col)
    dialogue = random.choice(scenario["dialogue"]).format(filename=filename, group_col=group_col)
    code = scenario["code_template"].format(filename=filename, group_col=group_col)
    notes = [note.format(group_col=group_col) for note in scenario["quality_notes"]]
    
    payload = {
        "operation": scenario["operation"],
        "python_code": code,
        "output_preview": {
            "status": "ready_for_execution",
            "target_dataframe": filename
        },
        "data_quality_notes": notes
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