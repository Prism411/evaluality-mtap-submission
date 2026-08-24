# Length-revision change map

Manuscript: *A Component-Level Audit of No-Reference Quality Scoring in a
Multi-Video Summarization Pipeline*

This record maps the second editorial assessment to the shortened manuscript. It
documents author-side changes; it does not imply acceptance or submission.

## Outcome

- Total manuscript length: 52 to 20 PDF pages after the second methodological
  revision added the DOVER-construct and scale-sensitivity results.
- Scientific body: the conclusion ends on page 16; declarations occupy the
  remainder of that page and the references run from pages 17--20.
- Supplement: 14 pages, Tables S1--S16, including the complete extractor and
  model-reference configurations.
- The former 52-page source and PDF are preserved in
  `mtap-52pp-baseline-before-main-consolidation.zip`.

## Central story retained

The shortened manuscript makes one claim chain central: the HSMVideoSumm
visual-quality stage uses a SIFT+BoVW+TF-IDF operation dominated by descriptor
count; that operation fails under known technical degradations; dependency-aware
screening identifies eligible NR-IQA alternatives; replacing the complete
visual-quality operation while holding all other pipeline stages fixed
materially changes segment selection.

The body retains the criterion--operation distinction, the two analytical
identities, the 19-extractor robustness result, within-reference KADID
sensitivity, the 800 constructed broadcast pairs, the common screening rule and
the 42-cluster substitution.

## Material transferred to the supplement

- Table S4: full ITU-T P.1401 triad.
- Tables S5--S6: paradigm aggregation and extractor-level ablation detail.
- Tables S7--S8: the separate 15-cluster human-annotated audit.
- Tables S9--S10: pooling variants and screening sensitivity.
- Tables S11--S12: application detail and the full registered-prediction audit.
- Tables S13--S14: method inventory and computational cost.
- Table S15: descriptive KonIQ--CLIVE--KADID and checkpoint-exposure contrasts.
- Table S16: descriptive attenuation after conditioning on detectable keypoint
  density.

Training-database overlap and keypoint-density conditioning are no longer
listed as principal contributions and are explicitly non-causal auxiliary
analyses.

## Main display set

- Figure 1: redesigned pipeline scope and evidence flow, with a single highlighted
  stage, two unambiguous vertical arrows and a uniform 2-by-2 evidence grid.
- Table 1: essential methods, supervision, polarity and audit role.
- Figure 2: score factorization and descriptor-count mechanism.
- Table 2: integrated sensitivity, generalization, in-domain floor and
  eligibility.
- Table 3: all 800 original--degraded broadcast comparisons.
- Table 4: common 42-cluster substitution and model-estimated output scores.

## Scientific safeguards retained

- The Conclusion now distinguishes the canonical formulation's statistical
  equivalence to keypoint density from the deployed formulation's near-exact
  sign-reversed large-database ordering.
- The factorization is not described as a universal impossibility theorem.
- KADID sensitivity is computed within reference and block-bootstrapped over
  source references.
- The application reports topic-block and hierarchical topic-to-cluster
  uncertainty; the latter crosses zero.
- Screening uses signed direction-aligned correlation, a universal unseen-
  database clause and a confirmed lower-bound in-domain floor.
- DOVER and Q-Align remain model references, not human ground truth.
- Redundancy-cluster membership is treated as a pipeline decision, not proof of
  identical semantic utility.
- No viewer preference or global summary-quality improvement is claimed.

## Files

- Canonical source: `main.tex`, `sec_intro.tex`, `sec_related.tex`,
  `sec_method.tex`, `sec_results.tex`, `sec_discussion.tex` and
  `sec_conclusion.tex`.
- Canonical build: `main.pdf`.
- Supplement: `supplementary.tex` and `supplementary.pdf`.
- First-revision traceability: `major_revision_response.md`.
- Reproducibility package: `mtap-revision-reproducibility.zip`.

## Validation completed

- `main.pdf`: 20 A4 pages; all fonts embedded.
- `supplementary.pdf`: 14 A4 pages; all fonts embedded.
- `mtap-52pp-baseline-before-main-consolidation.zip`: preserved 52-page baseline.
- No undefined citations, references or fatal LaTeX errors in the final builds.
- Visual inspection covered the title page, analytical figures, all four main
  tables, discussion/conclusion, the final reference page and Tables S15--S16.
- Source diff passes `git diff --check` for the canonical and revision files.

## Author decisions still required

- Confirm authorship, CRediT roles and any ORCID metadata.
- Create the promised versioned Zenodo record and insert its DOI.
- Confirm the canonical `ARTIGO-MTAP-EN.pdf` delivery after the final author
  read-through.
- A human within-cluster study is needed only if a later version restores a
  claim about viewer preference or compositional summary quality; the shortened
  manuscript makes no such claim.
