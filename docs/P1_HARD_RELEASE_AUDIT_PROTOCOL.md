# P1 Hard-Release Selection Audit

Defined after the soft-candidate result and therefore **post-hoc exploratory**.

This audit does not create new experiment runs. It reuses the frozen
`P1_PAIR_FEATURE_PROTOCOL_v1` records to decide whether the hard-group DP
control is credible enough to become a provisional P2 mechanism family.

The practical threshold is not newly tuned: it reuses the preceding protocol's
requirement of at least +0.02 paired AUC over each fixed public-only control with
a paired 95% confidence interval excluding zero.

Core cells are both domains, ideal secure aggregation, epsilon in `{2,4}`, and
feature corruption in `{0.25,0.5}`. Metrics are global and cross-client AUC;
public controls are constant, cosine, negative cosine, hard-same, and
hard-different. This yields 80 comparisons.

Corruption 1.0 at epsilon 4 is reported as a boundary diagnostic. Because the
hard release was not the preregistered candidate, any successful audit remains
exploratory and requires a new preregistered P2 pilot on untouched seeds or
domains.
