# P5F Privacy-Utility Frontier Validation Report

## Decision

`FRONTIER_INDEX_SUPPORTED_FOR_FRESH_VALIDATION`

This is a retrospective development result, not confirmatory evidence and not
authorization to open the encrypted P3 test payload. The next admissible step
is a frozen evaluation on graph sources not used to formulate this frontier.

## Execution and audit

- Six ordinary graph domains, five seeds, five epsilon values, and two server
  visibility models produced 300 unique validation records and 60 aggregate
  cells.
- The visible-message branch reproduced every prior P3 GAP-style Global,
  Intra, and Cross AUC exactly; maximum error was zero.
- The exact RDP curve was independently recalculated for every budget and hop
  count. Add/remove undirected-edge sensitivity remained `sqrt(2)`.
- Expected first-hop noise energy under visible messages was exactly five
  times ideal secure aggregation, matching the frozen five-client design.
- Every observed signal-energy ratio respected its row-degree upper bound.
- The encrypted P3 test remained untouched.

The first audit invocation stopped because its backbone check conflated the
requested SVD width with the actual width when the public feature matrix had
fewer columns. The correction is documented in
`P5F_AUDIT_CORRECTION_NOTE.md`; no record, random stream, gate, or result was
changed. The corrected independent audit passed every check.

## Retrospective evidence

Across dataset, epsilon, and visibility cells, Spearman correlation between
`log10(F_signal)` and mean Global-AUC gain over public cosine was:

| Cells | n | Spearman rho | p-value |
|---|---:|---:|---:|
| All | 60 | 0.769 | 6.89e-13 |
| Visible client messages | 30 | 0.758 | 1.20e-6 |
| Ideal secure aggregation | 30 | 0.748 | 2.00e-6 |

The result captures a trust-model shift rather than a new learning method.
Ideal secure aggregation removes the factor-five noise-energy penalty and
therefore shifts `log10(F_signal)` upward by `log10(5)`, approximately 0.699,
at matched epsilon. This often moves a release from harmful to useful: for
Facebook-MUSAE at epsilon 8, mean Global gain changes from -0.021 under visible
messages to +0.006 under ideal secure aggregation.

The frontier is not a universal AUC threshold. Domain-specific public-feature
strength and score geometry remain important. BlogCatalog is beneficial even
at the strongest evaluated privacy setting, whereas Facebook remains below
its public baseline over most cells. The admissible claim is therefore that
the index is a useful cross-condition feasibility diagnostic, subject to
fresh-source validation, not that it determines utility or guarantees AUC.

## Next gate

Before any manuscript claim or figure is promoted, freeze a fresh-source
protocol with at least one social and one blog network that were not used in
P1--P5F development. The protocol must pre-register source hashes, splits,
five seeds, epsilon values, both visibility models, the unchanged decoder and
RDP accountant, correlation gates, and zero test access until the runner and
audit are committed. Failure rejects the general frontier claim.
