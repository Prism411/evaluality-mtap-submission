# Evaluality MTAP submission

Private submission snapshot for **A Component-Level Audit of No-Reference
Quality Scoring in a Multi-Video Summarization Pipeline**.

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

The frozen PDFs contain 20 pages for the manuscript and 15 pages for the
supplement. The manuscript source of truth is `paper/main.tex`; no compact or
alternate manuscript route is used.

## Provenance

This snapshot was assembled from:

- manuscript repository commit
  `0bfb654b2be51cbc397546e7ae9fdde91ef3e309`;
- analysis repository commit
  `af9e8d50b48463efc8bb48d9ac52c35d9f973673`;
- prediction-registration commit
  `9377c07ca080ac61c7cff80e0ff6c7507b6ebaba`.

The prediction-registration object is published as the separate
`registered-predictions` branch and is also preserved in the release bundle.
See `reproducibility/registered_prediction_commit.md` for verification steps.

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

