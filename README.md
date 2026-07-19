# Federated-DP-Link-Prediction

Clean-room research repository for the paper:

> **Differentially Private Link Prediction in Federated Setting**

## Status

Phase 2: source and pilot protocol. Phase 1 closed on 2026-07-19 with a
provisional public-coarsened affinity-release family and explicit synthetic
failure boundaries. No final method, real dataset, real result, or manuscript
claim has been admitted yet.

## Clean-Room Boundary

This repository began from an empty working tree and a new Git history on
2026-07-18. Previous implementations, configurations, data, splits, results,
and manuscript prose are inadmissible. They must not be copied, imported, or
cited as evidence for this project.

Every future empirical artifact must be generated inside this repository after
its protocol is committed. Every privacy claim must be bound to executable
sensitivity and accounting checks.

## Current Priorities

1. Freeze dataset provenance and public/private field classifications.
2. Freeze client ownership, candidates, splits, and sealed-test controls.
3. Preregister an untouched pilot for the provisional mechanism family.
4. Re-audit matched baselines and privacy accountants before execution.
5. Preserve development, validation, and one-time sealed-test boundaries.

See `docs/RESEARCH_CHARTER.md` and `docs/EVIDENCE_POLICY.md`.

The P0 decision and residual obligations are recorded in
`docs/P0_CLOSEOUT.md`; full-text evidence and citation chains remain in
`docs/P0_FULLTEXT_AND_CITATION_AUDIT.md`.
