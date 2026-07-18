# P1 Block-Release Feasibility Derivation

## Query and sensitivity

For public groups `a<=b`, let `C_ab(D)` count private training edges whose
endpoints belong to that block pair. The vector `C(D)` has one coordinate per
unordered group pair. Under add/remove-edge adjacency, one canonical edge
changes exactly one coordinate by one, hence

`||C(D)-C(D')||_2 = 1`.

The Gaussian release is `Y=C(D)+N(0,s^2 I)`. Ideal secure aggregation uses
`s=sigma`. If all `K` individually visible client messages are independently
calibrated with standard deviation `sigma`, their released sum has
`s=sqrt(K)*sigma`, while the joint transcript remains edge-DP by parallel
composition because edge ownership is disjoint.

## Density signal and uncertainty

Let `M_ab` be the number of possible pairs in block `(a,b)`, `p_ab` its true
edge probability, and `r` the probability that an existing edge is retained in
the private training graph. The released density is

`p_hat_ab = Y_ab/M_ab`,

with expectation `r*p_ab`. Ignoring clipping at zero and one, its variance is

`Var(p_hat_ab) = r*p_ab*(1-r*p_ab)/M_ab + s^2/M_ab^2`.

For two block types `a` and `b`, the mean score separation is

`Delta_mu = r*(p_a-p_b)`.

Under a normal approximation, a sufficient pairwise separation condition at
one-sided quantile `z` is

`Delta_mu > z * sqrt(Var(p_hat_a)+Var(p_hat_b))`.

This exposes the feasibility variables required by P0: release dimension
enters through the number and capacities of blocks; sensitivity is one; server
visibility changes `s` by `sqrt(K)`; repeated releases replace the one-step
RDP curve by its adaptive sum; and small blocks are penalized by both
`M^-1/2` sampling error and `M^-1` DP error.

## Interpretation of the P1 result

Both frozen domains satisfy the empirical gate at `(epsilon,delta)=(4,1e-6)`.
The result demonstrates an existence regime for a low-dimensional public-group
statistic. It does **not** establish that public groups exist with comparable
quality in real graphs, that block counts are a publishable final mechanism,
or that a GNN will inherit this utility. The small visible-message penalty in
P1 follows from large block capacities; it must not be generalized to
high-dimensional updates or sparse workloads.

P1 therefore authorizes the next synthetic question: how utility changes with
block resolution, client count, privacy budget, and misspecified public groups,
while retaining the same inference-closed output contract.
