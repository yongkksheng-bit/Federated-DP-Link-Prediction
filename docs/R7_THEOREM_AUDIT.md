# R7 Theorem Audit

Audit date: 2026-07-24 (Asia/Shanghai).

## Verdict

`PASS_WITH_NARROWED_ASSUMPTIONS`

The executable accountant and frozen R5 decision reconstruct exactly. The
theorem chain is defensible only under the explicitly registered
role-labelled adjacency and computational randomization contract. R7 does not
upgrade either condition.

## Independent executable checks

The R7 auditor reads the tracked strict-JSON export rather than importing the
R5 runner's summary function.

- 1500/1500 privacy-grid records are present and uniquely keyed.
- The primary summary, all 50 diagnostic cells, all gates, and the final
  decision reconstruct with no differences.
- Every composed RDP curve equals the order-wise sum of its stored training
  and certification curves; maximum absolute discrepancy is `0`.
- Every reported epsilon reproduces from its stored RDP curve to `1e-12`.
- Exhaustive extreme-point enumeration gives certification-query sensitivity
  `sqrt(2)`.
- Endpoint corruption receives no graph/adjacency input and calls no graph
  loader or adjacency constructor.

Machine-readable result:
`results/r7_independent_audit/theory_contract.json`.

## Privacy theorem

The adaptive max-RDP result is valid when the public role assignment is
edge-stable and one neighboring role-labelled edge affects only one role.
R5 conservatively reports the sequential sum on the registered role-labelled
database.

Sequential summation does **not** prove privacy for a raw graph before an
unstable partition. R7 removed wording that could be read as making that
upgrade. The manuscript now states:

1. the protected record includes its frozen role label;
2. the R5 sum declines parallel-composition credit; and
3. raw pre-partition graph adjacency is outside the reported R5 guarantee.

## Finite-population theorem

Conditional on a fixed training release, fixed sealed population, and fixed
certification count, a genuinely independent Bernoulli assignment yields a
uniform subset and the Serfling step is sound. Shared endpoints do not change
that conditional finite-population argument.

The implementation uses edge-keyed SHA-256 with a fixed salt. Independence is
therefore a registered random-oracle/PRF-style assumption, not an
information-theoretic property of deterministic SHA-256. The sealed R5
population was fixed before the salt was frozen and opened, preventing
post-salt adaptive population construction in this experiment.

For production, use a committed PRF key hidden from data providers until the
population is frozen, or an auditable random draw after population freeze.

## Feasibility and lower bound

The sufficient and necessary rates match only in principal dependence:

`chi / alpha^2 + 1 / (epsilon alpha)`.

The visible-message `sqrt(K)` term is specific to this independent-message
implementation. Constants, approximate-DP logarithms, and the registered hard
instance remain outside the headline claim. No theorem maps these rates to
future-edge ROC-AUC.

## Remaining external-review requirement

R7 is an internal independent implementation audit. A privacy/statistics
expert who did not author the code should still re-derive Theorems 2--4 before
submission. This is a governance requirement, not a failed mathematical gate.
