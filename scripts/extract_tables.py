import re
from pathlib import Path

tex_file = Path("research/arxiv_package/main.tex")
content = tex_file.read_text(encoding="utf-8")

tbl_pattern = re.compile(r"(\\begin\{table\*?\}.*?\\end\{table\*?\})", re.DOTALL)
tables = tbl_pattern.findall(content)

out = []
for idx, t in enumerate(tables):
    cap_match = re.search(r"\\caption\{(.*?)\}", t, re.DOTALL)
    lbl_match = re.search(r"\\label\{(.*?)\}", t)
    cap = cap_match.group(1).replace("\n", " ") if cap_match else "No caption"
    lbl = lbl_match.group(1) if lbl_match else f"table_{idx+1}"
    out.append(f"=== Table {idx+1}: {lbl} ===\nCaption: {cap}\n\n{t}\n\n")

Path("scripts/extracted_tables.txt").write_text("".join(out), encoding="utf-8")
print(f"Extracted {len(tables)} tables to scripts/extracted_tables.txt")
