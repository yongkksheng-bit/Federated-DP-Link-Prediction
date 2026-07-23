# R2A Private-Certificate Synthetic Report

## Decision

`PASS_TO_R2B_END_TO_END_SYNTHETIC_PROTOCOL`

The corrected frozen execution completed 1,080 cells and 5.4 million trials.
The independent audit exactly replayed every record, summary metric, and final
decision. No graph, real dataset, sealed test, P5FC result, or future source was
accessed.

## Registered results

| Metric | Result | Gate |
|---|---:|---:|
| Maximum lower-bound safety-violation rate | 0.0064 | at most 0.05 |
| One-sided 95% upper bound | 0.00859 | at most 0.06 |
| Maximum false activation below `gamma` | 0.0022 | at most 0.05 |
| False-activation 95% upper bound | 0.00364 | at most 0.06 |
| Minimum registered ideal power | 1.000 | at least 0.80 |
| Minimum registered visible-message power | 1.000 | at least 0.70 |
| Positive-cell activation fraction | 0.4266 | at least 0.20 |
| Maximum accountant epsilon error | 1.75e-13 | at most 1e-10 |

All ten registered checks pass.

## Interpretation

For bounded block-dependent utility records, the noisy-sum/noisy-count
certificate is conservative without being vacuous. It controls activation
below the material threshold and retains high power when the true advantage is
at least 0.10 with 10,000 certification records and epsilon at least 2.

The visible-message result includes the increased aggregate variance from up to
five independently noised client messages in the registered power cells.

## Numerical correction provenance

The first execution is not hidden. It is preserved under
`results/r2a_certificate_synthetic_attempt1_numerical_nonconformance/`.
Its scientific checks passed, but the accountant error exceeded the numerical
gate because the solver's internal tolerance was too coarse; its audit also
used tuple/list-sensitive equality.

Commit `4e43eec` documented and froze the two implementation-only corrections
before the sole rerun. No scientific configuration or threshold changed. The
corrected audit passes.

## Claim boundary

R2A does not establish that a graph structural learner produces positive
utility, that pairwise certification transfers to standard ROC-AUC, or that the
existing aggregate-only visible-message helper represents the primary server
transcript. Those questions remain mandatory R2B work.
