# R4 Necessary Sample-Complexity Theorem

## Theorem

Fix `gamma in (-1, 1)`, an effect gap `alpha > 0` with
`gamma + alpha < 1`, a maximum testing error `eta in (0, 0.45)`, and a
dependence factor `chi >= 1`.

Consider the block-replicated Rademacher hard pair:

- under `H0`, each independent block is positive with probability
  `p0 = (1 + gamma) / 2`;
- under `H1`, each independent block is positive with probability
  `p1 = (1 + gamma + alpha) / 2`;
- there are `n / chi` independent blocks and every block is repeated `chi`
  times.

Let a selector be `(epsilon, delta)`-DP under unbounded add-or-remove record
adjacency and have worst-case testing error at most `eta`.

Define

`epsilon_r = 2 epsilon`,

`delta_r = (1 + exp(epsilon)) delta`,

and let `D_star` be the smallest nonnegative solution of

`0.9 exp(-10 epsilon_r D) - 10 D delta_r <= 2 eta`.

Then a necessary condition for such a selector is

`n >= max {`

`  2 chi (1 - 2 eta)^2 / KL(Ber(p0) || Ber(p1)),`

`  2 D_star / alpha`

`}`.

The first term is non-private and the second is the additional central-DP
testing obstruction delivered by the approximate-DP Le Cam inequality.

## Proof

### Non-private term

The two distributions contain `n / chi` independent Bernoulli blocks, so

`KL(P0 || P1) = (n / chi) KL(Ber(p0) || Ber(p1))`.

Classical Le Cam gives

`Pe >= (1 - TV(P0, P1)) / 2`.

If `Pe <= eta`, then `TV(P0, P1) >= 1 - 2 eta`. Pinsker's inequality gives

`TV(P0, P1) <= sqrt(KL(P0 || P1) / 2)`.

Combining and rearranging proves the first necessary count.

### Privacy term

One replacement can be represented by one removal and one addition. Two-step
group privacy converts the project mechanism into replacement
`(epsilon_r, delta_r)`-DP with the parameters above.

Under maximal coupling of `Ber(p0)` and `Ber(p1)`, a block differs with
probability

`|p1 - p0| = alpha / 2`.

When it differs, all `chi` replicated records differ. Across `n / chi` blocks,
the expected replacement Hamming distance is therefore

`D = (n / chi) chi alpha / 2 = n alpha / 2`.

The approximate-DP Le Cam theorem of Acharya, Sun, and Zhang gives

`Pe >= 0.5 [0.9 exp(-10 epsilon_r D) - 10 D delta_r]`.

For `Pe <= eta`, the bracketed expression must be at most `2 eta`. Hence
`D >= D_star` and `n >= 2 D_star / alpha`.

## Pure-DP corollary

When `delta = 0`,

`D_star = log(0.9 / (2 eta)) / (20 epsilon)`,

because `epsilon_r = 2 epsilon`. Thus

`n >= log(0.9 / (2 eta)) / (10 epsilon alpha)`.

For fixed `gamma` and small `alpha`,

`KL(Ber(p0) || Ber(p1))`

`= alpha^2 / [2 (1 - gamma^2)] + O(alpha^3)`.

The necessary count therefore has order

`Omega(chi / alpha^2 + 1 / (epsilon alpha))`.

## Comparison with R3

At fixed confidence allocations, the R3 Gaussian certificate has sufficient
count of order

`O(chi / alpha^2`

`  + sqrt(log(1 / delta)) / (epsilon alpha))`.

Therefore the upper and lower bounds match in their principal dependence on
`alpha`, `epsilon`, and `chi`, up to constants and privacy/confidence logarithms.
The Gaussian/RDP construction is not claimed to be minimax optimal in its
`delta` dependence.

## Transcript scope

The theorem applies to every central edge-DP transcript, including a transcript
revealing only an ideal secure aggregate. It also applies to visible-message
protocols because they are a subclass of central-DP transcripts.

It does not prove an additional `K`-dependent penalty for visible messages.
Such a separation requires a separately defined communication and randomness
model. The project's observed `sqrt(K)` noise growth is retained only as a
mechanism-specific property of independent Gaussian client messages.

## Interpretation

This is a necessary condition for certifying a bounded target-domain utility
gap. It is not a lower bound directly on link-prediction AUC, and it does not
state that every graph supplies independent block-Rademacher evidence. The
connection to graph link prediction remains conditional on the registered
utility reduction and dependence model.
