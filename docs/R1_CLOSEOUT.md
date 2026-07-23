# R1 Closeout

## Decision

`PASS_TO_SYNTHETIC_PROTOCOL_DESIGN`

R1 establishes a coherent mathematical route for CertFed-LP:

1. a data-independent disjoint edge partition supports adaptive parallel RDP
   composition when conditional certification is uniformly private;
2. the certification query releases both a bounded utility sum and its private
   count with L2 sensitivity `sqrt(2)`;
3. a one-sided noisy lower certificate yields a high-probability no-harm
   activation theorem under an explicit target-domain concentration condition;
   and
4. a training-only cross-domain selector cannot have a nontrivial universal
   no-harm guarantee without a transport assumption.

The framework therefore replaces unsupported cross-domain extrapolation with
same-domain private evidence and a public-only fallback.

## What R1 does not establish

R1 does not show that the candidate structural branch has positive utility,
that certification has useful power at practical privacy budgets, or that the
registered corrupted-pair utility transfers to standard ROC-AUC. It does not
resolve graph-edge dependence. These are R2 synthetic feasibility questions,
not consequences of the theorems.

## Access and integrity

- real-graph experiments: none;
- P3 sealed-test access: none;
- P5FC outcome reuse: none;
- new source acquisition: none; and
- method or threshold tuning from empirical outcomes: none.

R2 may begin only after its synthetic regimes, failure allocations,
accountants, dependence scope, and Go/No-Go gate are frozen in a new commit.
