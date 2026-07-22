# P5C2 Two-Axis Privacy-Utility Phase Diagram Report

## Decision

`REJECT_TWO_AXIS_PHASE_PROXY`

The registered two-axis model improves aggregate leave-one-dataset-out
prediction, but it fails the preregistered cross-domain stability gate. It must
not advance to fresh-source confirmation, and the same six development domains
must not be used to search for a replacement proxy.

No P3 test split or P5FC confirmatory record was accessed. The independent
artifact audit reproduced the input hashes, record counts, predictions,
metrics, gate checks, and final decision.

## Registered construction

The proposed phase diagram separates two quantities:

1. privacy-limited recoverability, represented by
   `r = F_signal / (1 + F_signal)`; and
2. a training-only structural-alignment proxy,
   `A_cv = AUC((s_public + s_structural) / 2) - AUC(s_public)`.

`A_cv` is measured on a deterministic internal probe carved from P3 training
edges. Probe positives are removed before fitting the structural channel, and
matched training negatives are used for evaluation. Validation and test edges
do not enter the proxy.

The registered comparison uses leave-one-dataset-out ridge regression. The
one-axis model contains `[1, r, r^2]`; the two-axis model adds
`[A_cv, r * A_cv]`. The outcome is the P5F mean Global-AUC gain over the public
baseline. Hyperparameters and gates were frozen before the proxy records were
generated.

## Results

| Metric | One axis | Two axes | Registered requirement |
|---|---:|---:|---:|
| LODO MAE | 0.0797 | 0.0609 | at least 15% reduction |
| Relative MAE reduction | - | 23.6% | pass |
| Sign accuracy | 0.733 | 0.817 | at least 0.80 |
| Prediction Spearman rho | 0.614 | 0.856 | at least 0.60 |
| Datasets with lower MAE | - | 3 / 6 | at least 4 / 6 |
| Worst dataset MAE degradation | - | 0.0682 | at most 0.02 |

The aggregate criteria pass, but only BlogCatalog, Facebook-MUSAE, and Deezer
obtain lower held-out-dataset MAE. GitHub and PolBlogs degrade modestly, while
LastFM degrades from 0.0202 to 0.0884. The final decision is therefore a strict
NO-GO.

| Held-out dataset | One-axis MAE | Two-axis MAE | Change |
|---|---:|---:|---:|
| BlogCatalog-v3 | 0.1731 | 0.0570 | -0.1161 |
| Facebook-MUSAE | 0.1495 | 0.0744 | -0.0752 |
| Deezer-Europe | 0.0368 | 0.0225 | -0.0143 |
| GitHub-Social | 0.0312 | 0.0410 | +0.0098 |
| PolBlogs-Newman | 0.0675 | 0.0821 | +0.0146 |
| LastFM-Asia | 0.0202 | 0.0884 | +0.0682 |

## Interpretation

The cross-fitted alignment axis contains real information: it materially
reduces aggregate error and improves both sign accuracy and rank correlation.
It is nevertheless not a general phase coordinate. Similar training-only
fusion gains can correspond to different held-out utility responses, and the
LODO failure on LastFM shows that the proxy does not identify structural
transferability across graph domains.

This result narrows the scientific claim. Release-energy magnitude alone is
not a universal privacy-utility frontier, and adding one scalar alignment
estimate does not repair that limitation. A universal two-dimensional phase
diagram is therefore unsupported by the present evidence.

## Consequence

P5C2 is closed as a permanent negative result. The project must not:

- retune the registered proxy or gate on these results;
- promote aggregate improvement while hiding the domain failures;
- access the untouched P3 test payloads for this hypothesis; or
- launch fresh-source confirmation for this rejected proxy.

Any subsequent work must change the scientific target rather than search for
another ad hoc coordinate on the same development evidence. Defensible options
include a domain-conditional result with an independently motivated assumption,
or an impossibility/boundary analysis showing why privacy-energy statistics
cannot determine downstream link-ranking utility without alignment information
that itself generalizes across graph domains.
