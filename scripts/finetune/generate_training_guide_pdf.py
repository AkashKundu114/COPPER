"""
Generate a PDF from the COPPER Training Guide using only the Python
standard library (no third-party deps required).

Uses reportlab-free approach: writes a structured PDF with headers,
tables, and code blocks using fpdf2 if available, otherwise falls
back to a clean plaintext-to-PDF converter.
"""

import subprocess
import sys
import os

def install_fpdf2():
    """Install fpdf2 for PDF generation."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "-q"])

def generate_pdf():
    try:
        from fpdf import FPDF
    except ImportError:
        install_fpdf2()
        from fpdf import FPDF

    def sanitize(text):
        """Replace Unicode chars that latin-1 can't encode."""
        replacements = {
            "\u2014": "--", "\u2013": "-", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*",
            "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
            "\u2502": "|", "\u2500": "-", "\u2550": "=",
            "\u250c": "+-", "\u2510": "-+", "\u2514": "+-", "\u2518": "-+",
            "\u251c": "+-", "\u2524": "-+", "\u252c": "-+-", "\u2534": "-+-",
            "\u253c": "-+-",
            "\u2713": "OK", "\u2714": "OK", "\u2715": "X", "\u2716": "X",
            "\u2717": "X", "\u2718": "X",
            "\u2705": "[OK]", "\u274c": "[X]", "\u26a0": "[!]",
            "\u00b7": ".", "\u2248": "~", "\u2265": ">=", "\u2264": "<=",
            "\u00a0": " ",
            "\u2611": "[x]", "\u2610": "[ ]",
            "\u25cf": "*", "\u25cb": "o", "\u25a0": "#", "\u25a1": "[ ]",
            "\u2588": "#", "\u2591": ".",
            "\u00d7": "x",
            "\u2019": "'",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        # Catch any remaining non-latin1 chars
        result = []
        for ch in text:
            try:
                ch.encode("latin-1")
                result.append(ch)
            except UnicodeEncodeError:
                result.append("?")
        return "".join(result)

    GUIDE_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "COPPER_Training_and_Deployment_Guide.txt")
    OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "COPPER_Training_and_Deployment_Guide.pdf")

    # Read the guide
    with open(GUIDE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Cover Page ──
    pdf.add_page()
    pdf.set_fill_color(9, 9, 11)  # zinc-950
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(80)
    pdf.cell(0, 20, "C.O.P.P.E.R", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(161, 161, 170)  # zinc-400
    pdf.cell(0, 10, "Coordinated Operational Pipeline for Parallel", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "Execution and Routing", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "Cloud GPU Training &", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 12, "Model Deployment Guide", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(15)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(113, 113, 122)  # zinc-500
    pdf.cell(0, 8, "Version 2.0  |  July 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "50 Specialist Agents + 1 Orchestrator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Optimized for RTX 5050 (8GB VRAM) + Ollama", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(30)
    pdf.set_draw_color(63, 63, 70)  # zinc-700
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(82, 82, 91)  # zinc-600
    pdf.cell(0, 6, "Covers: Vast.ai | RunPod | Google Colab | Local RTX 5050", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "LoRA Training | GGUF Quantization | Ollama Integration", align="C", new_x="LMARGIN", new_y="NEXT")

    # ── Table of Contents Page ──
    pdf.add_page()
    pdf.set_fill_color(9, 9, 11)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    toc_items = [
        ("1", "Overview & Architecture"),
        ("2", "Cloud GPU Provider Comparison"),
        ("3", "Step-by-Step: Training on RunPod"),
        ("4", "Step-by-Step: Training on Vast.ai"),
        ("5", "Step-by-Step: Training on Google Colab (Free)"),
        ("6", "Local Training on RTX 5050 8GB"),
        ("7", "Converting LoRA Adapters to GGUF (Q4)"),
        ("8", "Loading Models into Ollama"),
        ("9", "Integrating Models into the COPPER Project"),
        ("10", "Troubleshooting"),
        ("11", "Cost Summary & Recommendations"),
    ]

    pdf.set_font("Helvetica", "", 13)
    for num, title in toc_items:
        pdf.set_text_color(161, 161, 170)
        pdf.cell(15, 10, f"  {num}.", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")

    # ── Content Pages ──
    pdf.add_page()
    pdf.set_fill_color(9, 9, 11)
    pdf.rect(0, 0, 210, 297, "F")

    # Pre-sanitize the entire content
    content = sanitize(content)
    lines = content.split("\n")
    in_table = False

    for line in lines:
        # Check if we need a new page
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_fill_color(9, 9, 11)
            pdf.rect(0, 0, 210, 297, "F")

        stripped = line.strip()

        # Section headers (lines starting with # followed by ═ or ─)
        if stripped.startswith("# =") or stripped.startswith("# -") or stripped.startswith("# =="):
            # Draw a thin separator line
            pdf.set_draw_color(63, 63, 70)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(5)
            continue

        # Main title lines
        if stripped.startswith("#  SECTION"):
            section_text = stripped.replace("#  SECTION ", "Section ").replace("#", "")
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(255, 255, 255)
            pdf.multi_cell(0, 8, sanitize(section_text.strip()))
            pdf.ln(3)
            continue

        if stripped.startswith("#  COPPER"):
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(255, 255, 255)
            pdf.multi_cell(0, 9, sanitize(stripped.replace("#  ", "").strip()))
            pdf.ln(2)
            continue

        if stripped.startswith("#"):
            header_text = stripped.lstrip("#").strip()
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(255, 255, 255)
            pdf.multi_cell(0, 8, sanitize(header_text))
            pdf.ln(2)
            continue

        # Table lines (box drawing characters)
        if any(c in stripped for c in ["+-", "|--", "|  "]):
            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(200, 200, 200)
            safe = sanitize(stripped)
            if len(safe) > 100:
                safe = safe[:97] + "..."
            pdf.cell(0, 4, safe, new_x="LMARGIN", new_y="NEXT")
            continue

        # STEP lines
        if stripped.startswith("STEP "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(255, 255, 255)
            pdf.multi_cell(0, 6, sanitize(stripped))
            pdf.ln(1)
            continue

        # IMPORTANT / WARNING lines
        if stripped.startswith("IMPORTANT:") or stripped.startswith("LIMITATIONS:") or stripped.startswith("WHY "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(255, 200, 100)
            pdf.multi_cell(0, 6, sanitize(stripped))
            pdf.ln(1)
            continue

        # METHOD lines
        if stripped.startswith("METHOD "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(200, 200, 255)
            pdf.multi_cell(0, 7, sanitize(stripped))
            pdf.ln(1)
            continue

        # TOTAL / ALTERNATIVE / RECOMMENDED lines
        if stripped.startswith("TOTAL:") or stripped.startswith("ALTERNATIVE") or stripped.startswith("RECOMMENDED"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(130, 255, 130)
            pdf.multi_cell(0, 6, sanitize(stripped))
            pdf.ln(1)
            continue

        # Code-like lines (indented with spaces, starting with commands)
        if (line.startswith("  ") and len(stripped) > 0 and not stripped.startswith("•")):
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(180, 220, 180)
            # Ensure the line fits
            safe_line = line.rstrip()
            if len(safe_line) > 95:
                safe_line = safe_line[:92] + "..."
            pdf.cell(0, 4.5, sanitize(safe_line), new_x="LMARGIN", new_y="NEXT")
            continue

        # Bullet points
        if stripped.startswith("•") or stripped.startswith("-"):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(200, 200, 200)
            pdf.multi_cell(0, 5.5, sanitize("  " + stripped))
            pdf.ln(1)
            continue

        # Empty lines
        if not stripped:
            pdf.ln(3)
            continue

        # Regular text
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(200, 200, 200)
        pdf.multi_cell(0, 5.5, sanitize(stripped))
        pdf.ln(1)

    # ── Final page: Quick Reference Card ──
    pdf.add_page()
    pdf.set_fill_color(9, 9, 11)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "Quick Reference Card", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    quick_ref = [
        ("Generate datasets (CPU)", "python generate_all_agents.py --size 1500 --outdir ./dataset"),
        ("Generate COPPER dataset", "python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER"),
        ("Train all (cloud 24GB)", "bash launch_finetune_all.sh 24gb"),
        ("Train one agent (8GB)", "python finetune_agent.py --agent AXIS --batch_size 1 --grad_accum 16 --max_seq_len 512"),
        ("Convert to GGUF Q4", "model.save_pretrained_gguf('agent-q4', tokenizer, quantization_method='q4_k_m')"),
        ("Register in Ollama", "ollama create copper-axis -f axis.Modelfile"),
        ("Test model", "ollama run copper-axis 'Hello'"),
        ("Monitor GPU", "watch -n 2 nvidia-smi"),
    ]

    for label, cmd in quick_ref:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(161, 161, 170)
        pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(180, 220, 180)
        pdf.cell(0, 6, f"  {cmd}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Save
    pdf.output(OUTPUT_PATH)
    print(f"\n[OK] PDF generated successfully!")
    print(f"   Location: {os.path.abspath(OUTPUT_PATH)}")
    print(f"   Size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    generate_pdf()
