# R4 Lower-Bound Contract

## Statistical decision problem

R4 studies the same bounded target-domain utility object used by the R1
certificate. For a fixed material threshold `gamma`, define

`H0: Delta = gamma`

and

`H1: Delta = gamma + alpha`,

where `alpha > 0`. The hard pair consists of Rademacher utility records in
`{-1, +1}` with positive probabilities

`p0 = (1 + gamma) / 2`,

`p1 = (1 + gamma + alpha) / 2`.

A successful selector must have both false-activation and missed-benefit
probabilities at most `eta = 0.05`.

## Dependence model

For dependence factor `chi`, `n / chi` independent Rademacher draws are each
replicated `chi` times. The non-private information is therefore that of
`n / chi` independent blocks. This is a hard subclass, not a model for every
graph.

## Adjacency conversion

The project uses unbounded add-or-remove-one-edge adjacency. The fixed-size
hypothesis-testing literature commonly uses replacement adjacency. Replacing
one record can be implemented by one removal followed by one addition.
Accordingly, an `(epsilon, delta)` unbounded-DP transcript is treated as

`(2 epsilon, (1 + exp(epsilon)) delta)`

replacement-DP by two-record group privacy. R4 will report this conversion
explicitly rather than silently mixing adjacency conventions.

## Lower-bound layers

### Layer 1: non-private minimax bound

For the block-replicated hard pair, the product KL divergence is

`(n / chi) KL(Ber(p0) || Ber(p1))`.

Le Cam's method and Pinsker's inequality imply that testing error at most `eta`
requires

`n >= chi * 2 (1 - 2 eta)^2 / KL(Ber(p0) || Ber(p1))`.

This gives the necessary `Omega(chi / alpha^2)` sampling term.

### Layer 2: general central approximate-DP bound

R4 applies Theorem 1 of Acharya, Sun, and Zhang, "Differentially Private
Assouad, Fano, and Le Cam," ALT 2021. Under maximal coupling, the expected
replacement Hamming distance is

`D = n alpha / 2`.

Any replacement `(epsilon_r, delta_r)`-DP test satisfies

`Pe >= 0.5 max{1 - TV,`

`                  0.9 exp(-10 epsilon_r D) - 10 D delta_r}`.

Thus error at most `eta` requires the second expression to be at most
`2 eta`. R4 solves this monotone inequality for the smallest necessary `D` and
converts it to a sample lower bound.

For pure DP this recovers an `Omega(1 / (epsilon alpha))` privacy term. For
approximate DP the registered finite-delta expression is used directly.

### Layer 3: transcript-model separation

Ideal secure aggregation and server-visible client messages both inherit the
general central-DP lower bound. A stronger `K`-dependent lower bound for visible
messages requires an explicit distributed communication model.

The current implementation's `sqrt(K)` aggregate noise is a property of
independent per-client Gaussian messages. It is not registered as a minimax
lower bound over arbitrary correlated or interactive protocols.

## Go/no-go rule

R4 may claim a matching feasibility theory only if:

1. the central lower and R3 upper bounds match in their principal dependence on
   `alpha`, `epsilon`, and `chi`;
2. all adjacency and confidence conversions are explicit;
3. either a valid visible-message separation is proved under a frozen
   communication model or that separation is removed from the general claim;
4. numerical constants reproduce the analytical inequalities;
5. no real or held-out graph data are accessed.

Failure does not invalidate R3. It means the sufficient boundary remains an
upper bound without a matching minimax characterization.
