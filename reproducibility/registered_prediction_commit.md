# Registered-prediction commit provenance

The eight predictions in Supplementary Table S12 were committed before the
constructed experiment at:

- full commit: `9377c07ca080ac61c7cff80e0ff6c7507b6ebaba`
- author date: `2026-08-06T16:08:41-04:00`
- subject: `registra predicoes do experimento sintetico in-domain antes de rodar`
- file: `PREDICTIONS_synthetic_indomain.md`

The analysis repository's public default branch did not yet make this object
reachable when the submission archive was frozen. This submission repository
publishes it through the separate `registered-predictions` branch. Its private
release also includes `registered_prediction_commit.bundle`, a complete Git
bundle whose `master` reference resolves to the full commit above. After
downloading that asset, verify it without network access:

```bash
git clone registered_prediction_commit.bundle registered-predictions
git -C registered-predictions bundle verify \
  ../registered_prediction_commit.bundle
git -C registered-predictions show --stat \
  9377c07ca080ac61c7cff80e0ff6c7507b6ebaba
git -C registered-predictions show \
  9377c07ca080ac61c7cff80e0ff6c7507b6ebaba:PREDICTIONS_synthetic_indomain.md
```

The Git bundle makes the registered object and its parent history independently
inspectable. A future public archival release should expose the same full
commit and may be deposited in Zenodo after author approval.
