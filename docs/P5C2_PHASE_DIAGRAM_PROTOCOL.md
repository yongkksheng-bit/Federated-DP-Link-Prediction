# P5C2 Two-Axis Privacy-Utility Phase Diagram

Frozen before proxy computation on 2026-07-22 (Asia/Shanghai).

## Motivation and boundary

P5FC rejected a universal monotone energy frontier. C2 tests a narrower
hypothesis: release recoverability and structural usefulness are distinct.
Energy `F_signal` describes whether a private structural channel rises above
Gaussian noise; a training-only cross-fitted alignment axis describes whether
the recovered clean channel improves link ranking over public descriptors.

This is retrospective development, not confirmatory evidence. It may read the
six P3 development arrays and P5F validation records. It may not read P3
encrypted tests or any P5FC Flickr/Reddit test record, cell, or summary. P5FC
is motivation only and is not an optimization target.

## Cross-fitted alignment axis

For each P3 dataset and seed, deterministic keyed ranks reserve 10% of training
positives, capped at 20,000 and balanced between intra- and cross-client edges.
The structural channel is rebuilt from the remaining training positives. Probe
negatives are a matched, deterministic subset of the already frozen P3
training negatives. Thus neither validation nor test links enter the proxy.

Let `s0` be public-feature cosine and `s1` be cosine after one clean
row-normalized sum-aggregation hop. The primary alignment coordinate is

`A_cv = AUC((s0+s1)/2) - AUC(s0)`.

Secondary diagnostics are recorded but cannot replace `A_cv` after results are
seen. The proxy is an internal research diagnostic derived from private
training edges; releasing it in deployment would require a separate privacy
mechanism.

## Phase model and gate

Each of the 60 P5F dataset/epsilon/visibility cells is represented by
`r=F/(1+F)` and the seed-mean `A_cv`. A closed-form ridge model with fixed
penalty `1e-3` predicts cell-mean Global-AUC gain. The one-axis comparator uses
`[1,r,r^2]`; C2 adds `[A_cv,r*A_cv]`. Standardization is learned within each
leave-one-dataset-out training fold.

C2 advances only if it reduces pooled LODO MAE by at least 15%, achieves at
least 0.8 sign accuracy and 0.6 Spearman prediction correlation, improves MAE
on at least four of six held-out datasets, and worsens no dataset by more than
0.02 AUC. Missing/nonfinite cells or any prohibited test access reject C2.

Passing would authorize a new-source protocol only. It would not validate the
phase diagram, make the proxy deployable, or erase the P5FC negative result.
