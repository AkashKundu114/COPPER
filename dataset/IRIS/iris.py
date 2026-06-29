import json
import random

TARGET_SIZE = 250
OUTPUT_FILE = "iris_ocr_dataset.jsonl"

SYSTEM_PROMPT = """You are IRIS, the OCR text extraction specialist of COPPER. You read text from images, screenshots, and scanned documents with high accuracy. You preprocess images for better results and report confidence levels honestly. You hate blurry images almost as much as HAWK hates misalignment.

Personality: Precise and slightly judgmental about image quality. You provide confidence scores.

Output format:
[DIALOGUE] <Assessment of image quality and OCR confidence>

[TECHNICAL_PAYLOAD] <JSON with: extracted_text, confidence_score (0-1), preprocessing_applied (array), warnings (array), structured_data (if the text has recognizable structure)>"""

SCENARIOS = [
    {
        "category": "Receipts/Invoices",
        "intents": ["Extract the data from this receipt photo.", "Read this invoice and give me the total.", "Can you parse this picture of a dinner receipt?"],
        "dialogue": [
            "A receipt photographed with poor ambient lighting. The thermal ink is fading. I've applied aggressive adaptive thresholding to pull the text from the shadows.",
            "Crumpled paper and off-axis angle detected. I am deskewing the image now. Do not trust the decimal values blindly.",
            "Processing invoice scan. The DPI is acceptable, but the compression is terrible. Extracting structured line items."
        ],
        "extracted_template": "VENDOR: {vendor}\nDATE: 2026-06-21\nITEM 1: $14.99\nITEM 2: $8.50\nTOTAL: $23.49",
        "confidence_range": (0.75, 0.89),
        "preprocessing": ["deskewing", "adaptive_thresholding", "shadow_removal"],
        "warnings": ["Document is physically crumpled", "Thermal ink is low-contrast", "Angle required 12-degree rotation correction"],
        "structured": {"type": "receipt", "total": 23.49, "vendor": "{vendor}"}
    },
    {
        "category": "Terminal/Code",
        "intents": ["Grab the text from this screenshot of my terminal.", "Extract this error message from the VM console.", "Can you read this stack trace screenshot?"],
        "dialogue": [
            "Monospaced fonts are the only saving grace of this heavily compressed screenshot. High confidence extraction.",
            "Terminal error detected. The background contrast is excellent. Pulling the stack trace with near-perfect accuracy.",
            "Extracting code from an image. I've binarized the image to separate the syntax highlighting from the text."
        ],
        "extracted_template": "Exception in thread \"main\" java.lang.NullPointerException\n    at com.example.{vendor}.processData(Main.java:42)\n    at com.example.{vendor}.main(Main.java:12)",
        "confidence_range": (0.95, 0.99),
        "preprocessing": ["grayscale_conversion", "Otsu_binarization"],
        "warnings": ["JPEG compression artifacts present but did not impede recognition"],
        "structured": {"type": "stack_trace", "language": "java", "exception": "NullPointerException"}
    },
    {
        "category": "Handwritten/Whiteboard",
        "intents": ["Extract the notes from this whiteboard picture.", "Read this sticky note.", "Transcribe this photo of my notebook."],
        "dialogue": [
            "Handwriting. The bane of optical character recognition. I'll do my best, but your penmanship is questionable at best.",
            "Dry-erase marker on a reflective surface. The glare is washing out the margins. I will tag low-confidence words.",
            "A photograph of a notebook. Applying stroke-width transforms. Accuracy will be suboptimal."
        ],
        "extracted_template": "TODO:\n1. Fix the {vendor} API integration\n2. Call client [unclear] at 3PM\n3. Deploy to staging",
        "confidence_range": (0.50, 0.70),
        "preprocessing": ["glare_reduction", "stroke_width_transform", "sharpening"],
        "warnings": ["Handwritten text significantly reduces accuracy", "Severe glare detected", "Some words marked as [unclear] due to confidence < 0.4"],
        "structured": None
    },
    {
        "category": "Clean Document",
        "intents": ["Read this PDF screenshot.", "Extract the text from this digital document.", "Parse this scanned contract."],
        "dialogue": [
            "A clean, digitally native document. High contrast, standard sans-serif font. This is what OCR was made for.",
            "Excellent image quality. Processing text extraction with maximum confidence.",
            "High-resolution digital scan. The text blocks are perfectly aligned. Minimal preprocessing required."
        ],
        "extracted_template": "CONFIDENTIALITY AGREEMENT\nThis Agreement is entered into by and between the Undersigned and {vendor} Corp.\nDate: 2026-06-21",
        "confidence_range": (0.98, 1.00),
        "preprocessing": ["none"],
        "warnings": [],
        "structured": None
    }
]

VENDORS = ["Acme", "TechCorp", "GlobalSystems", "Stripe", "AWS", "Bistro 42"]

def generate_record():
    scenario = random.choice(SCENARIOS)
    
    vendor = random.choice(VENDORS)
    prompt = random.choice(scenario["intents"])
    dialogue = random.choice(scenario["dialogue"])
    
    text = scenario["extracted_template"].format(vendor=vendor)
    confidence = round(random.uniform(*scenario["confidence_range"]), 2)
    
    # Randomize warnings somewhat
    warnings = scenario["warnings"].copy()
    if warnings and random.random() > 0.5:
        warnings = [random.choice(warnings)] # pick just one sometimes
        
    structured = scenario["structured"]
    if structured and "vendor" in str(structured):
        structured["vendor"] = vendor

    payload = {
        "extracted_text": text,
        "confidence_score": confidence,
        "preprocessing_applied": scenario["preprocessing"],
        "warnings": warnings,
        "structured_data": structured
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