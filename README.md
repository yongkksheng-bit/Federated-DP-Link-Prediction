# Federated-DP-Link-Prediction

Clean-room research repository for the paper:

> **Differentially Private Link Prediction in Federated Setting**

## Status

Phase 0: literature, problem-definition, and novelty audit. The initial audit
decision is **proceed with narrowing**. No method, dataset, result, or
manuscript claim has been admitted yet.

## Clean-Room Boundary

This repository began from an empty working tree and a new Git history on
2026-07-18. Previous implementations, configurations, data, splits, results,
and manuscript prose are inadmissible. They must not be copied, imported, or
cited as evidence for this project.

Every future empirical artifact must be generated inside this repository after
its protocol is committed. Every privacy claim must be bound to executable
sensitivity and accounting checks.

## Initial Priorities

1. Complete a current literature and novelty audit.
2. Freeze the edge-adjacency, federation, adversary, and output definitions.
3. Derive a feasibility condition before selecting a model architecture.
4. Validate mechanisms synthetically before accessing real graph data.
5. Separate development, validation, and one-time sealed-test access.

See `docs/RESEARCH_CHARTER.md` and `docs/EVIDENCE_POLICY.md`.
