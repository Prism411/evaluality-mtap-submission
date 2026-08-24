# Response to the minor-revision review

We thank the reviewers for identifying the remaining notation,
cross-document-consistency and archive-provenance issues. No new human study is
claimed or required by the revised scope. The changes below preserve the
20-page main-paper limit.

## 1. Direction-aligned correlation

The Methods now defines `rho* = s_m s_y rho`, with separate signs for the
method and target. The text also states that KADID's released `dmos` field,
KonIQ MOS and CLIVE MOS are higher-is-better, whereas degradation level is
higher-is-worse. Supplementary Table S10 now reports “Minimum rho*” rather than
an absolute SRCC. The archive adds `verify_direction_alignment.py` and
`derived_data/direction_alignment_audit.json`; the audit reconstructs every
signed value reported in Main Table 2 without applying an absolute value.

## 2. Registered commit and immutable archive

Supplementary Table S12 now gives the full registered-prediction commit:
`9377c07ca080ac61c7cff80e0ff6c7507b6ebaba`. Because this object was not yet
reachable from the public default branch at freeze time, the submission archive
now contains `registered_prediction_commit.bundle`, its SHA-256 checksum and
offline verification commands. The public GitHub release and versioned Zenodo
record remain scheduled before final acceptance; no unverified DOI was
invented in the manuscript.

## 3. Method roles and DOVER outputs

The D/C/R/X/partial taxonomy is now identical in Main Table 1 and Supplementary
Tables S7 and S13. DINOv2 and feature-density measures are diagnostic (X),
SIFT+BoVW is deployed (D), NR-IQA alternatives are candidates (C), and Q-Align
is a reference (R). Legacy S6/S11 columns are explicitly labelled as the
uncalibrated raw DOVER technical-plus-aesthetic sum; DOVER-T remains the primary
technical-branch output.

## 4. Global-range estimand and Abstract

Methods now defines the cluster-weighted means `bar y`, `bar l` and `bar h`
before the ratio-of-means equation. The Abstract now states directly that the
DOVER technical output was reserved from screening and reached 97.6% accuracy
on the constructed pairs.

## 5. Q-Align cost

The categorical claim that Q-Align was “too costly” was removed. The paper now
reports the measured comparison: Q-Align was 13.7 times slower than LIQE in the
test setup and was therefore reserved as a reference model.

## 6. Direct prior work

Related Work now cites Jeong, Yoo and Cho's quality-aware static video
summarization method and distinguishes prior use of contrast, blur and skew
from the present mechanistic construct-validation audit.

## 7. MANIQA coverage

The supplement now records PyIQA 0.1.15.post2, the `maniqa-kadid` checkpoint,
the successful single-image diagnostic and the practical boundary: the released
20-crop inference path over all 21,360 images did not finish within the
experiment window on the single 8-GB RTX 4060. MANIQA is therefore labelled
uncompleted and excluded from screening, not treated as a failed candidate.

## 8. Human evaluation

No human compositional evaluation was added. The manuscript continues to state
that model-reference output is not viewer preference and that no improvement
in viewer experience or population-level output effect is established.
