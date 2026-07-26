# R8 Closeout

Closed: 2026-07-26 (Asia/Shanghai).

## Status

`R8_INTERNAL_RED_TEAM_COMPLETE`

Technical decision: `GO_SUBMISSION_PREPARATION`

Submission decision:
`CONDITIONAL_GO_PENDING_EXTERNAL_EXPERT_REDERIVATION`

## Passed gates

- The red-team protocol was frozen before the adversarial audit.
- 106/106 software tests passed.
- The R7 independent artifact audit passed unchanged.
- The R8 machine audit passed every registered theorem and manuscript check.
- Conditional fixed-size assignment was exhaustively checked for uniformity.
- The adaptive-public-hash and unstable-index-partition counterexamples were
  reproduced and are explicitly excluded by the manuscript contract.
- Certificate good-event algebra survived 5,000 adversarial trials, including
  2,560 valid parameter cases, with no violation.
- The pure-DP lower-bound formula was independently reproduced.
- Approximate-DP degradation was exhibited, and the manuscript now restricts
  inverse-epsilon rate matching to pure DP while using the exact
  `D_star(epsilon, delta, eta)` expression for approximate DP.
- The manuscript distinguishes an ideal independent draw, a registered
  random-oracle instantiation, and a secret-key PRF deployment; the PRF
  distinguishing advantage is included.
- A clean GitHub clone at commit
  `9ffb0c2e4c144635f1cb30c5e5ffeaa7eae891a7` passed the R7 and R8 audit
  wrappers without tracked working-tree changes.
- The clean-built nine-page manuscript is byte-identical to the tracked R8
  PDF, with SHA-256
  `1ed06bee6f1fafc328cddbf56a3ff866cb7e47e45c09e7ee052f9838909da06e`.
- The PDF has no undefined references, overfull boxes, clipping, overlap, or
  blank-page defect.
- The sealed P3/R5 holdout was not decrypted, regenerated, or revisited.

## Delivered

- `scripts/audit_r8_red_team.py`
- `scripts/reproduce_r8_submission.py`
- `tests/test_r8_red_team.py`
- `results/r8_red_team/audit.json`
- `results/r8_red_team/reproduction.json`
- `docs/R8_THEOREM_RED_TEAM.md`
- `docs/R8_TIFS_MOCK_REVIEW.md`
- `docs/R8_EXTERNAL_REVIEW_PACKET.md`
- `output/pdf/certfed_lp_r8_red_team_audited.pdf`

## Remaining human submission gates

R8 is an internal adversarial audit, not external peer review. Before an
actual journal submission:

1. have an independent privacy/statistics expert rederive Theorems 2--4 using
   `docs/R8_EXTERNAL_REVIEW_PACKET.md`;
2. repeat the forward/backward literature search on the submission date;
3. apply venue-specific anonymization, ethics, data-availability, and artifact
   requirements; and
4. do not alter the registered R5 claim or access the sealed holdout without a
   new preregistered protocol.

No failed internal technical R8 gate remains. The manuscript may enter
submission preparation, but external expert review must not be claimed until
it has actually occurred.
