# P4R RAP Fresh-Seed Synthetic Confirmation Report

## Decision

`GO_TO_NEW_REAL_DATA_DEVELOPMENT_PROTOCOL`

RAP-v2 used selection seeds 30--39 and held-out seeds 40--59, with no overlap
with RAP-v1. The independent audit passed every completeness, sensitivity,
RDP, semantic-noise-coupling, finite-metric, and no-real-data check. The frozen
selector chose profile energy `0.5`, profile weight `2.0`, and prior strength
`1.0`.

| Held-out domain | Global gain over GAP (95% CI) | Cross gain over GAP (95% CI) |
|---|---:|---:|
| Reciprocal social | +0.06135 [+0.05610, +0.06659] | +0.06099 [+0.05552, +0.06645] |
| Reciprocal blog | +0.04773 [+0.03952, +0.05595] | +0.04901 [+0.04015, +0.05788] |

All frozen +0.02 materiality and positive-confidence-interval gates pass. The
result establishes that a node-level reciprocal affinity profile can carry
link-specific information beyond a matched GAP cosine decoder while consuming
the same `sqrt(2)` query sensitivity and the same RDP budget.

This is synthetic mechanism evidence, not an empirical paper claim. It
authorizes a separately frozen real-graph development protocol. The synthetic
configuration must first be tested without tuning; P3 encrypted test data
remain prohibited, and fresh-source confirmation is mandatory before method
selection.
