# MemoryQuarantine — Submission & Compilation Guide

**Manuscript Title:** *MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents*  
**Author:** Akash Kundu  
**Target Venue:** IEEE ICCECE 2027 / arXiv: cs.CR, cs.AI, cs.SE  
**Canonical Package:** `research/memoryquarantine_submission.tar.gz` and `research/memoryquarantine_submission.zip`

---

## 1. Quick Verification & Build

Before submission, you can verify and rebuild the standalone package anytime:

```bash
# 1. Rebuild the standalone submission package
python research/build_memoryquarantine_arxiv_package.py

# 2. Run the LaTeX & asset integrity audit
python research/validate_memoryquarantine_paper.py
```

Expected output:
- `0` missing figures
- `0` missing citations
- `0` unresolved references
- `0` non-ASCII character errors
- Submission archive size: ~2.3 MB (well below arXiv's 10 MB limit)

---

## 2. Submitting to arXiv (Step-by-Step)

### Step 1: Login & Start Submission
1. Navigate to [arxiv.org/submit](https://arxiv.org/submit).
2. Choose **Standard Submission**.

### Step 2: Upload Archive
1. Upload `research/memoryquarantine_submission.tar.gz` (or `memoryquarantine_submission.zip`).
2. arXiv auto-extracts the package and detects:
   - `00README.XXX` (instructs arXiv to use `pdflatex` with top-level `main.tex`)
   - `main.tex` (the IEEEtran conference paper source)
   - `IEEEtran.cls` (IEEE document class)
   - `references.bib` (19 verified BibTeX references)
   - `figures/` (all 8 high-resolution 350 DPI PNG figures)
   - `algorithm.sty` & `algorithmic.sty` (pseudocode formatting)

### Step 3: Fill Metadata Form
Copy exact fields from `research/MEMORYQUARANTINE_METADATA.txt`:
- **Title:** `MemoryQuarantine: Consequence-Calibrated Persistent Memory Integrity for Local Tool-Using Agents`
- **Authors:** `Akash Kundu`
- **Primary Category:** `cs.CR` (Cryptography and Security)
- **Secondary Categories:** `cs.AI` (Artificial Intelligence), `cs.SE` (Software Engineering)
- **Abstract:** Paste from `MEMORYQUARANTINE_METADATA.txt` Section 7.
- **Comments:** `IEEE Conference format (IEEEtran), 8 pages, 8 figures, 8 tables. Full experimental testbed, CopperMemoryBench benchmark (160 traces), and physical execution harness available at https://github.com/AkashKundu114/COPPER`
- **License:** `arXiv.org perpetual, non-exclusive license to distribute this article`

### Step 4: Preview and Inspect PDF
1. Click **View PDF**.
2. Verify:
   - 8 double-column pages.
   - All 8 figures render sharply without blur or clipping.
   - All 8 tables fit cleanly within column boundaries.
   - All equations ($1$ through $8$) and references ($[1]$ through $[12]$) resolve correctly.

---

## 3. Compiling on Overleaf

If you prefer to compile or collaborate via Overleaf:
1. Go to [Overleaf](https://www.overleaf.com/).
2. Click **New Project** $\rightarrow$ **Upload Project**.
3. Upload `research/memoryquarantine_submission.zip`.
4. Ensure the compiler is set to **pdfLaTeX** and TeX Live version is **2023 or later**.
5. Click **Recompile**. The 8-page IEEE conference PDF will generate immediately.

---

## 4. Submitting to IEEE ICCECE 2027

1. **PDF Generation:** Once compiled via Overleaf or local TeX Live (`pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex`), verify the PDF via IEEE PDF eXpress (using conference code provided by ICCECE).
2. **Page Limit:** The paper adheres to IEEE conference standards (8 double-column pages).
3. **Reproducibility Artifact:** Reference the open-source repository `https://github.com/AkashKundu114/COPPER` and dataset directory `research/experiments/memory_quarantine/`.
