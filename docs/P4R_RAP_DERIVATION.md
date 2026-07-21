# P4R Method Pivot: Reciprocal Affinity Profile Release

## Missing information in prior candidates

The GAP-style baseline releases a node's semantic neighbor aggregate. P3R-v2
adds a global cell-pair/score-bin statistic. Neither object represents a
specific node's propensity to connect to the public semantic type of the other
endpoint. P4R introduces that node-level reciprocal signal and does not extend
the rejected P3R parameter grids.

## Private statistic

Let `c(v)` be a fixed public cell label. Define the reciprocal affinity profile

`M[u,j] = sum_{v: {u,v} in E} 1[c(v)=j]`.

For candidate pair `(u,v)`, the two directional entries `M[u,c(v)]` and
`M[v,c(u)]` directly describe mutual link-formation preference. The scorer
uses a public cell-frequency prior, nonnegative post-processing, noise-aware
reliability shrinkage, and a symmetric clipped log-lift. It never rereads the
private graph.

## Exact sensitivity and budget coupling

Adding canonical edge `{u,v}` changes exactly `M[u,c(v)]` and `M[v,c(u)]` by
one, hence `Delta_2(M)=sqrt(2)`. A row-bounded semantic aggregation `G=AZ` also
has sensitivity `sqrt(2)`. For profile energy `gamma`, release

`Q_gamma(D) = [sqrt(1-gamma) G(D), sqrt(gamma) M(D)]`.

The blocks occupy disjoint coordinates, so

`Delta_2(Q_gamma)^2 <= 2(1-gamma) + 2 gamma = 2`.

Thus RAP adds an LP-specific node-level statistic without increasing the
per-release sensitivity over GAP. Under visible client messages, each client
perturbs its complete local query and the server-sum noise is distributionally
`N(0, K sigma^2 I)`. All normalization, shrinkage, and pair scoring are DP
post-processing.

## Scientific status

RAP is a working hypothesis, not a paper contribution yet. Neighbor-type
distributions are not new in graph learning, and aggregation perturbation is
not new in edge-DP. The potentially defensible contribution is narrower: a
federated, inference-closed, edge-DP joint release and reciprocal LP decoder
under the frozen visible-message threat model. A targeted full-text novelty
audit remains mandatory before manuscript claims.

P4R begins with a frozen synthetic feasibility gate. No P3 validation or test
data may be accessed until the mechanism beats matched GAP on the synthetic
regimes for which node-specific affinity is information-bearing.
