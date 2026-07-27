# R10 Submission-Gate Closeout

Closeout date: 2026-07-28 (Asia/Shanghai).

Decision:

`TECHNICAL_PACKAGE_READY__HUMAN_FACT_GATES_AND_EXTERNAL_SIGNOFF_OPEN`

## Completed in R10

1. Re-derived the privacy, finite-population, and lower-bound arguments from
   the manuscript and executable contracts without relying on the conclusions
   of the earlier theorem reports.
2. Made the conditional-independence requirement for the finite-holdout
   theorem explicit and conditioned the displayed guarantee on the realized
   certification count. This closes an avoidable reviewer ambiguity without
   expanding the claim.
3. Audited all six dataset source/redistribution boundaries. The artifact
   remains source-directed and does not redistribute third-party raw or
   record-level processed data.
4. Prepared fillable author metadata, attestation, disclosure, EDICS, and
   Author Portal checklists under `submission/`.
5. Rebuilt and visually inspected the theorem and appendix pages.

## Verification

- Unit/integration tests: 106 passed.
- R7 theorem-contract audit: PASS.
- R8 red-team audit: PASS.
- Undefined references: none.
- Overfull boxes: none.
- Compiled pages: 10.
- PDF:
  `output/pdf/certfed_lp_r10_submission_gate_ready.pdf`
- PDF SHA-256:
  `b512c2ab2fc70d86a0c5e685cbbebd78f6db5eeee11ebc199735bbd6b7074766`
- Sealed holdout reopened: no.

## Deliberately open human gates

The following cannot be truthfully completed by an automated agent:

1. an independent privacy/statistics expert signs
   `docs/R9_EXTERNAL_EXPERT_SIGNOFF.md`;
2. real author names, order, affiliations, emails, ORCIDs, and corresponding
   author replace `Anonymous Authors`;
3. every author approves the manuscript, artifact, author order, and AI-use
   disclosure;
4. actual funding, conflicts, related/prior submissions, and live-portal EDICS
   are supplied; and
5. the corresponding author signs the dataset-use attestation after checking
   applicable source and institutional requirements.

R10 does not label internal AI-assisted review as external validation and does
not fabricate any author, legal, funding, conflict, or submission-history
fact.
