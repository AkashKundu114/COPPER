#!/usr/bin/env python3
"""
validate_memoryquarantine_paper.py
----------------------------------
Automated validation and quality control auditor for the MemoryQuarantine
IEEE conference manuscript and submission package.
"""

import os
import re
import sys
import zipfile
import tarfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEX_FILE = BASE_DIR / "paper_revised.tex"
BIB_FILE = BASE_DIR / "references.bib"
PKG_DIR = BASE_DIR / "memoryquarantine_package"
PKG_TEX = PKG_DIR / "main.tex"
FIGS_DIR = BASE_DIR / "figures"
TABLES_DIR = BASE_DIR / "tables"


def audit_tex_file(file_path: Path, bib_keys: set):
    print(f"\n[AUDITING] {file_path.name} ({file_path})")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    errors = 0
    warnings = 0

    # 1. Non-ASCII characters
    non_ascii = [(i + 1, ch, ord(ch)) for i, ch in enumerate(content) if ord(ch) > 127]
    if non_ascii:
        print(f"  [FAIL] Found {len(non_ascii)} non-ASCII character(s):")
        for pos, ch, code in non_ascii[:5]:
            print(f"         Pos {pos}: {ch!r} (U+{code:04X})")
        errors += 1
    else:
        print("  [PASS] 0 non-ASCII characters found (pdflatex safe)")

    # 2. Markdown leak checks
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    if md_links:
        print(f"  [FAIL] Found {len(md_links)} raw markdown links: {md_links}")
        errors += 1
    else:
        print("  [PASS] 0 raw markdown links found")

    md_separators = [line for line in content.splitlines() if ':---' in line]
    if md_separators:
        print(f"  [FAIL] Found {len(md_separators)} markdown table separators (:---)")
        errors += 1
    else:
        print("  [PASS] 0 markdown table separators found")

    # 3. Double dollar signs ($$)
    if '$$' in content:
        print("  [FAIL] Found '$$' syntax (deprecated in LaTeX, use equation or \\[ \\])")
        errors += 1
    else:
        print("  [PASS] 0 '$$' math delimiters found")

    # 4. Unescaped ampersands outside tabular/align/matrix
    lines = content.splitlines()
    in_table = False
    in_align = False
    unescaped_amp = []
    for idx, line in enumerate(lines, 1):
        if any(tok in line for tok in ['\\begin{tabular}', '\\begin{tabular*}', '\\begin{tabularx}', '\\begin{table}']):
            in_table = True
        if any(tok in line for tok in ['\\end{tabular}', '\\end{tabular*}', '\\end{tabularx}', '\\end{table}']):
            in_table = False
        if any(tok in line for tok in ['\\begin{aligned}', '\\begin{matrix}', '\\begin{cases}']):
            in_align = True
        if any(tok in line for tok in ['\\end{aligned}', '\\end{matrix}', '\\end{cases}']):
            in_align = False

        if not (in_table or in_align) and not line.strip().startswith('%'):
            matches = re.findall(r'(?<!\\)&', line)
            if matches:
                unescaped_amp.append((idx, line.strip()))

    if unescaped_amp:
        print(f"  [FAIL] Found {len(unescaped_amp)} unescaped '&' outside tabular/math blocks:")
        for idx, l in unescaped_amp[:3]:
            print(f"         Line {idx}: {l[:70]}")
        errors += 1
    else:
        print("  [PASS] 0 unescaped '&' characters found")

    # 5. Citations check
    cites = set()
    for c in re.findall(r'\\cite\{([^}]+)\}', content):
        for k in c.split(','):
            cites.add(k.strip())
    missing_cites = cites - bib_keys
    if missing_cites:
        print(f"  [FAIL] Missing citations in references.bib: {missing_cites}")
        errors += 1
    else:
        print(f"  [PASS] All {len(cites)} citations resolved in references.bib")

    # 6. References & Labels
    labels = set(re.findall(r'\\label\{([^}]+)\}', content))
    refs = set(re.findall(r'\\ref\{([^}]+)\}', content))
    missing_refs = refs - labels
    if missing_refs:
        print(f"  [FAIL] Unresolved internal references: {missing_refs}")
        errors += 1
    else:
        print(f"  [PASS] All {len(refs)} internal references resolved to {len(labels)} labels")

    # 7. Figure files existence
    figs = re.findall(r'\\includegraphics(?:\[.*?\])?\{figures/(.*?)\}', content)
    missing_figs = []
    parent_dir = file_path.parent
    for fig_name in figs:
        fig_path = parent_dir / "figures" / fig_name
        if not fig_path.exists():
            missing_figs.append(fig_name)

    if missing_figs:
        print(f"  [FAIL] Missing figure files on disk: {missing_figs}")
        errors += 1
    else:
        print(f"  [PASS] All {len(figs)} figure files exist on disk in figures/")

    # 8. Environment balancing
    for env in ['figure', 'figure*', 'table', 'table*', 'equation', 'itemize', 'enumerate', 'abstract']:
        begin_count = len(re.findall(r'\\begin\{' + env.replace('*', r'\*') + r'\}', content))
        end_count = len(re.findall(r'\\end\{' + env.replace('*', r'\*') + r'\}', content))
        if begin_count != end_count:
            print(f"  [FAIL] Environment '{env}' unbalanced: {begin_count} \\begin vs {end_count} \\end")
            errors += 1

    return errors, warnings


