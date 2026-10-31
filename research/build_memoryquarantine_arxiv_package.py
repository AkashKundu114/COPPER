#!/usr/bin/env python3
"""
build_memoryquarantine_arxiv_package.py
---------------------------------------
Packages the reconstructed MemoryQuarantine IEEE conference paper into a
standalone, submission-ready archive for arXiv / IEEE ICCECE 2027.
"""

import os
import shutil
import zipfile
import tarfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PKG_DIR = BASE_DIR / "memoryquarantine_package"
FIGS_OUT = PKG_DIR / "figures"


def main():
    print("=" * 70)
    print("Building Standalone MemoryQuarantine Submission Package")
    print("=" * 70)

    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True, exist_ok=True)
    FIGS_OUT.mkdir(parents=True, exist_ok=True)

    # 1. Copy core paper and bibliography
    shutil.copy2(BASE_DIR / "paper_revised.tex", PKG_DIR / "main.tex")
    shutil.copy2(BASE_DIR / "references.bib", PKG_DIR / "references.bib")
    if (BASE_DIR / "main.bbl").exists():
        shutil.copy2(BASE_DIR / "main.bbl", PKG_DIR / "main.bbl")

    # 2. Copy IEEE style and class dependencies
    for item in ["IEEEtran.cls", "orcidlink.sty"]:
        src = BASE_DIR / item
        if src.exists():
            shutil.copy2(src, PKG_DIR / item)

    for item in ["algorithm.sty", "algorithmic.sty"]:
        src = BASE_DIR / "resources" / item
        if src.exists():
            shutil.copy2(src, PKG_DIR / item)

    # 3. Copy all 8 publication figures
    fig_names = [
        "fig1_mq_dual_plane_architecture.png",
        "fig2_mq_attack_lifecycle.png",
        "fig3_mq_asr_tir_baselines.png",
        "fig4_mq_vector_breakdown.png",
        "fig5_mq_security_utility_tradeoff.png",
        "fig6_mq_epistemic_belief_dynamics.png",
        "fig7_mq_guardian_friction_roc.png",
        "fig8_mq_latency_distribution.png"
    ]

    for fname in fig_names:
        src = BASE_DIR / "figures" / fname
        if src.exists():
            shutil.copy2(src, FIGS_OUT / fname)
            print(f"  [COPIED FIGURE] {fname}")
        else:
            print(f"  [MISSING FIGURE] {fname}")

    # 4. Generate 00README.XXX for arXiv
    readme_content = """# MemoryQuarantine IEEE Conference Paper
# Target Venue: ICCECE 2027
# Primary File: main.tex
# Format: pdflatex
"""
    with open(PKG_DIR / "00README.XXX", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 5. Create zip and tar.gz
    zip_path = BASE_DIR / "memoryquarantine_submission.zip"
    tar_path = BASE_DIR / "memoryquarantine_submission.tar.gz"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(PKG_DIR):
            for file in files:
                p = Path(root) / file
                arcname = p.relative_to(PKG_DIR)
                zf.write(p, arcname)
    print(f"  [ARCHIVE] {zip_path.name} ({zip_path.stat().st_size / 1024:.1f} KB)")

    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(PKG_DIR, arcname="")
    print(f"  [ARCHIVE] {tar_path.name} ({tar_path.stat().st_size / 1024:.1f} KB)")

    print("=" * 70)
    print("MemoryQuarantine package successfully built!")
    print("=" * 70)


if __name__ == "__main__":
    main()
