# P0 Literature Search Protocol

## Purpose

Map the research intersection implied by **Differentially Private Link
Prediction in Federated Setting** before selecting a method or dataset. The
audit must distinguish exact predecessors from adjacent work and identify
claims that remain scientifically defensible.

## Search date and sources

- Search opened: 2026-07-18 (Asia/Shanghai).
- Sources: IEEE Xplore, ACM Digital Library, USENIX, OpenReview, PMLR, JMLR,
  proceedings websites, authors' official project pages, and arXiv for papers
  not yet available in archival proceedings.
- Secondary surveys may identify candidates but cannot establish a technical
  claim without checking the primary paper.

## Frozen query families

1. `federated link prediction differential privacy`
2. `federated graph link prediction edge privacy`
3. `edge differential privacy link prediction graph neural network`
4. `differentially private graph learning link prediction`
5. `vertical federated graph link prediction privacy`
6. `distributed graph link prediction secure aggregation differential privacy`
7. `private graph embedding edge differential privacy`
8. `differentially private graph publication link prediction`

Exact-title and backward/forward citation checks follow for every included
candidate.

## Inclusion criteria

A work is included when it contributes to at least one required axis:

- link prediction as an evaluated or formal task;
- federated or distributed ownership of graph information;
- formal edge-level differential privacy;
- private graph representation or score release;
- privacy accounting for graph training;
- attacks or deployment risks relevant to released embeddings or scores.

## Exclusion and classification

Works are not treated as exact predecessors when they provide only:

- node classification without link-prediction analysis;
- federated graph learning without formal differential privacy;
- local or central graph publication unrelated to federated training;
- cryptographic confidentiality without a DP guarantee;
- node-level or client-level DP presented as edge-level DP;
- empirical noise injection without an adjacency definition and accountant.

Such works may remain in the adjacent-work map.

## Extraction fields

For every candidate, record:

- bibliographic identity and authoritative URL;
- task and graph ownership model;
- neighboring-dataset definition;
- adversary and server-visible transcript;
- trusted components and secure-aggregation assumptions;
- exact DP output and any uncovered downstream output;
- mechanism, clipping unit, sampling, and accountant;
- datasets, baselines, metrics, and split protocol;
- whether test edges enter message passing;
- theorem scope and empirical scope;
- overlap with and difference from the fixed problem.

## P0 outputs

1. A literature matrix with exact, near, and adjacent predecessors.
2. A frozen problem definition and output contract.
3. A novelty audit containing admissible, risky, and prohibited claims.
4. A reviewer-objection list.
5. A P0 decision: proceed, narrow, or stop before method design.

No model implementation, dataset download, or experiment is permitted during
P0.
