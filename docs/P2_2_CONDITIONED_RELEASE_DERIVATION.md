# P2.2 Public-Score-Conditioned Release

## Motivation

P2.1 established that a public-cell count release can add material utility on
PolBlogs but leaves too little within-cell resolution on LastFM. P2.2 tests one
specific repair: condition the same count query on a fixed public cosine-score
bin. This is a refinement of the released statistic, not a new private model.

## Frozen query

Let `c(u)` be a public cell assignment and `b(s0(u,v))` a fixed bin of the
public descriptor cosine score. For every unordered cell pair `(a,d)` and bin
`r`, release

`q[a,d,r] = sum_{(u,v) in E_train} 1[{c(u),c(v)}={a,d}] 1[b(s0(u,v))=r]`.

All cells, descriptors, score bins, candidate pairs, and capacity samples are
public and edge independent. Public stratum capacities are estimated from a
deterministic sample of the public node-pair universe with symmetric Dirichlet
smoothing. They do not inspect the private edge set.

## Exact edge sensitivity

Under add/remove adjacency of one canonical undirected edge, exactly one
coordinate of `q` changes by exactly one. Therefore

`||q(E) - q(E')||_2 = 1`.

The vector dimension (544 for four bins or 1,088 for eight bins) does not alter
this sensitivity. With individually visible client messages, every client
applies a sensitivity-one Gaussian mechanism. Because canonical edges have one
owner and neighboring datasets differ at one owner, parallel composition gives
the same record-level `(epsilon, delta)` guarantee for the visible transcript.
Ideal secure aggregation is secondary and is not used for the development gate.

## Inference closure

No private graph, degree, neighborhood, or unnoised count is required after the
release. A candidate score is

`s(u,v) = s0(u,v) + lambda * R[c(u),c(v),b(s0(u,v))]`,

where `R` is a clipped log-enrichment computed only from the noisy vector and
public capacity estimates. Hence all scores are post-processing of public
objects and the one DP release. Public embedding or unrestricted score release
is not implied by this development experiment.

## Development-only decision

P2.2 may read only the existing development/validation payloads for
BlogCatalog-v3, Facebook-MUSAE, PolBlogs, and LastFM-Asia. No prior test payload
may be accessed. Candidate selection maximizes the worst 5-seed mean gain over
public cosine across Global and Cross AUC on all four domains. Advancement
requires positive mean gain in all eight cells and at least `+0.01` mean gain on
both LastFM metrics. Passing this gate authorizes registration of entirely new
confirmatory sources; it does not authorize reuse of an old test.
