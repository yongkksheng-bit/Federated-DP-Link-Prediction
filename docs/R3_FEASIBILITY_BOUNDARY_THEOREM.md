# R3 Feasibility Boundary Theorem

## Setup

Let `U_1, ..., U_n` be bounded utility advantages in `[-1, 1]` with
population mean `Delta >= 0`. We assume the one-sided concentration condition

`P(mean(U) <= Delta - t) <= exp(-n t^2 / (2 chi))`,

where `chi >= 1` is a registered dependence factor. This includes the
block-replicated Rademacher model used in R2A and does not assert that arbitrary
graph-edge utilities are independent.

The private certification query is

`q(U) = (sum_i U_i, n)`.

Under add/remove-one-edge adjacency its L2 sensitivity is at most `sqrt(2)`.
The released query is

`S_tilde = sum_i U_i + Z_s`,

`N_tilde = n + Z_n`,

where `Z_s` and `Z_n` are independent centered Gaussians with common effective
standard deviation `nu`. Under ideal secure aggregation, `nu` is the standard
deviation of one aggregate query. If the server observes `K` independently
noised client messages, `nu = sqrt(K) sigma_client`.

Define

`b_s = nu Phi^{-1}(1 - beta_s / 2)`,

`b_n = nu Phi^{-1}(1 - beta_n / 2)`,

and

`a(n, beta) = sqrt(2 chi log(1 / beta) / n)`.

The operational certificate implemented in `private_certificate.py` is

`C = (S_tilde - b_s) / (N_tilde + b_n)`

`    - a(N_tilde - b_n, beta_v)`,

provided the lower numerator is positive and the private lower count exceeds
the registered minimum; otherwise `C = -infinity`.

## Coverage theorem

With probability at least

`1 - beta_s - beta_n - beta_v`,

the certificate satisfies `C <= Delta`.

Therefore activation at `C >= gamma` certifies the registered population
utility statement `Delta >= gamma` at the corresponding one-sided confidence
level. This statement concerns the bounded corrupted-pair utility registered in
R1. It is not a confidence interval for AUC and it does not protect an
unrestricted embedding or score release.

## High-probability activation theorem

Fix an additional power-failure probability `beta_p` and define

`a_p(n) = a(n, beta_p)`.

On the joint event

`mean(U) >= Delta - a_p(n)`,

`|Z_s| <= b_s`,

`|Z_n| <= b_n`,

the operational certificate is bounded below by

`B(n, Delta) =`

`[n (Delta - a_p(n)) - 2 b_s] / [n + 2 b_n]`

`- sqrt(2 chi log(1 / beta_v) / [n - 2 b_n])`.

The expression is defined only when `n - 2 b_n` exceeds the registered minimum
count and its numerator is positive.

Consequently, if

`B(n, Delta) >= gamma`,

then the certificate activates with probability at least

`1 - beta_p - beta_s - beta_n`.

If activation and coverage are required simultaneously, the joint success
probability is at least

`1 - beta_p - beta_s - beta_n - beta_v`.

### Proof sketch

The concentration assumption gives
`sum_i U_i >= n (Delta - a_p(n))` except with probability `beta_p`.
The two Gaussian events hold except with probabilities `beta_s` and `beta_n`.
On these events,

- `S_tilde - b_s >= sum_i U_i - 2 b_s`;
- `N_tilde + b_n <= n + 2 b_n`;
- `N_tilde - b_n >= n - 2 b_n`.

The registered numerator is positive, so replacing its denominator by the
larger upper bound decreases the ratio. The sampling penalty decreases with its
count argument. Substitution yields `C >= B(n, Delta)`. A union bound completes
the activation statement.

## Monotonicity

For `Delta >= 0` and `n > 2 b_n`, the ratio term in `B(n, Delta)` is increasing
in `n`; the sampling penalty is decreasing. Thus `B` is strictly increasing on
its valid domain. It is also:

- increasing in `Delta`;
- decreasing in `chi`;
- decreasing in the effective Gaussian noise radii.

These properties justify an exponential bracket followed by exact integer
binary search for the smallest sufficient certification count.

## Minimum detectable effect

At a fixed valid count `n`, solving `B(n, Delta) >= gamma` gives

`Delta_min(n) = a_p(n)`

`+ [2 b_s + (n + 2 b_n)`

`   (gamma + sqrt(2 chi log(1 / beta_v) / (n - 2 b_n)))] / n`.

This inverse boundary separates effect sizes for which the registered
certificate has a high-probability activation guarantee from those for which it
does not.

## Non-private lower limit

Setting `nu = 0` gives

`Delta_min_nonprivate(n) = gamma + a(n, beta_p) + a(n, beta_v)`.

This limit is important: even a perfect privacy mechanism cannot overcome an
insufficient certification sample. DP noise can only raise this boundary.

## Scope

The theorem is a sufficient condition, not a necessary condition. A cell below
the boundary may activate by chance, but it lacks the registered
high-probability power guarantee. R3 will test numerical implementation and
Monte Carlo calibration without using real graph outcomes.
