import re
from pathlib import Path

tex_file = Path("research/arxiv_package/main.tex")
content = tex_file.read_text(encoding="utf-8")

print("=" * 80)
print("VERIFICATION OF RESEARCH/ARXIV_PACKAGE/MAIN.TEX")
print("=" * 80)

# Check 1: Raw markdown in tables
tbl_matches = re.findall(r"\\begin\{tabular.*?\}.*?\\end\{tabular.*?\}", content, re.DOTALL)
has_markdown_in_tables = False
for idx, tbl in enumerate(tbl_matches):
    if "**" in tbl:
        print(f"[FAIL] Found '**' in Table {idx+1}")
        has_markdown_in_tables = True

if not has_markdown_in_tables:
    print("[PASS] Zero raw markdown '**' found inside LaTeX tables!")

# Check 2: Figure labels & references
labels = set(re.findall(r"\\label\{(fig:.*?)\}", content))
refs = set(re.findall(r"\\ref\{(fig:.*?)\}", content))

print(f"\nFigure Labels Defined ({len(labels)}):")
for l in sorted(labels):
    print(f"  - {l}")

missing_fig_labels = refs - labels
if missing_fig_labels:
    print(f"[FAIL] Missing figure labels: {missing_fig_labels}")
else:
    print("[PASS] All referenced figure labels exist!")

# Check 3: Table labels & references
t_labels = set(re.findall(r"\\label\{(tab:.*?)\}", content))
t_refs = set(re.findall(r"\\ref\{(tab:.*?)\}", content))

print(f"\nTable Labels Defined ({len(t_labels)}):")
for l in sorted(t_labels):
    print(f"  - {l}")

missing_tab_labels = t_refs - t_labels
if missing_tab_labels:
    print(f"[FAIL] Missing table labels: {missing_tab_labels}")
else:
    print("[PASS] All referenced table labels exist!")

# Check 4: Check key reconciled numbers
print("\n--- Numerical Reconciliations Check ---")
for kw in [
    "515 passing automated tests",
    "62 peer-reviewed papers and preprints (2023--2026) across 10 research axes",
    "46.98~GiB (50.45~GB decimal) on disk",
    "6.38 GB & 6.38 GB",
    "8.12~GB Physical Addressable Ceiling",
    r"[99.09\%, 100.0\%]",
    "~90,900 QPS",
]:
    found = kw in content
    print(f"  [{'PASS' if found else 'FAIL'}] '{kw}' in main.tex")

print("=" * 80)
