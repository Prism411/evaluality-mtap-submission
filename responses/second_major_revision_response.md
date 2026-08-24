# Response to the second major-revision review

Manuscript: *A Component-Level Audit of No-Reference Quality Scoring in a
Multi-Video Summarization Pipeline*

This author-side change map addresses the review of the 19-page compact
manuscript. It records completed changes and explicitly distinguishes analyses
that were rerun from the human-preference claim that remains outside the study.

## Summary of the revision

- The intervention is now called a **visual-quality operation substitution**.
  The manuscript states that internal frame sampling, scoring and pooling differ
  between operations; only the other pipeline stages are held fixed.
- A new same-frame/same-pooling control gives both SIFT+BoVW and LIQE the same
  ten uniformly spaced frames. They still select differently in 16/42 clusters;
  the DOVER-T global-range contrast is +27.1 points with positive topic-block
  and hierarchical intervals.
- The primary output reference is now the **raw technical branch of DOVER**.
  The earlier 30.3-point result is identified as an uncalibrated sum of the raw
  technical and aesthetic branches and is retained only as sensitivity analysis.
- The exact DOVER technical output used downstream was additionally evaluated
  on all 800 constructed pairs: 97.6% accuracy, segment-block 95% CI
  [96.1%, 99.0%], and no ties.
- The DOVER result is reported under four estimands: raw score, global
  achievable range, mean within-cluster position and selection of the
  within-cluster maximum. Cluster-range distributions and small-range
  exclusions are supplied.
- The 800 constructed comparisons are described as construction-defined signal
  fidelity, not human perceptual ground truth. Ties and a sensitivity analysis
  excluding darkening and desaturation are reported.
- VSQUAL is cited as a direct precedent for applying objective IQA in video
  summarization. Novelty is restricted to the mechanistic construct-validation
  audit and dependency-aware propagation analysis.
- Tables S1--S16, a complete 19-extractor inventory, exact Q-Align/DOVER
  settings, derived pair data, scripts and a table-to-script-to-data manifest
  are included in the revision archive.

## Major concern 10.1: scorer versus operation

**New experiment.** A matched-input control gives both SIFT+BoVW and LIQE the
same fixed budget of ten uniformly spaced 1-fps frames and arithmetic-mean
pooling. The scorers select different representatives in 16/42 clusters. On the
raw DOVER technical branch, LIQE minus SIFT is +27.1 points of the global
achievable range (topic-block CI [5.6,47.8]; hierarchical CI [2.4,52.5]) and
+0.00736 in raw score (topic [0.00135,0.01406]; hierarchical
[0.00057,0.01683]). Thus the scorer/representation causes a material difference
when frames and pooling are fixed.

**Resolution.** The complete 22/42 comparison is still correctly described as
an operation substitution because its internal sampling and pooling differ.
The new 16/42 control separately isolates scorer identity. Thirteen of those 16
clusters overlap the original 22-cluster change set; the two experiments answer
different estimands and are not conflated.

## Major concern 10.2: DOVER construct

**Audit result.** The original cache was produced with the official DOVER
checkpoint and `dover.yml` `val-l1080p` configuration. The scoring script saved
the two raw model outputs as `technical` and `aesthetic`, and saved their simple
sum as `overall`. That sum was not the official standardised fusion.

**New validation.** The exact raw technical branch used in the application was
run on all 800 constructed pairs with the official checkpoint and
`val-l1080p` technical view. Original and degraded sequences use the same 5-fps
MP4 wrapper and paired spatial-fragment seed 42. DOVER-T is correct on 781/800
pairs (97.6%), with a segment-block 95% CI [96.1%,99.0%] and no ties. Accuracy
is 100% for blur, JPEG, H.264, rescaling and motion blur; excluding darkening
and desaturation yields 599/600 (99.8%, CI [99.5%,100%]). This establishes
competence for the constructed technical changes, not human or compositional
validity.

**Resolution.** The technical branch remains the primary output reference. Its
configuration, sampling and checkpoint are specified in Methods and Table S13;
the official standardised fusion and DOVER++ remain outside the analysis.

