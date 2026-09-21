import re
from pathlib import Path

tex_file = Path("research/arxiv_package/main.tex")
if not tex_file.exists():
    tex_file = Path("research/paper.tex")

content = tex_file.read_text(encoding="utf-8")

print(f"Inspecting {tex_file}: Total lines = {len(content.splitlines())}")

# Find all figures
fig_pattern = re.compile(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", re.DOTALL)
figures = fig_pattern.findall(content)
print(f"Total Figures found: {len(figures)}")

for idx, f in enumerate(figures):
    cap_match = re.search(r"\\caption\{(.*?)\}", f, re.DOTALL)
    lbl_match = re.search(r"\\label\{(.*?)\}", f)
    img_match = re.search(r"\\includegraphics.*?\{(.*?)\}", f)
    cap = cap_match.group(1).replace("\n", " ") if cap_match else "No caption"
    lbl = lbl_match.group(1) if lbl_match else "No label"
    img = img_match.group(1) if img_match else "No image"
    print(f"\nFigure {idx+1}:")
    print(f"  Label: {lbl}")
    print(f"  Image: {img}")
    print(f"  Caption: {cap[:120]}...")

# Find all tables
tbl_pattern = re.compile(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", re.DOTALL)
tables = tbl_pattern.findall(content)
print(f"\nTotal Tables found: {len(tables)}")

for idx, t in enumerate(tables):
    cap_match = re.search(r"\\caption\{(.*?)\}", t, re.DOTALL)
    lbl_match = re.search(r"\\label\{(.*?)\}", t)
    cap = cap_match.group(1).replace("\n", " ") if cap_match else "No caption"
    lbl = lbl_match.group(1) if lbl_match else "No label"
    print(f"\nTable {idx+1}:")
    print(f"  Label: {lbl}")
    print(f"  Caption: {cap[:120]}...")
