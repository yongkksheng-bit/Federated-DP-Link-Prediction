# R3 Monte Carlo Calibration Protocol

## Purpose

This protocol tests the frozen R3 sufficient sample-complexity boundary on
fresh synthetic bounded utility records. It does not tune the boundary and does
not use R2 outcomes to change the theorem constants.

## Grid

- Population effects: 0.05, 0.10, and 0.20
- Safety effects: 0 and 0.019, both below `gamma = 0.02`
- Certification epsilon: 1 and 4
- Clients: five
- Transcript models: ideal secure aggregation and visible client messages
- Dependence factors: one and five
- Counts: 0.25, 0.5, 1, and 2 times the predicted sufficient count
- Trials per cell: 3,000
- Fresh base seed: 20260803

Counts are rounded upward to a multiple of the dependence factor. The utility
distribution is the preregistered block-replicated Rademacher model.

## Gates

1. At every predicted sufficient boundary, the one-sided 95% lower confidence
   bound on activation power must be at least 0.90.
2. Across every safety cell, the one-sided 95% upper confidence bound on false
   activation must be at most 0.06.
3. Every effect/privacy/transcript/dependence cell must show an empirical 90%
   power transition on the registered count grid.
4. The predicted sufficient count may be at most four times the smallest
   registered count attaining 90% empirical power. This is a conservatism gate,
   not an assertion that the sufficient bound is necessary.
5. The accountant must reproduce target epsilon within `1e-10`.
6. All outputs must be finite, and real or held-out graph data access is
   prohibited.

Passing advances only to the R3 decision audit. It does not authorize a
real-data method claim by itself.
