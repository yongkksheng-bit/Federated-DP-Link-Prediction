# P0 Frozen Problem Definition

Frozen: 2026-07-18 (Asia/Shanghai).

This document fixes the scientific target. P1 may test mechanisms against this
contract but may not silently weaken it.

## Public universe and distributed private graph

Let `V` be a fixed public node universe, `X` fixed public node descriptors, and
`h: V -> {1,...,K}` a fixed public home-client map. The target is a simple
undirected homogeneous graph with private edge set

`E = disjoint_union(E_1, ..., E_K)`.

Each canonical edge `{u,v}` is stored by exactly one client under a fixed public
ownership rule `o(u,v)`. The rule and client/node membership do not depend on
whether any private edge exists. Duplicate storage is prohibited in the main
contract; a deduplication protocol would otherwise become part of the private
mechanism.

A candidate pair is **intra-client** when `h(u)=h(v)` and **cross-client** when
`h(u)!=h(v)`. Cross-client status is public metadata, not evidence that the
edge exists. Raw edges, degrees, neighborhoods, edge-derived partitions, and
edge-derived normalizers are private.

## Add/remove-edge adjacency

Federated datasets `D=(E_1,...,E_K)` and `D'` are neighbors, written `D~eD'`,
when they differ by one canonical edge record in exactly one client and all
public objects remain fixed. This is unbounded add/remove adjacency.

The protected individual is one relationship, not one node or one client. A
mechanism must account for every consequence of adding or removing that edge,
including negative sampling, minibatch membership, normalization, scheduling,
candidate construction, and repeated appearances in overlapping subgraphs.

## Threat model and transcript

The primary adversary is an honest-but-curious coordinating server that obeys
the protocol but records its complete view. In the primary, stronger visibility
model, the server observes every client message in every round, public control
flow, stopping metadata, final released state, and prediction interface.

Ideal secure aggregation is a separately reported secondary model in which the
server sees only the prescribed aggregate. It may tighten sensitivity or enable
central noise, but it is an explicit trusted functionality and is not itself a
DP guarantee. Client collusion is outside the primary theorem unless a later
mechanism states a threshold and includes colluders' views.

## Frozen output contract: inference-closed release

The main mechanism outputs a randomized release `R`, which may contain model
parameters, cached structural summaries, or both. The complete server-visible
training transcript together with `R` must satisfy `(epsilon,delta)` edge-DP
under `D~eD'`.

The deployed score has the form

`score_R(u,v) = F(R, X, u, v; public randomness)`.

It may not read `E`, a raw neighborhood, an unprotected edge-derived embedding,
or any other private state. Consequently, any finite or unlimited collection of
scores computed only this way is post-processing of `R`. Public release of raw
embeddings is permitted only when those embeddings are themselves contained in
or deterministically computed from `R` and public inputs.

A separately budgeted interactive score service is an optional future
extension, not part of the minimum contribution. Rate limits and logging alone
do not constitute DP.

## Privacy statement required of every mechanism

For both server-visibility models, a valid claim must state:

1. adjacency and protected edge owner;
2. every randomized message and released object;
3. clipping/sensitivity unit and sampling law;
4. per-step privacy mechanism;
5. adaptive composition over local steps and rounds;
6. conversion to `(epsilon,delta)` at a declared `delta` and optimized RDP
   order; and
7. why deployed inference is post-processing.

Privacy parameters may not be inferred from a nominal noise multiplier alone.

## Utility estimand and evaluation discipline

The primary estimand is the paired improvement attributable to private
structure over the strongest matched public-input-only predictor. Global,
intra-client, and cross-client ranking metrics must be reported separately.

The minimum causal controls are public-input-only, zero-private-signal or
noise-only, a tuned non-private oracle, and a matched non-private federated
method. Splits, candidate sets, client assignment, tuning budget, and seeds must
be shared. Test edges are sealed until the mechanism and hyperparameters are
frozen. A composite score is secondary and must expose fixed weights.

## P1 feasibility gate

Before real-data experiments, P1 must derive and test on synthetic graphs a
condition of the form

`private structural signal > release noise + approximation error + public gap`.

The derivation must expose release dimension, edge sensitivity, clipping unit,
client count, visibility model, compositions, degree/workload bounds, and any
query budget. P1 stops if no nontrivial regime is predicted or if a clean oracle
cannot beat the public-only control.

## Non-goals

- Node-attribute or node-level privacy.
- Knowledge-graph triple privacy presented as ordinary edge privacy.
- Cryptographic confidentiality presented as DP.
- Inference that rereads the private graph.
- Universal superiority of a named architecture or loss.
- A "first" claim based only on combining keywords.
