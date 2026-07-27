# R9 Submission-Preparation Closeout

Closed: 2026-07-27 (Asia/Shanghai).

## Status

`R9_TECHNICAL_SUBMISSION_PACKAGE_COMPLETE`

Decision:
`CONDITIONAL_GO__AUTHOR_AND_EXTERNAL_EXPERT_GATES_OPEN`

## Completed

- Repeated the submission-date novelty search and forward/backward trace.
- Added CE-FedGNN as a close metric-DP representation-exchange neighbor.
- Added the 2026 PoPETs federated-GNN link-inference attack.
- Added primary dataset citations and explicit source/audit provenance.
- Added data, code, and ethics boundaries to the manuscript.
- Added IEEE-compliant disclosure of AI assistance.
- Audited the draft against SPS/TIFS page, abstract, reproducibility, ethics,
  and AI-use requirements.
- Prepared an attributable external-expert sign-off form.
- Added a clean-checkout R9 reproduction gate that requires the rebuilt and
  tracked submission PDFs to be byte-identical.
- A fresh GitHub clone at commit
  `ca84fa8d6892f68aaec39c2b38b2a660ff1a1112` passed the full R9 gate:
  R7/R8 passed, the worktree remained clean, the PDF hashes matched, and the
  sealed holdout was not accessed.
- Compiled a 9-page IEEE manuscript with a 239-word abstract.
- Visually inspected all pages; no clipping, overlap, blank page, sparse
  terminal page, or unreadable table was found.
- Found no undefined references, overfull boxes, or LaTeX warnings.
- Re-ran 106 software tests successfully.
- Did not access, decrypt, regenerate, or query the sealed holdout.

## Frozen artifact

- PDF: `output/pdf/certfed_lp_r9_submission_ready.pdf`
- Clean-clone report: `results/r9_submission/reproduction.json`
- Bytes: `469319`
- SHA-256:
  `b961d2af59d4cd456ccbf9a850754621a42490984ca79d3fe75c7a4de416eed2`

## Open hard gates

The technical package is complete, but final submission is not truthful until
the following human-controlled gates close:

1. an independent privacy/statistics expert completes
   `docs/R9_EXTERNAL_EXPERT_SIGNOFF.md`;
2. all real authors, affiliations, emails, ORCIDs, order, and corresponding
   author replace `Anonymous Authors` and match the Author Portal;
3. every author manually verifies and approves the AI-assisted content and
   disclosure;
4. funding, conflicts, prior-submission/rejection history, and EDICS are
   supplied accurately; and
5. the authors confirm dataset use under applicable source terms.

No automated agent may mark these gates complete without attributable human
evidence.
