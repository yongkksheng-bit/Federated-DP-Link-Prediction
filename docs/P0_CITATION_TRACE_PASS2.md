# P0 Citation Trace - Pass 2

Trace date: 2026-07-18 (Asia/Shanghai).

## Purpose

This pass tests the provisional gap against works discovered through forward
citations, same-task recommendation terminology, and 2025--2026 publisher
records. Citation counts are discovery aids only; technical classification
requires primary text.

## Sources and query paths

- Semantic Scholar forward-citation API for DPLP (ICDE 2024).
- Publisher and DOI searches for exact titles and identifiers.
- Author-hosted publication pages and institutional repositories.
- Query families combining `edge differential privacy`, `federated graph`,
  `collaborative filtering`, `recommendation`, `link prediction`,
  `decentralized graph`, and `model deployment`.

## Material findings

### LGA-PGNN promoted to F1

The author-hosted TIFS paper was obtained and inspected. Its formal mechanism
protects selected node-feature dimensions under epsilon-LDP and its task is
node classification. Link stealing is an attack, not the learned task. It does
not establish add/remove-edge DP for a released LP scorer.

### PP-HGRL newly elevated

The 2026 publisher text explicitly formulates decentralized HIN recommendation
as link prediction, claims edge-level DP from graph publishing to model
deployment, and distributes private local subgraphs across clients and a
server. This is the closest discovered work to the target intersection. F1
inspection is mandatory before P0 closure.

### CF-DPGNN newly elevated

The DPLP forward-citation chain exposed CF-DPGNN (ICSIP 2025). Publisher text
confirms graph collaborative filtering, subgraph-sampled DP-SGD, privacy
amplification, and three recommendation datasets. Its ownership, adjacency,
accountant, and released output remain unknown without the full text.

## Pass-2 decision

P0 remains **open**. The ordinary homogeneous-graph, cross-client,
transcript-accounted, inference-closed LP gap is still plausible, but PP-HGRL
may cover a substantial fraction of it and CF-DPGNN may be a mandatory utility
baseline. No model design or real-data experiment is authorized until both
full texts are classified.
