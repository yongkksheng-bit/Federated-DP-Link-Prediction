# P0 Problem Definition Draft

This document defines the narrow target discovered by the literature audit. It
is a draft for formal review, not a frozen mechanism protocol.

## Graph and federation

Let `V` be a fixed public node universe with public node descriptors `X`. A
simple undirected graph has private edge set

`E = union(E_1, ..., E_K)`,

where client `k` owns `E_k`. Edge ownership must be unique and independent of
the presence or absence of any other private edge. Node membership, client
membership, and public descriptors are fixed under edge adjacency.

The target task scores candidate pairs in `V x V`, with separate reporting for
intra-client and cross-client pairs. A cross-client pair is a prediction target,
not permission to reveal either client's raw neighborhood.

## Neighboring federated datasets

Two federated datasets are add/remove edge neighbors when they differ by one
canonical edge record in exactly one client's edge set, while `V`, `X`, client
membership, public randomness, and every other record remain fixed.

Any negative sampler, partitioner, scheduler, normalization, or denominator
whose output changes for additional records after one edge is removed must be
included in the sensitivity analysis. Calling an edge a record is insufficient
if preprocessing creates graph-wide dependencies.

## Adversary draft

The minimum adversary is an honest-but-curious coordinating server that sees
the complete protocol-defined transcript and final released object. The final
paper must separately state guarantees under:

- no secure aggregation, where each client message is server-visible;
- ideal secure aggregation, where only an aggregate is server-visible; and
- optional client collusion assumptions.

Secure aggregation is a trusted protocol assumption, not a DP mechanism.

## Output contract

The formal mechanism output must include every object visible outside a client:

- messages observed in every training round;
- public metadata derived from private edges;
- final parameters, cached representations, or released statistics; and
- the deployed prediction interface.

Raw embeddings computed from `E`, unrestricted pair-score dumps, and inference
that rereads `E` are not covered by training DP through post-processing. The
preferred deployment target is either:

1. a scorer that consumes only public inputs and a DP release; or
2. a bounded score service whose query mechanism has an independently composed
   privacy budget.

The choice remains unresolved until the feasibility analysis.

## Utility target

The primary scientific question is not whether a private method attains high
absolute AUC. It is whether private structural information creates measurable
utility beyond the strongest matched public-input-only predictor.

Required metric families are global, intra-client, and cross-client ranking
quality. A composite metric may be reported only alongside its fixed weights
and all components; it cannot hide a failed cross-client result.

## Feasibility question

Before architecture design, P1 must derive a condition of the form

`private structural signal > release noise + approximation error + public-baseline gap`.

The derivation must expose dependence on release dimension, clipping unit,
client count, secure-aggregation visibility, number of compositions, graph
degree or workload bounds, and query budget. A method is admissible only if a
non-private oracle and the derived DP scale predict a nontrivial feasible
region.

## Explicit non-goals

- Protecting private node attributes under node-level DP.
- Claiming cryptographic security from simulation-only secure aggregation.
- Treating knowledge-graph triple completion as identical to ordinary graph LP.
- Releasing arbitrary embeddings under a training-only guarantee.
- Proving that a named loss is universally superior under DP.
