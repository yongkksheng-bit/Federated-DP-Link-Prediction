# R1 Theorem and Claim Audit

## Audit decision

`PASS_WITH_EXPLICIT_R2_OBLIGATIONS`

The three R1 results form a logically consistent foundation for a
target-domain private certificate. They do not yet establish empirical utility
or authorize a real-data run.

## Proof dependency table

| Result | Required condition | Failure if omitted |
|---|---|---|
| Certification sensitivity | one edge contributes one bounded record; no rejection sampling | sensitivity can exceed `sqrt(2)` |
| Adaptive parallel composition | public disjoint edge hash; uniform conditional certification DP | must sequentially compose |
| Inference post-processing | both branches are inference-closed | score transcript is not covered |
| Visible-message privacy | every client message is locally noised | server observes raw private statistics |
| Secure-aggregation utility | ideal functionality hides individual messages | central-noise implementation invalid |
| Empirical lower bound | noisy sum and count both satisfy registered tail bounds | denominator or numerator can be optimistic |
| Population no-harm | registered conditional concentration factor `chi` | certificate covers only the observed set |
| Cross-domain impossibility | unrestricted target family and no transport assumption | theorem no longer applies |

## Corrections to tempting but invalid claims

1. **Do not say that disjoint stages imply parallel composition.** The edge
   partition must be public and disjoint, and certification must be uniformly
   DP conditional on every training release.
2. **Do not treat the certification count as public.** It is released jointly
   with the bounded utility sum.
3. **Do not use `sqrt(2)` sensitivity with graph-dependent negative
   rejection.** One private edge could modify more than one record.
4. **Do not label the pairwise certificate as a standard-AUC certificate.**
   Their negative distributions differ unless separately proved equivalent.
5. **Do not use iid Hoeffding for graph edges without an assumption.** R2 must
   register and stress-test `chi`, or restrict the claim to empirical
   certification utility.
6. **Do not claim that secure aggregation is DP.** It changes server
   visibility and permits central noise; the Gaussian mechanism supplies DP.
7. **Do not release graph-backed embeddings or scores after training.** The
   deployed branch must remain a function only of DP/public releases and
   public inputs.
8. **Do not tune `gamma`, failure allocations, the corruption map, or the
   candidate branch on certification outcomes.**

## R2 obligations before synthetic execution

R2 must freeze:

- train/certification/test hash fractions and salt handling;
- the endpoint-corruption map and tie convention;
- candidate structural trainer and complete `rho_T(alpha)` accountant;
- visible-message and ideal-aggregation implementations;
- `sigma_C`, `delta`, RDP order grid, and failure-probability allocation;
- `gamma`, minimum usable noisy count, and fallback behavior;
- whether the primary theorem is empirical-set or population utility;
- a justified dependence factor `chi` for any population claim;
- neighboring-dataset unit tests for every preprocessing path;
- null, positive, harmful, sparse-count, and high-client-count synthetic
  regimes; and
- a Go/No-Go gate fixed before synthetic outcomes.

## Evidence access

R1 used no real graph outcome, opened no sealed P3 test, reused no P5FC
confirmatory record as evidence, and acquired no future source.

R2 remains synthetic-only. Real development data are not authorized until the
accountant, sensitivity tests, and synthetic false-activation gate pass.
