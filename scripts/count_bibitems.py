import re
from pathlib import Path

tex_file = Path("research/arxiv_package/main.tex")
content = tex_file.read_text(encoding="utf-8")

bibitems = re.findall(r"\\bibitem\{(.*?)\}", content)
print(f"Total bibitems in main.tex: {len(bibitems)}")

bbl_file = Path("research/arxiv_package/main.bbl")
if bbl_file.exists():
    bbl_content = bbl_file.read_text(encoding="utf-8")
    bbl_items = re.findall(r"\\bibitem\{(.*?)\}", bbl_content)
    print(f"Total bibitems in main.bbl: {len(bbl_items)}")
