# Reproducibility archive for the [venue] revision

This directory contains the dependency-aware reanalysis and table-generation
artefacts for *A Component-Level Audit of No-Reference Quality Scoring in a
Multi-Video Summarization Pipeline*. The matching private GitHub release also
contains a byte-for-byte copy of the original reproducibility ZIP and the Git
bundle used to preserve the prediction-recording history.

## Primary outputs

- `major_revision_reanalysis.json`: KADID within-reference sensitivity,
  reference-block equivalence, topic-block in-domain intervals and hierarchical
  topic-to-cluster sensitivity results (10,000 resamples, seed 42).
- `p1401_metrics.json`: mapped PLCC, RMSE, confidence-interval-discounted RMSE,
  outlier ratio and analytic 95% intervals.
- `e2e_scores_major_revision.json`: cached per-segment scores used by the common
  42-cluster analysis.
- `e2e_sift.json`, `e2e_scores.json`, `dover42_scores.json` and
  `segment_word_counts.json`: non-media derived inputs for the in-domain
  reanalysis.
- `second_revision_reanalysis.json`: operation-level selection changes, DOVER
  technical-branch/raw/rank/range sensitivities, topic-block and hierarchical
  intervals, tie accounting, darkening/desaturation exclusions, sample-topic
  composition and descriptor-count changes for the 800 constructed pairs.
- `third_revision_reanalysis.json`: same-frame/same-pooling SIFT--BoVW versus
  LIQE control, topic-aware DOVER-T estimands and validation of the exact DOVER
  technical output on all 800 constructed pairs.
- `derived_data/same_frame_same_pooling_control.json` and
  `derived_data/dover_constructed_pairs.json`: raw checkpointed outputs for the
  two additional controls.
- `derived_data/synth_*.json`: machine-readable per-pair and per-ablation
  derived inputs for the constructed-degradation analyses.
- `derived_data/direction_alignment_audit.json`: signed reconstruction of the
  Main Table 2 values, storing raw SRCC and both method and target polarities;
  no absolute value is used.
- Release asset `registered_prediction_commit.bundle`: complete Git history
  containing the prediction-recording commit
  `9377c07ca080ac61c7cff80e0ff6c7507b6ebaba`. Its content and provenance note
  are also tracked directly on this repository's `main` branch.
- `registered_prediction_commit.md`: verification commands, provenance and the
  explicit limitation that Git metadata is not an external trusted timestamp.
- `PREDICTIONS_synthetic_indomain.md`: the prediction text preserved from the
  historical commit. Its original heading is retained verbatim and should not
  be read as evidence of an externally timestamped preregistration.
- `manifest.md`: table-to-script-to-data provenance map.

## Entry points

Run these commands from the `benchmark` repository after placing the
paper's public databases and derived broadcast metadata at the paths declared at
the top of each script:

```bash
python score_pyiqa_kadid_cache.py --model tres --output-name tres --batch-size 1 --workers 2
python score_pyiqa_segments_major_revision.py dbcnn hyperiqa arniqa --output-keys dbcnn hyperiqa arniqa
python reanalyze_major_revision.py
python reanalyze_second_revision.py
python same_frame_same_pooling_control.py
python dover_constructed_pairs.py
python reanalyze_operation_controls.py
python p1401_metrics.py
python verify_direction_alignment.py \
  --opinion-metrics p1401_metrics.json \
  --clive metrics_clive.json \
  --output direction_alignment_audit.json
```

The analysis scripts fail on incomplete caches rather than silently dropping
observations. `reanalyze_major_revision.py` records SHA-256 hashes of each KADID
cache in its JSON output. Dataset redistribution is governed by the original
database and HSMVideoSumm collection terms; this archive therefore contains
code and derived results, not restricted source media.

`reanalyze_second_revision.py` performs no neural-network inference. It reads
the archived per-segment/per-pair outputs, records their SHA-256 hashes, and
reconstructs the results added in the second revision. In particular, the
primary DOVER analysis uses the cached technical branch. The archived
`overall` field is the uncalibrated sum produced by the original scoring script;
it is retained only to reproduce the earlier sensitivity result and must not be
interpreted as the official standardised DOVER fusion.

After downloading the bundle release asset, the prediction-registration object
can be inspected without network access:

```bash
git clone registered_prediction_commit.bundle registered-predictions
git -C registered-predictions bundle verify \
  ../registered_prediction_commit.bundle
git -C registered-predictions show --stat \
  9377c07ca080ac61c7cff80e0ff6c7507b6ebaba
```

## Environment

The revision was executed with Python 3.12 in the existing project environment,
PyTorch/PyIQA on an NVIDIA RTX 4060, and the dependency bounds in
`requirements.txt`. Q-Align uses `q-future/one-align`, task `quality`, input
`image`, four-bit NF4 double quantisation and FP16 compute. DOVER uses the
official `DOVER.pth` checkpoint and `dover.yml` `val-l1080p` configuration.
The DOVER source revision is
`f1ddc96215bc7fbcf8f315c65d47905f339c3419`; the checkpoint SHA-256 is
`f4a42c0bbc94c94dd7409e7f40887d44c5c30314d1d09e7edf03cc35813b4838`.
Constructed-pair inference uses the raw technical branch, paired fragment seed
42 and a common 5-fps MP4 wrapper. The matched-input control gives both scorers
the same ten uniformly spaced 1-fps frames and arithmetic-mean pooling.

The original inference environment was not preserved as a fully pinned
lockfile. Consequently, the archive supports result reconstruction from cached
scores and source-level inspection of inference settings, but does not claim
bit-for-bit recreation of every neural-model inference. This limitation is
reported explicitly rather than replacing historical package versions with a
snapshot of the current workstation.

MANIQA was attempted with PyIQA 0.1.15.post2 and the `maniqa-kadid`
checkpoint. A single-image diagnostic completed, but the released 20-crop
inference path did not finish over the full 21,360-image three-database set
within the experiment window on the single 8-GB RTX 4060. It is recorded as
uncompleted and is excluded from screening, not counted as a failed method.
