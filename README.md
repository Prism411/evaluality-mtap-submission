# Evaluality MTAP submission

Private submission snapshot for **Do Visual-Selection Heuristics Measure
Technical Quality? A Controlled Audit of Sixteen Operations Used in Video
Summarization**.

This repository contains the canonical manuscript source, the supplementary
material, revision responses, and the non-media reproducibility snapshot used
for the MTAP submission. It is private while the manuscript is under review.

## Repository layout

- `paper/`: canonical `main.tex`, section files, bibliography, Springer class,
  graphical abstract, and validated PDF.
- `supplement/`: supplementary source and validated PDF.
- `responses/`: author responses associated with the revision history.
- `reproducibility/`: scripts, cached derived results, provenance manifest, and
  checksums. Restricted source media, database images, model weights, and
  vendor trees are not redistributed.
  - `ops_da_literatura.py`: the reference implementation of the sixteen audited
    operations, with the direction each source declares for its own statistic.
    This is the module the constructed-pair and screening analyses call.
  - `derived_data/`: every measurement file a number in the manuscript depends on.
  - `paper_generators/`: the scripts that emit each table and figure from those
    files, so that no number in the body is typed by hand.
  - `paper_guards/`: the checks run before every build, each with a two-legged
    self-test that must approve the correct state and reject the reintroduced
    defect. `verifica_tudo.py` runs generators, build and guards in order.
### What runs from a clone, measured

Cloning this repository and running every script in `reproducibility/` with the
author's local paths made unreachable, **26 of the 40 scripts complete**. The
fourteen that do not are accounted for:

- **six** need database images or the source media that is not redistributed
  (KADID-10k and KonIQ-10k score tables, CLIVE, extracted frames);
- **five** need a vendor tree or a package that is not vendored here (`DOVER`,
  `moviepy`, a `transformers` version);
- **one**, `indomain_bovw.py`, reads an intermediate cluster file that no longer
  exists in any working copy, and is kept for provenance rather than for reuse;
- **one** is `verifica_tudo.py`, which belongs to the manuscript tree and needs
  `paper/` and `supplement/` beside it;
- **one** is a scoring stub that requires model weights.

⚠️ Scripts in the first two groups can still exit successfully while writing a
**partial** result when their inputs are missing: running the whole directory in
one pass let a two-cluster control file overwrite the shipped forty-two-cluster
one and break a downstream script. Run a script that needs media only in a tree
where that media is present.

`paper_guards/guarda_scripts_rodam_do_clone.py` keeps the first claim honest: it
clones the repository, blanks the author's paths, and runs the analysis scripts
that are supposed to be self-contained.

- `release-assets/`: local-only staging area for the complete submission and
  reproducibility archives. These files are attached to a private GitHub
  release rather than committed to Git.

## Build

The manuscript and supplement use Springer Nature's `sn-jnl` class. From the
repository root:

```bash
cd paper
latexmk -pdf main.tex

cd ../supplement
latexmk -pdf supplementary.tex
```

The frozen PDFs contain 30 pages for the manuscript and 31 pages for the
supplement. The manuscript source of truth is `paper/main.tex`; no compact or
alternate manuscript route is used.

## Provenance

This snapshot was assembled from:

- manuscript repository commit
  `0bfb654b2be51cbc397546e7ae9fdde91ef3e309`;
- analysis repository commit
  `af9e8d50b48463efc8bb48d9ac52c35d9f973673`;
- prediction-recording commit
  `9377c07ca080ac61c7cff80e0ff6c7507b6ebaba`.

The prediction-recording content and provenance note are tracked on `main`.
The original Git object and its parent history are preserved in the private
release asset `registered_prediction_commit.bundle`; see
`reproducibility/registered_prediction_commit.md` for verification steps.

## Reproducibility boundary

The archived JSON and CSV outputs are the source of truth for the reported
numerical results. The repository supports reconstruction of the reported
statistics and inspection of inference settings. It does not claim
bit-identical recreation of every neural-model inference because the original
inference environment was not preserved as a fully pinned lockfile.

Source databases and broadcast videos remain governed by their original access
terms. No restricted media or model weights are included here.

## Status and reuse

Private manuscript under review. No public DOI or reuse licence has yet been
assigned to this submission snapshot. Public release, archival deposition, and
licensing remain subject to author approval and the journal's review policy.
