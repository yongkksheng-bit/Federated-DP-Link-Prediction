# P0 Novelty Audit

## Decision

**Proceed with narrowing. Do not design a model yet.**

The broad intersection `federated + differential privacy + link prediction` is
not novel: CIKM 2021 FKGE already combines all three for knowledge graphs, and
2025--2026 work combines federated graph learning with local, metric, or
training-time DP. The defensible opportunity lies in a stricter operational
intersection.

## Potentially admissible novelty

A future paper may claim novelty only if it actually delivers and verifies:

1. ordinary-graph link prediction under distributed edge ownership rather than
   cross-domain KG embedding;
2. worst-case add/remove edge-DP rather than metric-DP, informal privacy, or
   record-DP for embeddings;
3. explicit accounting of the complete federated transcript;
4. cross-client prediction without raw-edge or raw-neighborhood exchange;
5. inference closure through a DP release or separately private bounded score
   service; and
6. a privacy-utility result that predicts and empirically clears a public-only
   baseline under matched controls.

No individual item is sufficient. The contribution must be their technically
nontrivial combination, supported by a theorem and an implementation audit.

## High-risk claims

These claims require further evidence and should not appear in an abstract
during P0:

- "the first federated edge-private link-prediction framework";
- "the first differentially private federated graph learner";
- "the first private federated link-prediction method";
- "secure aggregation guarantees differential privacy";
- "federated learning prevents data leakage";
- "the final encoder implies private embeddings and scores";
- "a lower-dimensional release necessarily improves AUC";
- "a contrastive objective is inherently more DP-robust than BCE".

## Prohibited novelty claims

The literature already rules out claiming novelty for:

- DP link prediction in general;
- federated link prediction in general;
- federated DP knowledge-graph link prediction;
- edge-private aggregation perturbation;
- private subgraph GNN extraction;
- cross-client representation exchange;
- local-noise federated GNN training; or
- privacy-preserving graph learning based solely on not sharing raw data.

## Candidate contribution shapes

### Shape A: mechanism plus inference closure

A low-dimensional edge-DP structural release designed specifically for
federated LP, with a scorer that never rereads private edges. This is viable
only if P1 proves a useful signal-to-noise regime and a clean oracle beats the
public-only baseline.

### Shape B: bounded private score service

A federated query mechanism for candidate links with workload-level
sensitivity, query accounting, and cross-client support. This must be more than
rate limiting: the score transcript itself needs a formal guarantee.

### Shape C: privacy-utility frontier

A lower/upper-bound and benchmark paper showing when edge-DP federated LP can
or cannot improve over public inputs, accompanied by a mechanism matching the
achievable regime. This is the safest fallback if no universal model wins.

## P0 gate into P1

P1 may begin only with the following constraints:

- start from the output contract, not a preferred neural architecture;
- derive sensitivity before implementation;
- compare central visibility and ideal secure aggregation separately;
- establish an information-bearing non-private statistic before adding noise;
- prohibit all real-data access until the feasibility theorem and synthetic
  mechanism tests are committed.

