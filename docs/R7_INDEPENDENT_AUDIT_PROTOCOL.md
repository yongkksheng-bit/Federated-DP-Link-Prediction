# R7 Independent Reproducibility and Theorem Audit Protocol

## Freeze point

- R6 evidence/manuscript commit: `9b8dd95`.
- R5 protocol/runner/result commits: `ef2cd74`, `dcdbf2e`, `e8c5ea7`.
- R7 may inspect tracked records and public source files.
- R7 must not decrypt, reopen, regenerate, or tune against any sealed P3/R5
  holdout payload.

## Objectives

1. Reproduce the software tests, R5 accountant audit, R5 summary, R6 figures,
   and IEEE PDF from a clean Git checkout.
2. Independently re-derive the transcript-privacy, finite-population no-harm,
   sufficient-boundary, and necessary-boundary arguments.
3. Audit the exact assumptions behind role-labelled adjacency, inference
   closure, visible messages, secure aggregation, and the edge-keyed
   certification split.
4. Refresh forward/backward literature through the submission date.
5. Amend claims whenever an assumption is computational, conditional, or
   narrower than the R6 prose.

## Independent execution boundary

The clean reproduction checkout must:

- be created from Git commit `9b8dd95`, not copied from the active working
  tree;
- use tracked artifacts only;
- run in a newly created virtual environment or an explicitly recorded
  interpreter environment;
- write all derived output outside the canonical R5 result directory;
- compare hashes or numerical summaries without rewriting immutable R5 raw
  records; and
- record commands, tool versions, return codes, and output hashes.

This is an artifact reproduction, not a second sealed-test execution. A true
raw-data rerun would violate the one-time R5 access contract and requires a new
protocol and new holdout.

## Theorem audit questions

### A. Adjacency and composition

1. Is the protected database the frozen role-labelled edge database, or the
   raw graph before role assignment?
2. Under which definition is sequential training-plus-certification
   composition valid when the historical split is not edge-stable?
3. Are all server-visible messages and post-processed scores included?

### B. Certification sensitivity

1. Can one add/remove certification edge change only one utility contribution
   and one count?
2. Does endpoint corruption avoid graph-dependent rejection?
3. Does inference use only public inputs and released state?

### C. Finite-population randomization

1. Was the hash salt frozen before the sealed holdout was opened?
2. Is the theorem information-theoretic, computational under a PRF/random
   oracle model, or merely conditional on the realized split?
3. Does public knowledge of the salt permit an adaptively chosen target
   population outside the theorem?

### D. Feasibility rates

1. Do sufficient and necessary rates use the same effect gap and adjacency?
2. Is the visible-message `sqrt(K)` term mechanism-specific rather than
   minimax?
3. Are approximate-DP logarithms and constants kept outside headline claims?

## Pass gates

R7 passes only if:

- all tracked tests pass in the clean checkout;
- every stored composed epsilon reproduces from the stored RDP curve;
- reconstructed primary and diagnostic summaries equal the frozen files;
- regenerated figure source data equal the frozen R5 records;
- the manuscript compiles with no undefined references or overfull boxes;
- every theorem assumption is explicit in the theorem statement or immediately
  preceding setup;
- no claim upgrades finite-holdout pairwise utility to ROC-AUC or future links;
  and
- the literature refresh finds no exact predecessor invalidating the stated
  novelty.

## Stop conditions

Stop submission preparation and mark R7 failed if:

1. a sealed test payload must be accessed to reproduce a reported claim;
2. an accountant mismatch exceeds `1e-12`;
3. a graph-dependent corruption changes certification sensitivity;
4. the finite-population theorem requires unreported randomization;
5. an inference path rereads private topology; or
6. a current exact predecessor provides the same task, adjacency, complete
   transcript, inference closure, and private utility gate.

## Deliverables

- `scripts/audit_r7_theory_contract.py`
- `scripts/reproduce_r7_artifact.py`
- `results/r7_independent_audit/`
- `docs/R7_THEOREM_AUDIT.md`
- `docs/R7_LITERATURE_REFRESH.md`
- `docs/R7_REPRODUCIBILITY_REPORT.md`
- revised manuscript and reviewer-risk audit if required
- `docs/R7_CLOSEOUT.md`
