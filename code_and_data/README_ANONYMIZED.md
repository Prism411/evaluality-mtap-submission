# Code and derived data (anonymized for double-anonymized review)

This archive accompanies the manuscript under review. It contains the analysis scripts, the
reference implementation of the audited operations, the derived measurement files every
reported number depends on, the scripts that generate each table and figure, the consistency
checks run before each build, and a one-topic sample of the broadcast corpus.

**Anonymization.** Author names, e-mail addresses, user names, local paths and repository and
venue names were replaced by neutral placeholders (for example `[author]`, `/home/user`,
`/data/projects/`) in comments, strings and provenance fields. No measured value was changed.
Because of these replacements the checksums in `reproducibility/SHA256SUMS` were recomputed on
this anonymized content; the permanent repository, cited upon acceptance, carries the original
files and their original checksums.

**Corpus sample.** `reproducibility/sample_corpus/bebe_real/` holds one topic (three videos,
34 MB). The second sample topic (three videos, 255 MB) is not in this archive because of its
size; it accompanies the permanent repository. The full corpus is not redistributed: it remains
with its authors and is used under their permission.

**Running.** Local absolute paths in the scripts point to the original machine and must be
adapted; `reproducibility/README.md` lists which scripts run end to end from this archive and
which need inputs that are not redistributed (image-quality databases, source media, model
weights).
