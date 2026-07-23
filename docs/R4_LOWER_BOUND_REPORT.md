# R4 Lower-Bound Report

## Decision

`R4_GO_TIGHT_FEASIBILITY_THEORY`

This decision means **rate-matched central feasibility theory**, not
constant-tight minimax optimality and not authorization of a real-data utility
method.

## Executed grid

- 40 analytical cells
- Effect gaps: 0.01, 0.03, 0.08, and 0.18
- Epsilon: 0.5, 1, 2, 4, and 8
- Delta: `1e-6`
- Dependence factors: one and five
- Maximum testing error: 0.05
- No real graph or held-out test data accessed

The independent audit exactly replayed every record and summary.

## Numerical checks

Every registered check passed:

- positive non-private lower bounds;
- DP root residual at most `7.98e-12`;
- correct monotonicity in effect, epsilon, and dependence;
- every R3 sufficient count exceeded the corresponding R4 necessary count;
- finite outputs and no real-data access.

Across the registered finite grid, the ratio

`R3 sufficient count / R4 necessary count`

ranged from 8.03 to 16.58. The bounds are therefore separated by nontrivial
constants but agree in principal asymptotic order.

## Representative cells

For `chi = 1`:

| epsilon | Gap alpha | Necessary count | R3 sufficient count | Ratio |
|---:|---:|---:|---:|---:|
| 1 | 0.01 | 32,377 | 267,642 | 8.27 |
| 1 | 0.03 | 3,595 | 31,505 | 8.77 |
| 1 | 0.08 | 504 | 5,052 | 10.04 |
| 1 | 0.18 | 98 | 1,245 | 12.72 |
| 4 | 0.01 | 32,377 | 261,790 | 8.09 |
| 4 | 0.03 | 3,595 | 29,562 | 8.23 |
| 4 | 0.08 | 504 | 4,330 | 8.60 |
| 4 | 0.18 | 98 | 928 | 9.48 |

At the evaluated privacy budgets, the non-private sampling obstruction
dominates the finite-constant DP Le Cam term. The privacy term nevertheless
recovers the required `1 / (epsilon alpha)` order in the pure-DP corollary.

## Claim boundary

Admissible:

- `Omega(chi / alpha^2)` non-private necessary count;
- a general central approximate-DP implicit lower bound;
- `Omega(1 / (epsilon alpha))` pure-DP privacy order;
- rate matching with R3 in `alpha`, `epsilon`, and `chi`, up to logarithms and
  constants.

Not admissible:

- constant-tight minimax optimality;
- generic `sqrt(K)` visible-message lower bound;
- direct AUC lower bound;
- a claim that CertFed-LP is a successful real-graph utility method.

## Top-journal assessment

R4 closes the central theoretical loop that was missing after R3. However, the
core reduction uses established DP Le Cam machinery. Top-journal novelty will
depend on the graph-specific layer that follows:

1. justify or estimate the dependence factor for federated edge utilities;
2. map real graph regimes to the theoretical phase boundary under a frozen
   protocol;
3. show that the boundary predicts feasible and infeasible regimes better than
   simpler sample-size heuristics;
4. retain the strict deployment and transcript privacy scope.

R4 is therefore a genuine advance from `THEORY_ONLY` toward a publishable
feasibility theory, but it is not by itself an Accept-level paper.
