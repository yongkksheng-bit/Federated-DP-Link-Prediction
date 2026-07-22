# P6B Conservative Feasibility Selector Report

## Decision

`REJECT_CONSERVATIVE_SELECTOR`

The frozen selector fails five of the seven substantive gate checks. It may not
advance to fresh-source protocol design, and its features, ridge penalty,
safety margin, or thresholds may not be retuned on the same P5F outcomes.

The independent audit reproduced all 60 cells, input hashes, features,
outcomes, nested-LODO predictions, actions, policy metrics, gate checks, and
the final decision. No P3 test, P5FC confirmatory record, or fresh source was
accessed.

## Gate results

| Criterion | Registered requirement | Observed | Pass |
|---|---:|---:|---|
| Activation fraction | at least 0.15 | 0.167 (10/60) | yes |
| Activated held datasets | at least 3 | 1 | no |
| Negative-mean-gain activations | 0 | 2 | no |
| Material precision | at least 0.80 | 0.50 | no |
| Positive-oracle gain capture | at least 0.40 | 0.070 | no |
| Worst dataset policy gain | at least 0 | 0.000 | yes |
| Macro domain gain 95% CI lower | above 0 | -0.0116 | no |

The policy's macro dataset gain is 0.0074 AUC with a 95% t interval of
[-0.0116, 0.0263]. The always-DP diagnostic mean is 0.0911 and the
positive-mean-gain oracle is 0.1056, but neither comparator satisfies the
selector's prospective no-harm requirement.

## Actions

The selector abstains on BlogCatalog, Facebook, PolBlogs, LastFM, and GitHub.
It activates all ten Deezer cells. Deezer's average policy gain is 0.0443, but
the two lowest-privacy cells include gains of -0.011 and approximately zero;
only five of ten activations reach the registered +0.02 materiality level.

## Failure analysis

The dominant failure is unsupported covariate extrapolation. Deezer's public
feature coverage is 0.782, so its missing-feature fraction is 0.218. In the
outer Deezer fold, the largest missing-feature fraction among the five training
domains is approximately 0.023. The standardized linear ridge model therefore
extrapolates far outside its training support and predicts gains of roughly
0.61--0.75. The nested historical maximum-overprediction margin is only about
0.10 and cannot protect against this domain shift.

This diagnosis is post-result. Adding an out-of-distribution support guard now
and rerunning P6B would be an adaptive repair and is prohibited. More broadly,
the result shows that a residual-based safety margin controls observed-domain
optimism but does not guarantee safe transfer to a graph whose covariates lie
outside the training envelope.

## Scientific consequence

P6B does not support a learned cross-domain switch for the frozen GAP-style
channel. The no-harm objective remains scientifically meaningful, but six
heterogeneous development domains are insufficient to estimate a transferable
decision boundary with the present specification.

Any later selector must treat covariate support as part of its design before
outcomes are observed. A defensible future protocol could require automatic
public-only abstention outside a training-domain support envelope, but that
hypothesis needs genuinely new evidence; it cannot be validated by repairing
and replaying these 60 cells.

P3 tests and future candidate sources remain closed.
