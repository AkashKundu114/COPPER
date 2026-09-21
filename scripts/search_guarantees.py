from pathlib import Path
import re

content = Path("research/arxiv_package/main.tex").read_text(encoding="utf-8")
for idx, line in enumerate(content.splitlines()):
    if any(k in line.lower() for k in ["differential", "laplace", "dp noise", "guarantee"]):
        print(f"L{idx+1}: {line[:120]}")
