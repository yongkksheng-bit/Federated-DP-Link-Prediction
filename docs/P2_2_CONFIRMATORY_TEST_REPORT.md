# P2.2 One-Time Confirmatory Test Report

Decision: **GO TO P3.**

The one-time test began and completed on 2026-07-19 UTC from clean freeze
commit `1a5a4c4`. Exactly ten encrypted payloads were accessed once. The access
record was written before decrypt, completed successfully, and its records and
summary SHA-256 values independently match the generated files. This test must
never be run again.

## Frozen-gate results

| Domain | Metric | Candidate AUC | Gain over public cosine (95% CI) | Cell decision |
|---|---|---:|---:|---|
| GitHub Social | Global | 0.65916 | +0.05079 [+0.05006, +0.05152] | PASS |
| GitHub Social | Cross | 0.65901 | +0.05071 [+0.05004, +0.05139] | PASS |
| Deezer Europe | Global | 0.63738 | +0.03365 [+0.03139, +0.03591] | PASS |
| Deezer Europe | Cross | 0.63548 | +0.03348 [+0.03032, +0.03665] | PASS |

Every mean gain exceeds the preregistered `+0.02` materiality threshold and
every paired interval lower bound is above zero. In every cell, the paired
interval lower bounds over both random score and the matched zero-private-signal
release are also above zero. All five individual seed gains are positive in
each cell.

## Privacy and provenance

- Candidate: `conditioned_b8_lambda_0.1`.
- Primary transcript: individually visible client messages.
- Calibrated release: `epsilon=3.9999999997`, `delta=10^-6`, Gaussian standard
  deviation `1.4049865331`, selected RDP order 8.
- Query dimension: 1,088; exact add/remove-edge L2 sensitivity: 1.
- Records: 10/10, five seeds on each of two untouched sources.
- Zero-private-signal uses the exact same Gaussian draw as the candidate.
- Test access record: `completed`, ten payloads, one batched access event.

The result selects the public-score-conditioned count release as the primary
mechanism for P3 benchmarking. It does not yet establish a submission-ready
paper: P3 must add matched baselines, privacy-budget sweeps, scalability and
failure-boundary analyses without retuning this test. GitHub and Deezer test
data are now exhausted confirmatory evidence and cannot be reused for method
selection.
