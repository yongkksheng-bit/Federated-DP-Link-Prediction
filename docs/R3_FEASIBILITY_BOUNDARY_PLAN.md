# R3 Feasibility Boundary Plan

## Motivation

R2 separates two facts:

1. the one-sided private utility certificate is statistically valid; and
2. the end-to-end graph protocol does not supply enough certification edges or
   enough utility gain for that certificate to activate.

Opening another adaptive model search would repeat the failure pattern that this
repository was created to prevent. R3 therefore studies the feasibility
boundary before authorizing any new real-data method experiment.

## Primary question

For a bounded per-edge utility advantage with population mean `Delta`, determine
the minimum certification count required to prove

`Delta >= gamma`

under:

- certification privacy budget `(epsilon_cert, delta_cert)`;
- Gaussian release of a bounded utility sum and private count;
- ideal secure aggregation or individually visible client messages;
- `K` clients;
- dependence factor `chi`;
- fixed one-sided failure allocation.

The result must distinguish theorem-guaranteed sufficient conditions from
empirical power estimates.

## Registered analytical object

Let `s_tilde` and `n_tilde` be the private sum and count, let `b_s` and `b_n`
be simultaneous Gaussian error radii, and let `beta_sampling` be the sampling
failure probability. The existing certificate activates only if

`(s_tilde - b_s) / (n_tilde + b_n)`

`- sqrt(2 chi log(1 / beta_sampling) / (n_tilde - b_n)) >= gamma`,

with positive and sufficiently large denominator bounds.

R3 will derive and numerically verify:

1. a sufficient minimum-count function
   `n_min(Delta, gamma, epsilon_cert, delta_cert, K, visibility, chi)`;
2. its monotonicity in effect size, privacy budget, client count, and
   dependence;
3. a non-private lower limit showing when sampling uncertainty alone makes
   activation impossible;
4. an ideal-secure-aggregation versus visible-message separation;
5. an inverse boundary giving the minimum detectable utility gain at a fixed
   certification count.

## Work packages

### R3.1 Formal derivation

- State all probability spaces and conditioning assumptions.
- Derive a deterministic sufficient condition on the true count and mean.
- Prove the simultaneous coverage statement.
- State explicitly that the result certifies the registered bounded utility,
  not AUC and not unrestricted deployment outputs.

### R3.2 Numerical boundary solver

- Implement a monotone root solver for minimum certification count.
- Cross-check the solver against brute-force integer search.
- Cover both transcript models and the full registered RDP accountant.
- Record all constants, RDP orders, sensitivities, and failure allocations.

### R3.3 Synthetic calibration

- Reuse no outcomes from R2 to choose thresholds.
- Compare predicted minimum counts with fresh Monte Carlo activation power.
- Require calibrated safety and a prespecified error tolerance between the
  predicted and empirical transition regions.

### R3.4 Decision audit

Before any real-data access, classify the route:

- `FEASIBLE`: registered graph-scale counts and plausible effect sizes exceed
  the boundary with margin;
- `THEORY_ONLY`: the boundary is valid and informative, but realistic graph
  cells are below it;
- `INVALID`: coverage, monotonicity, or calibration fails.

Only `FEASIBLE` authorizes a new preregistered method protocol. `THEORY_ONLY`
authorizes a feasibility-boundary paper direction, not a utility-improvement
claim. `INVALID` closes the route.

## Stop rules

- Do not lower `gamma` after seeing R2.
- Do not reallocate failure probabilities to optimize R2 outcomes.
- Do not increase graph size merely until a desired activation appears.
- Do not access real graph labels or held-out tests during R3.
- Do not describe a conservative fallback with zero activation as a successful
  link-prediction method.
- Any change to the privacy unit, trust model, or released output requires a new
  P0 problem-definition audit.

## Publication interpretation

R3 can support a rigorous paper only if the boundary itself is novel,
theoretically sound, and empirically calibrated. It would reposition the work
from "a private method that always improves utility" to "when private
federated link-prediction adaptation is statistically certifiable, and when it
is not." The fixed paper title remains compatible with this scope, but the
abstract and contribution claims must follow the final R3 decision rather than
precede it.
