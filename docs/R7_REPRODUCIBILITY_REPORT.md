# R7 Clean-Checkout Reproducibility Report

Audit date: 2026-07-24 (Asia/Shanghai).

## Verdict

`PASS`

## Independent checkout

- Remote: `git@github.com:yongkksheng-bit/Federated-DP-Link-Prediction.git`
- Audited commit: `bfa114878fd7be385b213c6c8f9b5c575e6014a2`
- Checkout directory:
  `D:\DPLPIFS_POLY\Federated-DP-Link-Prediction-R7-repro-bfa1148`
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
   SHA-256 `e417c9286c68878a537075d186eea13d0c1a8fed565d8cdf04c0b874682e2333`.

The final Git tracked-change set after reproduction was empty. Untracked
derived outputs were the compiled manuscript and the reproduction report.

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
