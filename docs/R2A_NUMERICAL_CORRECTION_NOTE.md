# R2A Numerical-Conformance Correction

## First execution

The first frozen execution at code commit `4cecf2d` completed all 1,080 cells
and 5.4 million trials. Every scientific safety and power check passed, but the
registered accountant-reproduction check failed:

- maximum epsilon error: `3.0638e-10`;
- registered tolerance: `1e-10`.

The runner had called the shared Gaussian calibrator at its default internal
binary-search tolerance of `1e-10`. A stopping tolerance on noise standard
deviation does not guarantee the same absolute tolerance after nonlinear
conversion to epsilon. The implementation therefore did not satisfy the
already frozen numerical gate.

The first independent audit also reported `records_exactly_replayed=false`.
Inspection found no numerical record discrepancy: JSON serialization converts
the accountant's `orders` and `rdp` tuples into lists, while the in-memory replay
retains tuples. Native Python dictionary equality treated those equivalent
representations as unequal. The summary reproduced exactly.

The complete first output, including its failed audit, is preserved at
`results/r2a_certificate_synthetic_attempt1_numerical_nonconformance/`.

## Authorized correction

Two implementation-only corrections are made:

1. call the unchanged Gaussian calibrator with internal tolerance `1e-13`; and
2. compare replayed records after JSON canonicalization.

No scientific quantity changes: configuration, grid, trials, seeds,
distribution, privacy targets, failure allocation, material threshold, power
cells, and Go/No-Go thresholds remain byte-identical. The corrections were
determined solely by the registered numerical requirement and serialization
type mismatch.

The corrected implementation must be committed before rerun. Both attempts
must be reported. Any further scientific or numerical failure is terminal for
R2A under this protocol.
