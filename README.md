# Federated-DP-Link-Prediction

Clean-room research repository for:

> **Differentially Private Link Prediction in Federated Setting**

## Current Result

R7 independently audits the R6 IEEE journal manuscript around
**CertFed-LP**: an architecture-agnostic deployment policy that privately
certifies whether an inference-closed edge-DP structural branch materially
improves over a public-only scorer, and otherwise falls back.

The preregistered R5 primary cell contains six social/blog networks and five
seeds. At composed privacy `(epsilon=5.6640, delta=2e-6)`, CertFed-LP:

- activates 15/30 dataset-seed cells across three datasets;
- observes zero material false activations on the registered finite holdout;
- obtains mean disjoint-Q5 pairwise gain `+0.08543`;
- avoids 10/30 cells in which always enabling private structure is harmful;
- remains `0.00568` mean gain below a non-deployable sign oracle.

The claim is certified finite-holdout fallback under heterogeneous structural
utility. It is not universal superiority of a graph learner and not an AUC
confidence interval.

## Manuscript

- Source: `manuscript/main.tex`
- Compiled draft: `output/pdf/certfed_lp_r6_draft.pdf`
- R7 audited draft: `output/pdf/certfed_lp_r7_audited.pdf`
- Claim contract: `docs/R6_MANUSCRIPT_CONTRACT.md`
- Evidence map: `docs/R6_EVIDENCE_MAP.md`
- Reviewer-risk audit: `docs/R6_REVIEWER_RISK_AUDIT.md`
- R6 closeout: `docs/R6_CLOSEOUT.md`
- R7 theorem audit: `docs/R7_THEOREM_AUDIT.md`
- R7 clean reproduction: `docs/R7_REPRODUCIBILITY_REPORT.md`
- R7 literature refresh: `docs/R7_LITERATURE_REFRESH.md`

Build:

```powershell
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Tests:

```powershell
python -m pytest -q
```

## Reproducibility

The confirmatory protocol was frozen at commit `ef2cd74`; the one-time runner
at `dcdbf2e`; and the immutable result closeout at `e8c5ea7`.

Primary artifacts:

- `configs/r5_graph_phase_confirmatory.json`
- `data/manifests/r5_test_access.json`
- `results/r5_graph_phase_confirmatory/records.jsonl`
- `results/r5_graph_phase_confirmatory/records_strict.jsonl`
- `results/r5_graph_phase_confirmatory/summary.json`
- `results/r5_graph_phase_confirmatory/audit.json`

R7 clean-artifact audit (does not reopen the sealed holdout):

```powershell
python scripts/audit_r7_theory_contract.py
python scripts/reproduce_r7_artifact.py
```

Every privacy-grid cell is an alternative deployment. Releasing the full grid
on one private graph would require additional composition.

## Clean-Room Boundary

This repository began from an empty working tree and new Git history on
2026-07-18. Previous implementations, configurations, results, and manuscript
prose are inadmissible. All empirical evidence in this repository was generated
after its corresponding protocol freeze.
