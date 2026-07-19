# P2 Validation Report

Status: **NO-GO; sealed test remains untouched.**

The validation implementation was frozen at `9ed8fc3`. It produced 10 paired
records (two datasets by five seeds) under `(epsilon,delta)=(4,10^-6)` with a
one-shot sensitivity-one Gaussian release. Every record stores the full RDP
curve, selected order, calibrated standard deviation, release dimension,
client counts, config hashes, and `test_accessed=false`.

## Primary validation comparison

| Dataset | Metric | Visible-message DP | Selected public control | Paired gain (95% CI) | Advance |
|---|---|---:|---:|---:|---|
| BlogCatalog v3 | Global | 0.5830 | cosine 0.5503 | +0.0328 [0.0305, 0.0351] | yes |
| BlogCatalog v3 | Cross | 0.5828 | cosine 0.5502 | +0.0326 [0.0305, 0.0348] | yes |
| Facebook MUSAE | Global | 0.8680 | cosine 0.9418 | -0.0738 [-0.0748, -0.0728] | no |
| Facebook MUSAE | Cross | 0.8677 | cosine 0.9419 | -0.0741 [-0.0760, -0.0722] | no |

All four cells were required. The candidate therefore fails the preregistered
validation advance rule and the encrypted test payloads may not be opened.

## Mechanistic diagnosis

This is not primarily a privacy-noise failure. On Facebook, the nonprivate
coarsened affinity oracle reaches 0.8681 Global AUC, essentially identical to
the DP visible-message result. Ideal secure aggregation is also 0.8681. The
public descriptor cosine reaches 0.9418. Thus the 16-cell approximation discards
predictive public geometry that the fixed public control retains; reducing the
Gaussian noise cannot close the gap.

BlogCatalog shows the complementary regime: the same release improves Global
and Cross AUC over public cosine by more than 0.03 with paired intervals above
zero. P1 feasibility was therefore real but not cross-domain sufficient.

## Scientific consequence

The provisional hard public-coarsened affinity release is rejected as the
paper's cross-domain primary method. The result does not invalidate
inference-closed edge-DP link prediction. It requires a redesigned release or
score that preserves the strongest public predictor and adds private structure
as a DP residual, rather than replacing the public geometry with a hard cell
lookup.

Any redesign is a new protocol version. It may use these validation findings as
development evidence, but it may not unseal or reuse the current P2 test gate.
An untouched confirmatory source/split must be registered before a new claim.
