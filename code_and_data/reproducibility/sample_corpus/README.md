# Sample corpus

Two topics from the broadcast collection used in this study, included so the
scoring and analysis scripts can be run end to end on real input.

| Topic | Videos | Size | Where |
|---|---:|---:|---|
| `bebe_real` | 3 | 34 MB | here, in the repository |
| `brumadinho` | 3 | 244 MB | release asset `sample_corpus_brumadinho` |

`brumadinho` ships as a release asset rather than in the repository because one
of its files is 98.7 MB, against GitHub's 100 MB per-file limit.

**This is a sample, not the collection.** The full corpus is not redistributed:
it remains with its authors.
This study uses it under their permission.

Only the video files are included. The segment boundaries and topic labels that
accompany the collection are not part of this package and are not required to
reproduce the results reported here: every operation evaluated in the article
scores individual frames, and the per-segment scores, cluster memberships and
seeds that the analyses consume are released as derived data under
`reproducibility/`.
