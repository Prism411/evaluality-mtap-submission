# Major-revision response and change map

Manuscript: *A Component-Level Audit of No-Reference Quality Scoring in a
Multi-Video Summarization Pipeline*

This document maps the independent-review panel's findings to the revised
LaTeX, supplementary material and analysis code. It is an author-side change
record, not a claim that a formal editorial decision has already been received.

## Revision summary

- The central analytical claim is now explicitly conditional: the factorization
  identifies the two available channels and explains the observed count
  dominance; it is not presented as a universal impossibility theorem.
- KADID-10k sensitivity is computed within each reference image and
  block-bootstrapped over the 81 references.
- In-domain uncertainty is block-bootstrapped over 19 news topics, with a
  hierarchical topic-to-cluster sensitivity analysis.
- Every in-domain output claim is qualified as DOVER-estimated,
  Q-Align-estimated or reference-estimated. No human compositional preference is
  inferred.
- The cross-database training-overlap contrast and the keypoint-density partial
  correlations are explicitly descriptive rather than causal.
- The method-screening rule is identified as non-preregistered and operational;
  its mathematical justifications, quantifier, common cluster set and
  confirmed-pass definition were corrected.
- The first revision reduced the manuscript from 67 to 52 PDF pages. The
  canonical `main.tex` manuscript now contains 20 total pages after the second
  methodological revision; the former
  52-page source and PDF are preserved in
  `mtap-52pp-baseline-before-main-consolidation.zip`. Secondary detail is
  consolidated into a 14-page supplement containing Tables S1--S16.
- The separate graphical abstract was aligned with the revised evidence: three
  eligible methods, an operational rather than preregistered screen, bounded
  factorization claims and the reference-block KADID equivalence result.

## Major concerns

### 1. Scope of the factorization

**Action.** Rewrote the Abstract, Introduction, Results, Discussion and
Conclusion to distinguish the exact identity from its empirical interpretation.
The revised text states that descriptor count and mean IDF weight are the two
channels in the evaluated aggregation, that either could be informative under a
different extractor or distribution, and that the empirical evidence supports
count dominance only under the tested configurations.

**Files.** `main.tex`, `sec_intro.tex`, `sec_results.tex`,
`sec_discussion.tex`, `sec_conclusion.tex`.

### 2. Statistical unit of independence

**Action.** Replaced pooled KADID sensitivity with within-reference
correlations. The 95% intervals now use 10,000 block-bootstrap resamples over 81
reference images (seed 42). The 42-cluster application now resamples the 19 news
topics; a second analysis resamples clusters within sampled topics.

The SIFT+BoVW--keypoint-density comparison is also paired at the reference
level: the KADID-10k difference is +0.0024, with a block-bootstrap 95% interval
of [-0.0019,+0.0084], wholly inside the adopted +/-0.02 equivalence margin.
DBCNN and HyperIQA were rescored on the same 83 segment cache as every other
complete candidate; their topic-block floor intervals are [+0.274,+0.655] and
[+0.122,+0.606], respectively.

The second revision identified that the earlier +30.3-point DOVER contrast used
an uncalibrated raw sum of the technical and aesthetic branches. The primary
analysis now uses the technical branch: the LIQE-minus-SIFT contrast is +25.5
points, with topic-block interval [-12.1,+54.9] and hierarchical interval
[-17.2,+59.6]. Both cross zero, so the manuscript reports a positive point
estimate with uncertain population magnitude. The old raw-sum result is retained
only as a labelled sensitivity analysis.

**Files/data.** `sec_method.tex`, `sec_results.tex`, `sec_discussion.tex`,
`sec_conclusion.tex`, `supplementary.tex`, `major_revision_reanalysis.json`,
`second_revision_reanalysis.json`.

**Code.** `reanalyze_major_revision.py` and
`score_pyiqa_kadid_cache.py` in the quality-benchmark repository.

### 3. Human quality versus model-reference scores

**Action.** Replaced *delivered quality* and unqualified *raises quality* with
*reference-estimated output score*, *DOVER-estimated score* or
*Q-Align-estimated score*. The Abstract, application Results, Discussion and
Conclusion now state that no human visual-quality or compositional-preference
judgements were collected and that model agreement does not establish viewer
preference.

**Resolution chosen.** The optional new human experiment was not performed;
the corresponding human claim was removed.

### 4. Training exposure

**Action.** Recast the KonIQ--CLIVE--KADID comparison as an operational,
cross-database contrast. The revised manuscript lists the unmatched factors
(content, acquisition, annotation, model family and training recipe) and states
that the one-third contrast is not a causal estimate of training exposure.

**Resolution chosen.** Matched checkpoints with and without KonIQ were not
trained; the causal claim was removed.

### 5. Method-screening rule

**Action.** The rule is now called a *method-screening rule*, is explicitly
identified as non-preregistered, and uses operational rather than mathematical
justifications: mean sensitivity at least 0.50, more than 0.50 on at least 15 of
25 types (60% coverage), universal generalization of at least 0.65 on every
unseen database, and a common 42-cluster in-domain floor. A confirmed floor pass
requires the lower topic-block confidence limit to exceed zero. Point-estimate
passes are distinguished in the Methods.

