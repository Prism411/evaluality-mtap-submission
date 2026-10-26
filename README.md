# Visual-selection operations and technical quality

Review package for **Do Visual-Selection Operations Track Technical Quality? A Controlled Audit for Multi-Video Summarization**, by Jader L. de Souza Gonçalves and Rudinei Goularte, ICMC, University of São Paulo.

This repository freezes the package prepared for *Multimedia Tools and Applications* on 25 October 2026. It is a submission candidate, not an accepted article. The manuscript's funding declaration is awaiting the authors' current confirmation. Journal policy is [single-blind review](https://link.springer.com/journal/11042/submission-guidelines): author identification is intentional.

**The current submission package is on `main`.** Older releases contain earlier snapshots and are not the matching version. The repository is currently private; a URL alone does not grant reviewers access.

## Read the article

- [Manuscript, 27 pages](submission/manuscript.pdf)
- [Online Resource 1: supplementary material, 54 pages](submission/ESM_1.pdf)
- [Title page](submission/title_page.pdf)
- [Cover letter](submission/cover_letter.pdf)
- [Editable LaTeX sources](source/)
- [Code, derived results and sample input](code_and_data/)

The PDFs are byte-identical to the prepared Downloads package. The paper audits the evaluated visual-selection implementations when reused for technical quality; it does not propose a new summarizer or infer failure of every method in a class.

## Quick verification: Python only, no GPU

Clone the default branch and verify the frozen artifacts:

```bash
git clone https://github.com/Prism411/evaluality-mtap-submission.git
cd evaluality-mtap-submission
python3 tools/verify_snapshot.py
```

The command validates all 361 file hashes and checks internal counts in two archived summaries. It does not modify the archived data. It reports 42 clusters, 21 implementations and 18 distinct representative-selection sets. These are checks of the frozen results, not a new execution of the experiments.

## Rebuild the PDFs

Requirements: Python 3, `pdflatex`, `bibtex`, `pdftotext`, `pdfinfo`, and the LaTeX packages imported by `source/*.tex` (TeX Live with recommended/extra packages and Latin Modern). The Springer class and bibliography style are supplied.

```bash
python3 tools/build_pdfs.py
```

The command compiles in isolated `build/` directories, checks the page counts and compares extracted text against all four supplied PDFs. It leaves `source/`, published PDFs and derived results unchanged. The supplied PDFs were visually checked locally, including the table S22 layout; text equality is not a substitute for visual inspection in a different TeX installation.

## Reproduction boundary

`code_and_data/` preserves all 313 entries of the submitted Online Resource 2. Its [historical README](code_and_data/README_ANONYMIZED.md) documents path/identity substitutions made for the earlier journal; it does not describe MTAP's review policy. [README_MTAP.txt](README_MTAP.txt) identifies this package.

The [analysis README](code_and_data/reproducibility/README.md) documents the experiment scripts and external requirements; [requirements.txt](code_and_data/reproducibility/requirements.txt) records dependency bounds, not a fully pinned environment. Historical paths in scripts may require adaptation. Some notes refer to earlier article titles or private releases and are retained as provenance. The quick verifier and PDF rebuild above are the tested entry points for this snapshot.

The archive contains derived scores and a **one-topic, three-video sample** (`bebe_real`). It does not include the full broadcast corpus, public IQA database images, model weights or all vendor implementations. The full inference pipeline has not been rerun for this packaging update. Run experimental scripts in a separate working copy after obtaining their documented inputs; do not run every legacy script indiscriminately over the frozen results.

The registered-prediction Git bundle is not in this snapshot. Its later public release remains described in the manuscript. Git author dates are not independent trusted timestamps.

## Provenance and changes

This snapshot derives from the MTAP package assembled on 21 October and checked on 25 October. The main manuscript text is unchanged. Packaging fixes load `xcolor` on the title page, clarify the three-video sample in the letter, move the complete S22 notes outside an oversized float, and add MTAP metadata to the archive. No measurement or scientific table entry was changed.

`MANIFEST.sha256` identifies the distributed PDFs, LaTeX files, code, data and sample media. The preparation audit is in [REVIEW-CHECKS.txt](REVIEW-CHECKS.txt). The funding confirmation is the remaining author declaration, not a failed compilation check.

## Rights and contact

No new blanket reuse licence is granted by this preparation. Data, media, Springer template files and third-party implementations retain their applicable rights and access conditions. Repository access does not itself change those rights.

Corresponding author: Jader L. de Souza Gonçalves, **jaderlouis@usp.br**. Co-author: Rudinei Goularte, **rudinei@icmc.usp.br**.
