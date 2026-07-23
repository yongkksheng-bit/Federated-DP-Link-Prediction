# R6 Closeout

## Status

`R6_MANUSCRIPT_CONSTRUCTION_COMPLETE`

## Delivered

- IEEEtran manuscript with fixed required title.
- Abstract, introduction, related work, problem/privacy model, CertFed-LP
  method, theorem chain, confirmatory experiments, discussion, conclusion, and
  complete proof appendix.
- Three vector primary figures with PNG previews.
- Dataset, predecessor-contract, and primary policy tables.
- Bibliography grounded in the P0 full-text audit.
- Stable compiled PDF at `output/pdf/certfed_lp_r6_draft.pdf`.
- Reviewer-risk audit and updated repository entry point.

## Critical corrections made during R6

1. Corrected the manuscript RDP conversion to
   `rho(lambda) + log(1/delta)/(lambda-1)`.
2. Restored missing addition operators in the sufficient and necessary
   sample-complexity rates.
3. Separated full-holdout mean (`0.0797162`) from always-structural Q5 mean
   (`0.0794474`).
4. Added selected-policy global ROC-AUC gain (`0.1170942`) only as a secondary
   diagnostic.
5. Removed long monospace paths that damaged appendix justification.
6. Balanced the final bibliography page and visually audited all nine pages.

## Frozen primary facts

- Primary records: 30.
- Diagnostic records: 1500.
- Privacy: `(epsilon=5.6640, delta=2e-6)`.
- Activated: 15/30 across BlogCatalog, GitHub Social, and PolBlogs.
- Material false activations: 0 observed.
- Mean Q5 policy gain: `0.0854325`.
- Always-structural Q5 gain: `0.0794474`.
- Oracle Q5 gain: `0.0911170`.
- Mean oracle regret: `0.0056845`.

## Next phase

R7 is independent reproducibility and external theorem review, not additional
test-set tuning. Any new learner comparison must use a newly frozen protocol
and new admissible evidence; it cannot modify the R5 confirmatory claim.
