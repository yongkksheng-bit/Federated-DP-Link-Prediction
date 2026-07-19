# P3R-v2 Budget-Coupled Joint Release Protocol

## Hypothesis

P3R-v1 showed that a low-dimensional random identity sketch cannot reliably
replace semantic aggregation under visible-message noise. P3R-v2 instead
retains each dataset's already frozen strongest GAP-style semantic backbone and
adds the 1,088 structured, public-score-conditioned edge statistics validated
in P2.2. The two private signals share one Gaussian query rather than consuming
two privacy budgets.

## Joint query and exact sensitivity

Let `G(D)=A Z` be the one-hop undirected semantic aggregation with row-bounded
public encoding `Z`; its add/remove-edge L2 sensitivity is `sqrt(2)`. Let
`H(D)` be the conditioned histogram in which each canonical edge increments
exactly one coordinate; its sensitivity is one.

For histogram energy fraction `gamma` in `(0,1)`, release

`Q_gamma(D) = [sqrt(1-gamma) G(D), sqrt(2 gamma) H(D)]`.

One edge changes disjoint coordinates in the matrix and histogram blocks, so

`Delta_2(Q_gamma)^2 <= 2(1-gamma) + 2 gamma = 2`.

Thus every first-hop candidate has the same exact `sqrt(2)` sensitivity as the
GAP-style first hop. For a frozen two-hop backbone, the second query aggregates
the normalized private first-hop semantic channel and is another adaptive
`sqrt(2)` Gaussian query. The RDP accountant composes exactly the same number
of releases as that GAP backbone.

Under the primary visible-message adversary, every client perturbs its complete
scaled local joint vector. Because canonical edge ownership is disjoint across
clients, privacy composes in parallel across clients. The implementation may
sample the server sum with standard deviation `sqrt(K) sigma`, which is exactly
distribution-equivalent to summing `K` independent client noises.

## Inference

The noisy semantic block is divided by its public scale, normalized, and used
by the frozen GAP cosine decoder. The noisy histogram is divided by its public
scale and transformed into clipped log enrichment. The final score is

`s_GAP(u,v) + lambda r_hist(u,v)`.

All operations after the joint release are post-processing. Prediction never
rereads private edges.

## Frozen development discipline

The semantic dimension and hop count are copied from the completed P3.2 GAP
validation and are not retuned. Only five histogram energy fractions and five
bounded residual weights are searched. Leave-one-seed-out nested selection
uses four seeds to choose `(gamma, lambda)` and reports the fifth. The unchanged
P3R gates require three significant dataset wins, macro Global and Cross gains
of at least 0.02, and no dataset mean loss worse than 0.01.

The old P3 encrypted test remains inaccessible. A GO authorizes only a new
fresh-source confirmatory protocol, not a test run or a novelty claim.
