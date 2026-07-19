# P3R Dual-Sketch Method-Development Protocol

## Why P3R exists

P3.2 rejected the conditioned-count release as a Transactions-level primary
method because a GAP-style cached aggregation was substantially stronger on
several development domains. P3R does not retune that rejected method and does
not open the encrypted P3 test. The six P3 train/validation views are now used
only as method-development evidence. Any successful P3R candidate requires a
new, fresh-source confirmatory protocol.

## Candidate mechanism

For node `v`, let `z_v` be a graph-independent, row-normalized semantic
encoding of its registered public descriptors. Let `r_v` be a public
Rademacher signature derived only from the public node index, with entries
`+/- 1/sqrt(d_r)`. For semantic energy fraction `eta`, define

`q_v = [sqrt(eta) z_v, sqrt(1-eta) r_v]`.

Every row has norm at most one. Each client computes its local contribution to
the undirected one-hop sum `A Q`, adds calibrated Gaussian noise, and transmits
the noisy matrix. The primary server sees every client message. Since each
canonical edge has one owner, client mechanisms compose in parallel; the
server-summed noise has the distribution `N(0, K sigma^2 I)`.

The server caches the summed DP matrix. Candidate-pair scores combine public
semantic cosine, cosine between the private semantic aggregation blocks, and
one of two topology scores: cosine between topological blocks or a bounded
noise-standardized dot product. Inference uses only public inputs and this
cached release.

## Privacy lemma

Removing one undirected edge `{u,v}` changes row `u` of `A Q` by `q_v` and row
`v` by `q_u`. Therefore the Frobenius/L2 change of the complete matrix is

`sqrt(||q_u||_2^2 + ||q_v||_2^2) <= sqrt(2)`.

The complete candidate uses one fixed-sensitivity Gaussian release and the
same exact RDP conversion as P3.2 GAP-style. Decoder choices are
post-processing and consume no additional privacy budget.

## LP-specific topology lemma

Let `R` contain independent public Rademacher rows with entries
`+/-1/sqrt(d_r)`. Before Gaussian perturbation, the topology block is `A R`.
For distinct candidate nodes `u` and `v`,

`E_R[(A R)_u^T (A R)_v] = |N(u) intersect N(v)|`.

Cross terms between different neighbor identities have zero expectation and a
shared neighbor contributes one. Independent zero-mean Gaussian noise in
distinct output rows leaves the signed expectation unchanged. Thus the joint
release contains an explicit randomized common-neighbor estimator, an
LP-specific signal absent from a purely semantic GAP encoder. This is a local
mechanism statement, not yet a novelty or utility claim.

## Fair development discipline

Joint release dimension is at most 32, so gains cannot be obtained by making a
substantially larger private output than the strongest one-hop GAP settings.
All mechanism and decoder grids are frozen in
`configs/p3r_dual_sketch_development.json`.

Selection is leave-one-seed-out within each dataset: four seeds select one
configuration and the held-out seed evaluates it. Five held-out scores form
the paired interval against the already frozen P3.2 GAP-style scores. No result
from the encrypted P3 test is available to P3R.

P3R advances only if every preregistered gate passes: positive paired Global
and Cross 95% intervals on at least three datasets, macro gains of at least
0.02 on both primary metrics, and no dataset mean loss worse than 0.01. A
failure rejects this candidate rather than weakening the gates.
