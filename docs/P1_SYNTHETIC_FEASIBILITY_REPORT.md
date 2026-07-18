# P1 Synthetic Feasibility Report

Run date: 2026-07-18 (Asia/Shanghai).

Evidence status: **diagnostic protocol evidence**, not manuscript evidence.

## Integrity

- Frozen protocol commit: `e64033760276bcf3a3fa3620a797a54512d7672d`
- Executed source commit: `7a7a768942ab15b5306087b6050f6cf81e24b299`
- Records: 60/60 (2 domains x 30 paired seeds)
- Tests: 10/10 passed
- `records.jsonl` SHA-256:
  `253E61E7DC2BEEC2A7BB37E3A88895F58AEBFA32696F8661B9A6C2007B3DD15A`
- `summary.json` SHA-256:
  `08A68EA7C2D81222FBDC1A131F2D76BB0CC882170153EC7AAEB654FBA8937513`
- A second execution produced identical hashes.

The calibrated release has `epsilon=3.99999999969362`, `delta=1e-6`, selected
RDP order 8, L2 sensitivity 1, one composition, and absolute Gaussian noise
standard deviation `1.4049865331`.

## Frozen-gate results

| Domain | Metric | Ideal-secagg DP AUC | Public-only AUC | Paired improvement (95% CI) | Oracle AUC |
|---|---|---:|---:|---:|---:|
| Social assortative | Global | 0.7418 | 0.5000 | +0.2418 [0.2357, 0.2478] | 0.7423 |
| Social assortative | Cross-client | 0.7405 | 0.5000 | +0.2405 [0.2337, 0.2474] | 0.7412 |
| Blog mixed | Global | 0.6074 | 0.5000 | +0.1074 [0.1029, 0.1119] | 0.6062 |
| Blog mixed | Cross-client | 0.6070 | 0.5000 | +0.1070 [0.1012, 0.1129] | 0.6067 |

Every preregistered global and cross-client gate passed in both domains. The
machine-readable decision is `GO`.

## Visibility diagnostic

Visible-message global AUC is 0.7409 on the social domain and 0.6072 on the
blog domain, versus 0.7418 and 0.6074 under ideal secure aggregation. The
expected count-noise variance is five times larger, but block capacities are
large enough that this produces less than 0.001 AUC loss here.

## Scientific conclusion

P1 establishes only that a sensitivity-one, low-dimensional, inference-closed
structural release can preserve link-ranking signal in two controlled regimes.
It does not validate a final method or real-data performance. The next gate
must stress block misspecification, higher release dimension, client scaling,
and stricter epsilon before any real dataset is accessed.
