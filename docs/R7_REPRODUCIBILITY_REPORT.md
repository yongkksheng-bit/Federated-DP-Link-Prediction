# R7 Clean-Checkout Reproducibility Report

Audit date: 2026-07-24 (Asia/Shanghai).

## Verdict

`PASS`

## Independent checkout

- Remote: `git@github.com:yongkksheng-bit/Federated-DP-Link-Prediction.git`
- Audited commit: `fbe71506e29884c73c894b14ca14fef67ef3d785`
- Checkout directory:
  `D:\DPLPIFS_POLY\Federated-DP-Link-Prediction-R7-audited-fbe7150`
- Interpreter and package versions are recorded in
  the archived `results/r7_independent_audit/reproduction.json` snapshot.
  New runs write to `tmp/r7_independent_audit/reproduction.json` so the
  tracked checkout remains unchanged.

The checkout was cloned from GitHub. No active-worktree files were copied into
it. The sealed P3/R5 holdout was not decrypted, regenerated, or queried.

## Reproduced artifacts

1. Full test suite: 101/101 passed.
2. Independent theorem/accountant audit: passed.
3. Three publication figures: rebuilt byte-for-byte with no tracked changes.
4. IEEE manuscript: compiled successfully to nine pages.
5. Built manuscript PDF:
   SHA-256 `93235995768b4f1507a012f73418007c39477399419db04999fd46553ae2b237`.

The final Git tracked-change set after reproduction was empty. Untracked
derived outputs were the compiled manuscript and the reproduction report.
The clean-built manuscript is byte-identical to
`output/pdf/certfed_lp_r7_audited.pdf`.

## Artifact correction

The original `records.jsonl` contains 585 non-standard JSON `Infinity` tokens
for invalid certificate lower bounds. R5 preserved that immutable raw file and
created a non-destructive strict export replacing only those invalid bounds
with JSON `null`. R7 now tracks `records_strict.jsonl`; its serialization audit
preserves record count and raw-file hash.

## Determinism correction

The first clean build found that Matplotlib inserted current timestamps into
the vector PDFs. PNG content was already byte-identical. R7 disabled PDF
creation/modification timestamps and added a hard gate: any tracked artifact
change after clean reproduction fails the run.

R7 also suppresses pdfTeX build dates, trailer IDs, and engine metadata. Two
forced local rebuilds and the final clean clone produced the same manuscript
hash shown above.
