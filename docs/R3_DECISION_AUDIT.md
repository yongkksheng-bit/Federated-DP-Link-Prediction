# R3 Decision Audit

## Decision

**Classification:** `THEORY_ONLY_FEASIBILITY_BOUNDARY`

**Real-data method authorization:** denied.

R3 validates a rigorous and empirically calibrated sample-complexity boundary
for the R1 private no-harm certificate. It does not rehabilitate CertFed-LP as
an end-to-end utility method. The realistic synthetic graph counts and effects
observed in R2B lie far below the most optimistic R3 boundary.

## Analytical boundary audit

The frozen R3 analytical grid contains 558 records, including 240 private
minimum-count cells. Every registered check passed:

- every boundary was finite within the fixed maximum count;
- every returned count passed while the preceding integer failed;
- minimum count decreased with effect size and epsilon;
- minimum count increased with dependence;
- ideal secure aggregation was invariant to client count;
- visible-message requirements increased with client count;
- forward and inverse boundaries agreed;
- the RDP accountant reproduced target epsilon;
- no real or held-out graph data were accessed.

The analytical decision was
`PASS_TO_R3_MONTE_CARLO_CALIBRATION_PROTOCOL`.

## Fresh Monte Carlo audit

The frozen fresh-seed calibration produced 128 aggregate cells from 384,000
synthetic trials.

| Metric | Result |
|---|---:|
| Minimum activation rate at predicted boundary | 0.9913 |
| Minimum one-sided 95% power lower bound | 0.9880 |
| Maximum safety false-activation rate | 0.0030 |
| Maximum one-sided 95% safety upper bound | 0.00523 |
| Maximum predicted/empirical 90% transition ratio | 1.000 |
| Maximum accountant epsilon error | 9.15e-14 |

All registered calibration gates and the exact replay audit passed.

## Practical boundary

For five clients and `chi = 1`, representative sufficient counts are:

| Transcript | epsilon | Effect 0.05 | Effect 0.10 | Effect 0.20 |
|---|---:|---:|---:|---:|
| Ideal secure aggregation | 1 | 31,505 | 5,052 | 1,245 |
| Visible client messages | 1 | 34,642 | 6,171 | 1,714 |
| Ideal secure aggregation | 4 | 29,562 | 4,330 | 928 |
| Visible client messages | 4 | 30,425 | 4,655 | 1,073 |

R2B generated only 1,048--1,368 certification edges per graph. Even under the
strictly more optimistic **non-private** boundary, the minimum detectable
population effect over that count range is approximately 0.158--0.177. At
`epsilon = 8`, the ideal-secure-aggregation requirement is approximately
0.162--0.183.

The largest R2B empirical certification gain was 0.0683. Across all 2,880 R2B
cells, no observed certification gain reached even the non-private
high-probability boundary. The smallest optimistic gap was still

`observed gain - non-private minimum detectable effect = -0.0979`.

This comparison is a descriptive post-R2B diagnosis, not a new confirmatory
test. Its purpose is to explain the terminal zero-activation result.

## Interpretation

The private certificate is valid and its sufficient power boundary is neither a
software artifact nor grossly miscalibrated. The route fails because the
registered graph protocol supplies effects that are too small relative to the
number of independent certification records. Privacy noise worsens the
requirement, but it is not the sole cause: the non-private confidence boundary
already excludes the observed R2B regime.

Therefore:

1. R3 supports a theorem-and-calibration contribution about the feasibility
   boundary of certified private adaptation.
2. R3 does not support a claim that CertFed-LP improves link-prediction utility
   on realistic graphs.
3. No real-data experiment is authorized for the current method.
4. A new utility method may be considered only after a new P0/R1 derivation
   changes the statistical object, privacy unit, trust model, or source of
   independent certification evidence.

## Publication consequence

The scientifically defensible route is now a boundary paper:

> When is target-domain utility improvement certifiable for differentially
> private link prediction in a federated setting?

The fixed title remains usable, but the contribution must center the formal
privacy boundary, the no-harm impossibility result, the sample-complexity
theorem, and audited synthetic calibration. It must not be presented as a
state-of-the-art real-graph utility method without a separately authorized and
successful method protocol.
