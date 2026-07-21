# P5F Frontier Validation Protocol

This retrospective development protocol evaluates the frozen GAP-style
inference-closed release over six P3 validation domains, five seeds, five
privacy budgets, and two server visibility models. It performs no architecture
or hyperparameter search.

The visible-message branch reuses the exact original RNG stream and must
reproduce the prior P3 GAP AUCs to within `1e-12`. The ideal-SecAgg branch keeps
the same sensitivity, RDP calibration, public encoding, split, candidates, and
decoder, but applies one Gaussian perturbation to each aggregate rather than
summing five independently perturbed full client messages.

For every record the runner stores the first-hop signal/noise energy ratio,
the row-degree upper ratio, expected noise energy, a 95% Gaussian norm interval,
complete RDP curve, cache hash, and Global/Intra/Cross AUC gain over public
cosine. The primary diagnostic is Spearman correlation between log frontier
ratio and mean Global AUC gain across dataset/epsilon/visibility cells. The
gate requires correlation at least 0.5 overall and within visible messages,
exact factor-five noise-energy separation, complete finite records, exact
visible reproduction, and zero P3 test access.

This is an explanatory frontier test. Passing does not turn the index into an
AUC theorem and does not authorize opening the encrypted P3 test. It authorizes
fresh-source validation of the frontier law.