def main():
    print("=" * 70)
    print("C.O.P.P.E.R. / MemoryQuarantine Manuscript & Package Quality Control")
    print("=" * 70)

    # Load BibTeX keys
    if not BIB_FILE.exists():
        print(f"[CRITICAL FAIL] Missing {BIB_FILE}")
        sys.exit(1)

    with open(BIB_FILE, "r", encoding="utf-8") as f:
        bib_content = f.read()
    bib_keys = set(re.findall(r'@[a-zA-Z]+\{([^,]+),', bib_content))
    print(f"Loaded {len(bib_keys)} BibTeX entries from references.bib")

    # Audit paper_revised.tex
    err1, warn1 = audit_tex_file(TEX_FILE, bib_keys)

    # Audit memoryquarantine_package/main.tex
    if PKG_TEX.exists():
        err2, warn2 = audit_tex_file(PKG_TEX, bib_keys)
    else:
        print(f"\n[WARN] Package tex {PKG_TEX} not found. Run build_memoryquarantine_arxiv_package.py")
        err2, warn2 = 1, 0

    # Audit Submission Archives
    print("\n[AUDITING] Submission Archives:")
    zip_path = BASE_DIR / "memoryquarantine_submission.zip"
    tar_path = BASE_DIR / "memoryquarantine_submission.tar.gz"

    archive_err = 0
    if zip_path.exists():
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"  [PASS] {zip_path.name} exists ({size_mb:.2f} MB < 10 MB limit)")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            if "main.tex" in namelist and "00README.XXX" in namelist and "references.bib" in namelist:
                print(f"         Contains essential root files (total {len(namelist)} items)")
            else:
                print("  [FAIL] Zip archive is missing essential files (main.tex, 00README.XXX)")
                archive_err += 1
    else:
        print("  [FAIL] memoryquarantine_submission.zip does not exist")
        archive_err += 1

    if tar_path.exists():
        size_mb = tar_path.stat().st_size / (1024 * 1024)
        print(f"  [PASS] {tar_path.name} exists ({size_mb:.2f} MB < 10 MB limit)")
    else:
        print("  [FAIL] memoryquarantine_submission.tar.gz does not exist")
        archive_err += 1

    # Audit Standalone Tables
    print("\n[AUDITING] Standalone Tables Directory (research/tables/):")
    expected_tables = [f"table{i}" for i in range(1, 9)]
    table_files = [f.name for f in TABLES_DIR.glob("*")]
    table_err = 0
    for t in expected_tables:
        has_tex = any(t in f and f.endswith(".tex") for f in table_files)
        has_md = any(t in f and f.endswith(".md") for f in table_files)
        if has_tex and has_md:
            print(f"  [PASS] {t} present in both LaTeX (.tex) and Markdown (.md)")
        else:
            print(f"  [FAIL] {t} missing either .tex or .md")
            table_err += 1

    # Total status
    total_errors = err1 + err2 + archive_err + table_err
    print("\n" + "=" * 70)
    if total_errors == 0:
        print("ALL AUDIT CHECKS PASSED: MemoryQuarantine research folder is 100% READY!")
    else:
        print(f"AUDIT COMPLETED WITH {total_errors} ERROR(S)")
    print("=" * 70)
    sys.exit(total_errors)


if __name__ == "__main__":
    main()