Table S10 varies the generalization threshold, unseen-database quantifier,
distortion-type count and point-versus-confirmed floor. The complete-case set at
the adopted rule is LIQE, QualiCLIP and CLIP-IQA+; all three have confirmed
in-domain passes. ARNIQA and TReS are labelled partial and excluded from
complete-case claims; MANIQA is explicitly identified as not included because
the required axes could not be completed.

### 6. Interpretation of the keypoint-density control

**Action.** Replaced causal phrases such as *accounts for* with
*attenuates after conditioning on* and *shares rank variation with*. The revised
Methods and Discussion state that detectable keypoint density is narrower than
content density, may share causes with quality and may remove legitimate quality
signal. The arithmetic near-identity for BoVW is separated from the descriptive
partial correlations for the other methods.

### 7. Semantic substitutability within clusters

**Action.** Replaced *equally relevant* with a conditional pipeline statement:
once the detector treats candidates as redundant, the quality scorer acts as a
tie-breaker. The manuscript does not claim identical semantic utility and lists
the lack of a human substitutability audit as a limitation.

**Resolution chosen.** No new semantic audit was performed; the universal claim
was removed.

### 8. Supplement and benchmark auditability

**Action.** Added and compiled `supplementary.tex`/`supplementary.pdf` with
Tables S1--S16. The supplement now contains cluster definitions, worked
sensitivity examples, dependency-aware KADID sensitivity, the full P.1401
report, paradigm aggregation, ablation detail, the 15-cluster descriptive audit,
the screening sensitivity analysis, the registered-prediction audit, method
inventory and computational cost.

The P.1401 table now reports PLCC, RMSE, confidence-interval-discounted RMSE and
outlier ratio for both KonIQ-10k and KADID-10k; analytic 95% intervals are
preserved in the machine-readable output generated by `p1401_metrics.py`. TReS and ARNIQA are not described
as complete frontier coverage; their partial status is visible in the inventory
and screening table. TReS was run on all 10,125 KADID-10k images and reaches a
within-reference sensitivity of 0.620 (95% block interval [0.598,0.640]) on
18/25 distortion types. ARNIQA is additionally reported on the common
42-cluster application, where its floor interval crosses zero. MANIQA is
identified as outside the executed benchmark.

## Minor concerns

1. Frame accounting now separates 2,155 sampled original frames from 88,355
   total frame instances after the original plus 40 degraded versions.
2. The runtime comparison is now 44--152 times, not three orders of magnitude.
3. MUSIQ is correctly described as slower per frame than LIQE.
4. LIQE is no longer called strongest on every axis; QualiCLIP has the largest
   corrected mean sensitivity and LIQE the largest generalization margin.
5. NIQE is described as a training-free CPU option, not the cheapest responsive
   method.
6. Q-Align is described as approximately seven times faster than the deployed
   full path, not an order of magnitude.
7. Adoption language now acknowledges integration, memory, dependencies and GPU
   requirements.
8. Ethics approval now says three public image-quality databases.
9. The DINOv2 cross-reference was corrected.
10. Delta notation was standardized so losses and signed differences are not
    interchanged.
11. Direction-aligned signed rho is used where orientation matters; absolute
    SRCC is not treated as equivalent to it.
12. The custom statistic is named `kappa_uniform` and explicitly distinguished
    from Cohen's kappa.
13. The unsupported hundred-cluster power statement was removed.
14. Saturation is defined as `S' = clip(alpha S, 0, 255)` with all five factors;
    the other constructed-degradation parameters are also explicit.
15. The QualiCLIP arXiv identifier is protected in BibTeX as 2403.11176 and the
    version note is standardized.

## Reproducibility artefacts

The listed files are assembled into `mtap-revision-reproducibility.zip` for the
revision package. Public GitHub and Zenodo publication remain explicit
pre-acceptance author actions rather than being described as already complete.

- `major_revision_reanalysis.json`: dependency-aware numerical results,
  bootstrap metadata, seed and cache hashes.
- `reanalyze_major_revision.py`: KADID and in-domain resampling.
- `score_pyiqa_kadid_cache.py`: reproducible missing-cache generation.
- `score_pyiqa_segments_major_revision.py`: common 42-cluster segment scoring.
- `p1401_metrics.py` and `results/major_revision/p1401_metrics.json`: mapped
  P.1401 point estimates and analytic confidence intervals.
- `p1401_metrics.py`: PLCC, RMSE, RMSE*, outlier ratio and their 95% intervals
  from cached per-image scores.
- Recovered original harnesses: `synth_build.py`, `synth_score.py`,
  `synth_sift.py`, `synth_qalign.py`, `synth_cnnbovw.py`, `e2e_score.py`,
  `dover42.py`, `indomain_bovw.py`, `e2e_analyse.py`, `clive.py` and
  `newmethods_db.py`.

## Author actions still required before submission

- Confirm the CRediT/authorship statement with both authors.
- Create the promised versioned Zenodo record and replace the provisional data
  availability sentence with its DOI.
- If the human-level claim is restored in a later revision, run the paired
  within-cluster human study first; the current manuscript deliberately makes no
  such claim.
