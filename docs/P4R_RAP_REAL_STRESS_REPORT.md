# P4R RAP Fixed Real-Graph Stress Report

## Decision

`NO_GO_REJECT_RAP_REAL_STRESS`

The fixed RAP configuration from the fresh-seed synthetic GO was evaluated
without tuning on six legacy P3 validation domains and five paired seeds. All
30 records completed. The audit passed sensitivity, complete RDP, frozen
configuration, public-cache hash, finite-metric, and no-test-access checks.

| Dataset | Global gain over GAP (95% CI) | Cross gain over GAP (95% CI) |
|---|---:|---:|
| BlogCatalog-v3 | -0.0918 [-0.0939, -0.0896] | -0.0918 [-0.0948, -0.0888] |
| Facebook-MUSAE | -0.0723 [-0.0736, -0.0709] | -0.0737 [-0.0758, -0.0716] |
| PolBlogs-Newman | -0.0817 [-0.0918, -0.0716] | -0.0810 [-0.0906, -0.0714] |
| LastFM-Asia-SNAP | -0.1340 [-0.1419, -0.1262] | -0.1338 [-0.1447, -0.1228] |
| GitHub-Social-SNAP | -0.0785 [-0.0830, -0.0741] | -0.0782 [-0.0822, -0.0742] |
| Deezer-Europe-SNAP | -0.0495 [-0.0578, -0.0413] | -0.0483 [-0.0568, -0.0398] |

Macro Global and Cross gains are -0.08464 and -0.08446. Every utility gate
fails. The encrypted P3 test remains untouched.

## Interpretation

The synthetic result was valid for its registered node-specific preference
model but did not transfer to ordinary social/blog graphs. Real node-cell
profiles are sparse relative to visible-message Gaussian noise, while the
synthetic-selected profile energy of 0.5 removes too much energy from the
strong semantic aggregation. This is a model-mismatch result, not a privacy or
implementation failure.

RAP is rejected as a primary method. Retuning its energy or decoder on these
observed validation outcomes is prohibited. Together with the rejected random
topology sketch and the near-but-subthreshold global conditioned histogram,
this result supports moving from repeated universal-method searches to the
pre-registered privacy-utility-frontier contribution shape.