**Reanalysis.** On the global-achievable-range scale, SIFT+BoVW reaches 50.5%
and LIQE 76.0%, a difference of +25.5 points. The topic-block 95% interval is
[-12.1,+54.9] and the hierarchical interval is [-17.2,+59.6]. Neither excludes
zero; the Abstract and Conclusion therefore report changed decisions and an
uncertain positive output estimate, not a confirmed population improvement.

## Major concern 10.3: within-cluster 0--100 scale

**Clarification.** The primary percentage is the position between the mean
selected low and high endpoints across clusters, not the arithmetic mean of
42 independently min--max-normalised scores.

**Added estimands.** For the DOVER technical branch, the raw mean difference is
+0.0069 (topic-block interval [-0.0028,+0.0178]; hierarchical interval
[-0.0041,+0.0197]). Mean within-cluster position differs by +7.2 points and the
rate of selecting the within-cluster maximum by +4.8 points; their intervals
also include zero. No cluster has zero range. The observed technical-branch
range has median 0.0169 and IQR [0.0089,0.0412]. Excluding the bottom 10% and
25% of ranges gives global-range differences of +25.9 and +28.1 points,
respectively.

## Major concern 10.4: supplement and archive

**Resolution.** Tables S1--S16 are compiled in `supplementary.pdf`. Table S13
now lists all 19 extractors, released torchvision weights, endpoints and common
preprocessing, and records the exact Q-Align and DOVER configurations. The
archive includes the raw derived JSONs for the constructed pairs,
`second_revision_reanalysis.json`, `third_revision_reanalysis.json`, the
matched-input and DOVER-T inference/reanalysis scripts, and
`reproducibility_manifest.md`.

**Boundary disclosed.** The historical model-inference environment was not
captured as a fully pinned lockfile. The archive therefore supports exact
reconstruction of reported statistics from hashed cached scores and source-level
inspection of inference settings, but does not claim bit-for-bit regeneration
of every neural score.

## Major concern 10.5: construction-defined truth

**Resolution.** The text now calls the unmodified member the
construction-defined higher-fidelity member and separates signal fidelity from
human-perceived quality. Ties remain in the denominator and count as neither
correct nor incorrect; no ties occur for SIFT+BoVW, LIQE or Q-Align.

**Sensitivity analysis.** Across all eight types, strict accuracy is 65.1% for
SIFT+BoVW, 99.5% for LIQE and 98.2% for Q-Align. Excluding darkening and
desaturation leaves 600 comparisons and yields 63.7%, 99.8% and 100.0%,
respectively. The decisive noise/JPEG conclusion is therefore unchanged.

## Major concern 10.6: novelty positioning

**Resolution.** Related Work now cites VSQUAL and states explicitly that the use
of IQA in video summarization is not new. The claimed novelty is the chain from
an exact implementation-level factorisation through controlled construct
validation to dependency-aware propagation in an operational pipeline.

## Additional reviewer questions

- **Descriptor-count mechanism.** Direct diagnostics were brought into the
  main Results and Table S12: degraded-minus-original descriptor count averages
  +469 for noise and +289 for JPEG, increasing in 92% and 95% of those pairs.
- **Q-Align quantisation.** The manuscript records the exact
  `q-future/one-align` checkpoint, `quality` task, `image` input, NF4 double
  quantisation and FP16 compute. No numerical-equivalence claim to FP16 is made.
- **Sampling and cost.** The candidate cache contains 2,892 uniform 1-fps frames
  from 83 distinct segments (3,525 instances after repeated cluster
  memberships). Table S14 separates per-frame timing from complete-operation
  timing and warns that the normalised SIFT value is not an identical-path
  microbenchmark.
- **Multiplicity and equivalence.** Methods now identifies the 630 possible
  pairwise contrasts among 36 evaluated scores, Bonferroni
  alpha=7.94e-5 and critical |z|=3.95. The +/-0.02 SRCC equivalence margin is
  explicitly an operational smallest effect of interest, not a universal field
  standard.

## Claims deliberately not made

The revision does not claim that LIQE alone caused the 22 changes under
identical frames and pooling, that the DOVER output is human ground truth, that
the DOVER output improvement is confirmed for a population of unseen topics,
that darkening/desaturation always reduce human preference, or that IQA had not
previously been used in summarization.
