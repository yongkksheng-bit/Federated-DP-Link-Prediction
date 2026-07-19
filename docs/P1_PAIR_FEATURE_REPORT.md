# P1 Pair-Feature Candidate Report

Run date: 2026-07-19 (Asia/Shanghai).

Evidence status: **closed diagnostic failure**.

## Integrity

- Frozen protocol and source commit:
  `ed5aad25336a9fd220a390c02528737e37242bae`
- Records: 1080/1080; cells: 36; tests: 17/17 passed
- `records.jsonl` SHA-256:
  `C15169A748A8F7D20845F5FEAFC0421FE78F07173B89E1F21CA91D5AFC519B20`
- `summary.json` SHA-256:
  `88ED0EAED50ECD7B5CD95DCF97B63D471DE782491A4562493F70E91C04BCB369`
- Deterministic replay reproduced both hashes.
- All records use L2 sensitivity one and include the complete RDP curve.
- No raw edge, candidate, latent-group, or node-feature arrays were admitted.

The machine-readable decision is `REJECT`: 4 of 12 gate checks failed.

## What succeeded

All eight public-utility gate cells passed. The soft DP statistic exceeded each
fixed public-only comparator (constant, cosine, negative cosine, hard-same, and
hard-different) by the preregistered practical and confidence thresholds. This
repairs an important weakness of the reference P1 test: on generalized
affinities, private edge statistics add information unavailable from simple
public-feature similarity alone.

## Why the candidate was rejected

Cross-client AUC at epsilon 4 under ideal secure aggregation:

| Domain | Feature corruption | Soft pair DP | Hard-group DP | Soft minus hard (95% CI) |
|---|---:|---:|---:|---:|
| Heterophilic social | 0.25 | 0.6855 | 0.6972 | -0.0117 [-0.0139, -0.0094] |
| Heterophilic social | 0.50 | 0.6414 | 0.6929 | -0.0515 [-0.0561, -0.0469] |
| Heterophilic social | 1.00 | 0.5723 | 0.6150 | -0.0427 [-0.0484, -0.0370] |
| Mixed blog | 0.25 | 0.6576 | 0.6824 | -0.0248 [-0.0271, -0.0226] |
| Mixed blog | 0.50 | 0.6147 | 0.6816 | -0.0670 [-0.0698, -0.0642] |
| Mixed blog | 1.00 | 0.5577 | 0.6207 | -0.0630 [-0.0673, -0.0587] |

Both hard noninferiority checks and both high-corruption hard-superiority checks
failed. The candidate may not be promoted or retuned under this protocol.

## Mechanism diagnosis

The likely issue is statistical rather than privacy calibration. Continuous
noisy public features enter a second-order pair map, while the public Gram
matrix treats them as error-free covariates. This errors-in-variables effect
attenuates the learned affinity. Hard argmax discards uncertainty but also
denoises the latent centers, yielding a much more efficient block statistic.

The next candidate should preserve hard quantization's efficiency while
reducing dependence on one brittle assignment. A preregistered ensemble of
multiple public hard views is admissible only with its joint L2 sensitivity and
release dimension derived in advance.
