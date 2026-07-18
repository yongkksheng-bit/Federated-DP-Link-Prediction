# Federated-DP-Link-Prediction

Clean-room research repository for the paper:

> **Differentially Private Link Prediction in Federated Setting**

## Status

Phase 1: synthetic mechanism feasibility. Phase 0 closed on 2026-07-18 with a
narrowed ordinary-graph, cross-client, inference-closed edge-DP output
contract. No method, real dataset, result, or manuscript claim has been
admitted yet.

## Clean-Room Boundary

This repository began from an empty working tree and a new Git history on
2026-07-18. Previous implementations, configurations, data, splits, results,
and manuscript prose are inadmissible. They must not be copied, imported, or
cited as evidence for this project.

Every future empirical artifact must be generated inside this repository after
its protocol is committed. Every privacy claim must be bound to executable
sensitivity and accounting checks.

## Current Priorities

1. Derive a privacy-utility feasibility condition before selecting an
   architecture.
2. Implement accountant and neighboring-dataset unit tests.
3. Validate candidate releases on synthetic graphs only.
4. Stop if no mechanism clears the public-only and clean-oracle gates.
5. Preserve development, validation, and one-time sealed-test boundaries.

See `docs/RESEARCH_CHARTER.md` and `docs/EVIDENCE_POLICY.md`.

The P0 decision and residual obligations are recorded in
`docs/P0_CLOSEOUT.md`; full-text evidence and citation chains remain in
`docs/P0_FULLTEXT_AND_CITATION_AUDIT.md`.
