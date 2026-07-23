# R1 Privacy Theorem

## Definitions

Let `D=(E_1,...,E_K)` and `D'` be add/remove-edge neighbors. A public
deterministic hash assigns each canonical edge to exactly one of `E^T`, `E^C`,
or `E^Q`.

The DP trainer releases server transcript and inference-closed state

`R <- M_T(E^T)`.

For every fixed possible `R=r`, the certification mechanism computes

`Q_C(E^C;r)=(S_r,n_C)`,

where each certification edge contributes `(d_r(e),1)` with
`d_r(e) in [-1,1]`. It releases an isotropic Gaussian perturbation and a
decision obtained by post-processing:

`C <- M_C(E^C;r)`.

Assume:

1. `M_T` is `rho_T(alpha)`-RDP for every registered order `alpha>1`;
2. for every fixed `r`, `M_C(.;r)` is uniformly `rho_C(alpha)`-RDP;
3. neither mechanism reads `E^Q`; and
4. deployed scores use only `(R,C)`, public inputs, and public randomness.

## Lemma 1: certification sensitivity

Under add/remove-edge adjacency and conditional on fixed `r`,

`Delta_2 Q_C <= sqrt(2)`.

### Proof

Adding or removing one certification edge changes `S_r` by one bounded
contribution whose absolute value is at most one. It changes `n_C` by exactly
one. Therefore the squared L2 change is at most `1^2+1^2=2`. Taking a square
root proves the result. The comparison-pair map must not perform
graph-dependent rejection; otherwise one edge could alter additional records.

## Lemma 2: certification RDP

Release

`Q_C(E^C;r) + N(0,2*sigma_C^2 I_2)`.

For every `alpha>1`, it satisfies

`rho_C(alpha) = alpha/(2*sigma_C^2)`

RDP.

### Proof

The Gaussian query has L2 sensitivity `sqrt(2)` and coordinate noise standard
deviation `sqrt(2)*sigma_C`. The basic Gaussian RDP bound is

`alpha*Delta_2^2/(2*sigma_abs^2)`.

Substitution gives `alpha*2/(2*2*sigma_C^2)`.

## Theorem 1: adaptive disjoint-edge composition

Under the definitions and assumptions above, the joint released transcript

`M(D)=(R, M_C(E^C;R), selected inference-closed score interface)`

satisfies

`rho_joint(alpha) = max{rho_T(alpha), rho_C(alpha)}`

RDP for every registered order.

Consequently, a valid conservative conversion is

`epsilon(delta) = min_alpha [
  rho_joint(alpha) + log(1/delta)/(alpha-1)
]`.

### Proof

A neighboring edge is assigned to one partition by a public rule.

If it lies in `E^T`, then `E^C` is identical. Conditional certification is the
same Markov kernel applied to the two possible training releases. Appending the
kernel and its decision is post-processing of `M_T`; the divergence is bounded
by `rho_T(alpha)`.

If it lies in `E^C`, the distribution of `R` is identical. Conditional on
every `R=r`, certification is bounded by `rho_C(alpha)` uniformly in `r`.
Integrating over the common distribution of `R` preserves that bound.

An edge in `E^Q` affects no released mechanism. The score interface is
post-processing by the inference-closed assumption. Taking the worst of the
only two affected cases yields the maximum.

## Corollary 1: primary visible-message model

Suppose client `k` releases an independently noised local query
`(S_k,n_k)`, each calibrated to L2 sensitivity `sqrt(2)`. The server sees all
`K` messages.

Because one neighboring edge changes one owner client's message, the
certification transcript remains `rho_C(alpha)`-RDP rather than
`K*rho_C(alpha)`. However, the server's aggregated sum contains noise variance
from all client messages. If every client uses coordinate variance
`2*sigma_C^2`, the aggregate coordinate variance is `2K*sigma_C^2`.

This is client-owner parallel composition, not privacy amplification.

## Corollary 2: ideal secure aggregation

If an ideal secure-aggregation functionality reveals only the global
`(S,n)` query with one central Gaussian perturbation of coordinate variance
`2*sigma_C^2`, the same certification RDP curve holds with lower aggregate
noise than the visible-message implementation.

Secure aggregation is a trust-model change. It does not strengthen the DP
definition by itself.

## Sequential-composition fallback

The maximum rule is invalid if:

- edge partitioning depends on private graph statistics;
- one canonical edge can enter both training and certification;
- certification reads an unprotected training state;
- conditional certification DP is not uniform over possible `R`; or
- inference rereads private graph state.

Without a proof of disjoint adaptive composition, the safe RDP fallback is

`rho_joint(alpha) <= rho_T(alpha)+rho_C(alpha)`,

plus every additional private release.

## Scope

The theorem protects the complete server-visible transcript, released state,
binary decision, and inference-closed score outputs. It does not protect raw
private-graph embeddings, unrestricted graph-backed APIs, or a publicly
released test metric unless those objects receive a separate valid mechanism.
