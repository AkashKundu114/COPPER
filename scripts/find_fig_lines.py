import re
from pathlib import Path

tex_file = Path("research/arxiv_package/main.tex")
lines = tex_file.read_text(encoding="utf-8").splitlines()

for idx, line in enumerate(lines):
    if "\\includegraphics" in line or "\\begin{figure" in line or "\\caption" in line and "fig" in line.lower():
        print(f"L{idx+1}: {line[:120]}")
