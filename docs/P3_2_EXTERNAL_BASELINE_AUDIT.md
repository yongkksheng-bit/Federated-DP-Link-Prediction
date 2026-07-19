# P3.2 External Baseline Audit

## Scope

P3.2 admits external methods only after matching the protected adjacency,
released output, adversary, sensitivity, composition, and RDP conversion. It
uses P3 development and validation arrays only. The sealed P3 test remains
inaccessible until every baseline and analysis script is frozen.

## ICDE 2024 DPLP

The relevant DPLP is Ran et al., *Differentially Private Graph Neural Networks
for Link Prediction* (ICDE 2024), not the distinct protected-connections
ranking method of De and Chakrabarti (AAAI 2021).

ICDE DPLP projects the graph to bounded degree, extracts positive and sampled
negative target-link subgraphs, bounds how many clipped per-subgraph gradients
one edge can influence, and applies a sampled Gaussian DP-SGD mechanism. Its
path-subgraph variant reduces this edge-influence multiplicity. No verified
official implementation was located in this audit. A faithful reproduction
therefore remains blocked until the path extractor, negative sampler,
edge-influence bound, and sampler-specific RDP accountant agree in code.

DPLP is centralized and assumes a trusted curator. Even after reproduction,
its nominal epsilon cannot be called adversary-matched to individually visible
federated client messages. It will be labeled as a centralized formal edge-DP
baseline with a disclosed scope difference.

## GAP-style LP adaptation

GAP separates a graph-independent public encoder from cached noisy neighborhood
aggregations and graph-independent downstream prediction. The official method
targets node classification. P3.2 adapts only its audited mechanism principle:
public row-bounded encodings, perturb-message-normalize aggregation, caching,
and graph-free pair scoring.

For GAP's directed aggregation convention, changing one adjacency entry changes
one row and has L2 sensitivity one. P3 protects one canonical **undirected**
edge. Removing `{u,v}` changes the aggregation of `u` by the bounded vector of
`v` and the aggregation of `v` by the bounded vector of `u`. The full released
matrix therefore has sensitivity

`sqrt(||x_u||_2^2 + ||x_v||_2^2) <= sqrt(2)`.

P3.2 consequently calibrates every hop at sensitivity `sqrt(2)` and composes
the hops sequentially. Each edge has one client owner, so the primary
visible-message transcript uses parallel composition across clients. Every
client perturbs its full local aggregation matrix before transmission. The
implementation samples the server's summed noise directly as
`N(0, K sigma^2 I)`, which is distribution-equivalent to summing `K`
independent client noises and does not alter the visible-message adversary or
the reported logical communication. The server caches the summed DP channels;
all candidate scores are post-processing
of these channels and registered public descriptors, with no private-graph
reread.

This row is named **GAP-style inference-closed LP adaptation**, never GAP or an
official reproduction. Its public projection dimension and hop count are
selected at epsilon 4 from the frozen grid in
`configs/p3_external_baselines.json`; ties prefer fewer hops and then the
smaller release.

## Admission state

| Track | Mechanism verified | Accountant verified | P3.2 status |
|---|---:|---:|---|
| GAP-style LP adaptation | yes | yes, fixed-query Gaussian RDP | admitted to validation |
| ICDE 2024 DPLP | paper only | no sampler-specific rederivation yet | blocked from result table |

Neither baseline may access the P3 test during P3.2.

## Closest admissible centralized fallback

Because ICDE DPLP cannot yet be faithfully reproduced, P3.2 also admits a
conservative formal fallback under the protocol's "DPLP or closest" clause. It
is a centralized edge-DP logistic pair classifier over bounded public pair
features and must not be called DPLP.

Training contains every positive training edge and an equal-size stable
negative set obtained from a graph-independent pseudorandom proposal stream.
Adding an edge inserts one positive record. If that edge occupied the stable
negative set, it also removes that negative and admits the next proposal. Thus
at most three clipped record gradients change, giving per-step L2 sensitivity
`3C`. The implementation uses full-batch gradients, adds Gaussian noise at
this sensitivity for each of 20 adaptive steps, and composes the complete RDP
curve. Its final model scores public pair features without rereading the graph.

This baseline assumes a centralized trusted curator. Its `(epsilon, delta)` is
formally valid for that output but is an explicitly disclosed adversary-scope
mismatch to the primary individually visible federated transcript.
