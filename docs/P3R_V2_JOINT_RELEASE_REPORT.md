# P3R-v2 Joint Release Development Report

## Decision

`NO_GO_REJECT_JOINT_RELEASE_CANDIDATE`

The frozen run completed all 750 grid cells and all 30 leave-one-seed-out
held-out records. The independent audit passed every completeness, privacy,
provenance, communication, and no-test-access check. The encrypted P3 test was
not accessed.

## Paired gains over the frozen GAP-style baseline

| Dataset | Global gain (95% CI) | Cross gain (95% CI) |
|---|---:|---:|
| BlogCatalog-v3 | +0.0010 [-0.0002, +0.0023] | +0.0012 [-0.0005, +0.0029] |
| Facebook-MUSAE | +0.0475 [+0.0461, +0.0489] | +0.0475 [+0.0455, +0.0494] |
| PolBlogs-Newman | -0.0019 [-0.0099, +0.0060] | -0.0026 [-0.0129, +0.0076] |
| LastFM-Asia-SNAP | +0.0052 [-0.0011, +0.0114] | +0.0047 [-0.0030, +0.0124] |
| GitHub-Social-SNAP | +0.0420 [+0.0404, +0.0435] | +0.0417 [+0.0400, +0.0434] |
| Deezer-Europe-SNAP | +0.0084 [+0.0011, +0.0157] | +0.0103 [+0.0032, +0.0174] |

The candidate met the predeclared significant-win count exactly: Facebook,
GitHub, and Deezer had positive Global and Cross confidence intervals. It also
met both per-dataset non-inferiority boundaries. It failed only the two macro
materiality gates: mean Global gain was +0.0170 and mean Cross gain was +0.0171,
below the frozen +0.02 thresholds.

## Interpretation

The result validates the budget-coupling construction but not this frozen
decoder as the final method. The conditioned residual adds material utility on
feature-rich social domains while preserving the GAP backbone, but contributes
little on BlogCatalog and LastFM and is neutral on PolBlogs. Four datasets
selected the maximum residual weight for most held-out folds, and the aggregate
validation AUC increased monotonically across the frozen weight grid. The
smallest histogram energy fractions were generally strongest. This is evidence
that the search boundary, rather than the joint sensitivity construction, may
be limiting the candidate; it is not permission to reinterpret P3R-v2 as a GO.

Any P3R-v3 boundary extension must be frozen as a new development protocol and
must retain the same encrypted-test prohibition. The P3R-v2 decision is final.
