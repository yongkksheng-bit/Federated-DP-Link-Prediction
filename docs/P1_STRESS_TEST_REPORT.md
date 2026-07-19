# P1 Synthetic Stress-Test Report

Run date: 2026-07-19 (Asia/Shanghai).

Evidence status: **diagnostic protocol evidence**, not manuscript evidence.

## Integrity

- Frozen protocol and executed source commit:
  `517e018785794e5b68508d6932ab19bab84d7471`
- Records: 1600/1600; summary cells: 80; required gate cells: 22
- Tests: 14/14 passed
- `records.jsonl` SHA-256:
  `0103F03952E8BF04006AF347241EEDF3748DA01FDA3A81B934D220FAE13F1A8F`
- `summary.json` SHA-256:
  `C501D0B31AE4DE5998B4432D6B48E7FAE471D66F9DA37E176F5B991DCD74F4E3`
- Deterministic replay reproduced both hashes.
- No raw edge or candidate arrays are present in admitted records.

All 22 preregistered gate cells passed. The machine-readable decision is
`ADVANCE`; real-data access remains prohibited.

## Public-group misspecification

Cross-client AUC under ideal secure aggregation at epsilon 4:

| Corrupted public labels | Social assortative | Blog mixed |
|---:|---:|---:|
| 0% | 0.7404 | 0.6046 |
| 10% | 0.6875 | 0.5813 |
| 25% | 0.6167 | 0.5489 |
| 50% | 0.5324 | 0.5092 |

The 25% cells retain more than the required +0.02 AUC over public-only in both
domains. At 50% corruption, every blog cell falls below the practical-effect
threshold; at epsilon 0.5 its paired interval includes zero. Public-view
quality, rather than Gaussian noise, is the dominant failure mode in this
coarse release.

## Privacy and release dimension

Calibrated one-step Gaussian scales were 10.6074, 5.3500, 2.7207, 1.4050, and
0.7416 for epsilon 0.5, 1, 2, 4, and 8, respectively. Coarse block scores remain
nearly flat across epsilon because the noise rarely changes the ordering of the
few block densities. This is a ranking-resolution effect, not evidence that DP
noise is costless.

At epsilon 1 and refinement factor 4, cross-client AUC is:

| Domain | Ideal secure aggregation | Visible messages |
|---|---:|---:|
| Social assortative | 0.7364 | 0.6878 |
| Blog mixed | 0.5796 | 0.5425 |

The release dimensions span 10--210. Increased dimension and reduced block
capacity expose the expected DP and visibility penalties that coarse blocks
hide.

## Federation scaling

At epsilon 4 and refinement factor 4:

| Domain | Visibility | K=2 cross AUC | K=5 | K=10 | K=20 |
|---|---|---:|---:|---:|---:|
| Social assortative | Ideal secure aggregation | 0.7411 | 0.7402 | 0.7415 | 0.7413 |
| Social assortative | Visible messages | 0.7410 | 0.7380 | 0.7402 | 0.7363 |
| Blog mixed | Ideal secure aggregation | 0.6022 | 0.6015 | 0.6001 | 0.6002 |
| Blog mixed | Visible messages | 0.6000 | 0.5880 | 0.5882 | 0.5680 |

Ideal aggregation is stable with K, as predicted for one aggregate release.
Visible independent messages accumulate `K` noise vectors and degrade the
sparser blog regime most strongly.

## Decision and next constraint

The sensitivity-one release has a genuine but conditional feasible region.
P1 may advance to a stronger synthetic candidate mechanism. That mechanism
must reduce reliance on accurate public groups, keep its release dimension
explicit, and treat ideal secure aggregation and individually visible messages
as different privacy-utility regimes. The 50%-corruption failure must remain in
the evidence record and may not be tuned away.
