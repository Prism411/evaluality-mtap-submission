# Pre-registered predictions — synthetic in-domain ground-truth experiment

Committed **before** any of the experiment below was run. The point of writing
these down is that Equation (8) of the article,

    score_i = D_i * mean_idf_i

makes falsifiable, method-specific predictions about an experiment whose correct
answer is known by construction. If the measurements match, the factorization
predicted the pattern rather than being fitted to it. If they do not, the
factorization is wrong and the article must say so.

## Experiment being predicted

- 31 distinct broadcast segments, 1 FPS, capped at 30 frames each.
- 8 degradation types x 5 levels applied to each segment:
  - KADID-compatible: gaussian blur, white noise, darkening, JPEG compression.
  - Broadcast-realistic: H.264 low-bitrate transcode, 720p->480p->720p
    downscale-upscale, motion blur, saturation shift.
- Design A: cluster = {original, degraded copy at level L}. Correct answer =
  original. 31 x 8 x 5 = 1240 binary clusters.
- Design B: Spearman between score and level over the 6 points
  (original + 5 levels), per segment x type; 248 pairs.
- Design C: stratify Design A accuracy by the overlay annotation already
  released with the article (13 heavy / 11 moderate / 7 light).

Bootstrap is at the **segment** level (resample the 31 with replacement, 10^4
draws, seed 42), because the 1240 clusters reuse 31 segments and are not
independent.

## Predictions

| # | Method | Prediction | Derivation |
|---|--------|-----------|------------|
| P1 | SIFT+BoVW | High accuracy on blur and darkening | Both remove detectable structure, so D drops, so the score drops. Correct answer by accident. |
| P2 | SIFT+BoVW | **Inverted** (below 50%) on white noise | Noise creates spurious extrema; Table 4 already measures +75% keypoints on the noisy copy. D rises, score rises, degraded copy wins. |
| P3 | SIFT+BoVW | Near chance on JPEG and H.264 transcode | Compression at moderate rates leaves keypoint density largely intact. |
| P4 | CNN+BoVW (all 19) | At the chance floor on **every** type | Fixed-size feature map => D_i constant => the count channel is switched off, leaving only the bounded rarity channel. |
| P5 | NIQE, BRISQUE | Accuracy drops in the heavy-overlay stratum relative to light | Synthetic edges and flat regions violate the natural-scene-statistics assumption. This is the hypothesis of Section 5.3, untested there. |
| P6 | LIQE, QualiCLIP, CLIP-IQA+, Q-Align | No interaction with overlay stratum | Counterfactual to P5: if the NSS drop is about the NSS assumption, methods that do not make it should not show it. |
| P7 | SIFT+BoVW | Design B mean Spearman below 0.15 | It responds to 2 of 25 KADID types; the same insensitivity should reproduce on 8 types in-domain. |
| P8 | Q-Align (reference model) | Accuracy above 0.90 on Design A | Stated so the reference's own competence on this content is measured rather than assumed. A value below 0.90 weakens every in-domain claim that rests on it, and the article must report that. |

## What would falsify the factorization

P2 and P4 are the load-bearing ones. If SIFT+BoVW does **not** invert on noise,
the claim that the count channel governs is wrong. If the CNN+BoVW variants do
**not** sit at chance, then the rarity channel carries something after all and
the ablation argument in Section 4.6 collapses.

## Discipline

This experiment is **reported and not used in the acceptance rule** of Section
3.4. The rule was stated before this experiment existed, and reopening it now
would destroy the property it exists to provide.

---
Author: J. L. de Souza Goncalves. No human subjects are involved in any part of
this experiment.
