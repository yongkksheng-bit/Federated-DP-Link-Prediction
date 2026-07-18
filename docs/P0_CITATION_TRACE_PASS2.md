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

The complete 2026 paper was subsequently obtained and promoted to F1. It
formulates heterogeneous recommendation as link prediction, but the server
already owns the raw user-item interaction graph. Clients publish perturbed
auxiliary relation graphs once; all HGNN training then occurs centrally. It is
the closest discovered work to the target intersection and rules out broad
novelty based on decentralized edge-DP recommendation, while leaving open
multi-round federated optimization over distributed prediction edges,
cross-client candidates, and a bounded private score transcript.

### CF-DPGNN newly elevated

The DPLP forward-citation chain exposed CF-DPGNN (ICSIP 2025), which was then
obtained and promoted to F1. It is centralized graph collaborative filtering:
overlapping sampled subgraphs are clipped as training examples and Gaussian
noise is added under a claimed multiplicity-aware RDP amplification bound.
There are no clients or federated transcript, but it is a mandatory
centralized edge-DP recommendation baseline whose accountant must be
independently re-derived before comparison.

## Pass-2 decision

The two high-risk papers are now classified. The ordinary homogeneous-graph,
cross-client, transcript-accounted, inference-closed LP gap remains plausible,
but it is narrow and does not justify a "first" claim. P0 remains **open** until
the problem definition is frozen and the two nonstandard privacy accountants
are re-derived; no real-data experiment is authorized before that gate.
