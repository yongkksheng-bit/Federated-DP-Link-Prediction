# P2.1 Public-Preserving Residual Development

Frozen before the P2.1 development run. Existing P2 encrypted tests remain
permanently unavailable.

## Motivation

P2 failed on Facebook because a hard 16-cell score replaced a public cosine
predictor with AUC 0.9418 by a coarsened oracle with AUC 0.8681. Since the DP and
nonprivate coarse scores were nearly identical, privacy noise was not the
bottleneck. P2.1 therefore preserves public geometry and permits private
structure to act only as a bounded additive residual.

## Candidate family

For public cosine score `s_0(u,v)` and DP block release `R`, candidates are

`s(u,v) = s_0(u,v) + lambda * r_R(c(u),c(v))`,

where `c` is the fixed public-only 16-cell coarsening. Two bounded residual maps
are frozen:

1. centered percentile rank of the 136 released block densities in `[-1,1]`;
2. clipped standardized log-density in `[-1,1]`.

The lambda grid is `0.0025, 0.005, 0.01, 0.02, 0.05, 0.1`. Lambda zero is the
reported public baseline but is not an eligible private method. The mechanism
reuses the same sensitivity-one release, so these transformations and blends
are DP post-processing with no additional privacy cost.

## Development selection and stopping rule

All candidates are evaluated only on the already-opened P2 validation data.
The selected candidate maximizes its minimum mean gain over public cosine in
four cells: Global and Cross AUC on BlogCatalog and Facebook. Ties prefer the
smaller lambda and then centered rank.

Simple residual fusion advances only if the selected nonzero candidate has
positive gain in every cell and at least +0.002 mean gain on both Facebook
primary metrics. Otherwise this family is rejected. A failure authorizes design
work on a newly specified release but never access to an existing P2 test.
