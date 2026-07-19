# P2 Validation-Only Advance Rule

Frozen after split sealing and before any validation metric is computed.

The strict confirmatory test gate remains unchanged in
`docs/P2_PILOT_PROTOCOL.md`. Validation has one narrower purpose: decide whether
the provisional mechanism is credible enough to spend the one-time test
access.

For each dataset and each primary metric (Global and Cross-client AUC), the
strongest public control is selected by its mean validation AUC across the five
frozen seeds from two fixed candidates: sparse public-feature cosine and public
same-cell indication. The selected control is then fixed for test.

The visible-message DP coarsened release advances only if its mean paired
validation gain over that selected control is strictly positive in all four
dataset-metric cells. Confidence intervals and the +0.02 effect threshold are
reserved for the untouched test gate. A validation failure prohibits test
unsealing; it does not authorize changing cells, descriptors, partitions,
privacy parameters, or seeds and trying the same test again.
