# P2.1 Confirmatory Validation Sanity Gate

Frozen before any PolBlogs or LastFM validation metric is computed.

The method is already fixed: public cosine plus weight 0.05 times the centered
rank of the sensitivity-one DP block release. Validation cannot select a new
weight, transform, coarsening, privacy parameter, or seed.

Before spending the one-time encrypted test access, the visible-message
candidate must have strictly positive mean paired gain over public cosine in
all four Dataset-by-{Global,Cross} validation cells. Confidence intervals and
the +0.02 threshold remain properties of the untouched confirmatory test gate,
not this sanity check.

Failure leaves all confirmatory tests encrypted and rejects this protocol
version. Passing authorizes an implementation/result-schema freeze followed by
one batched test access.
