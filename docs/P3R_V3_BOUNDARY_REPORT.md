# P3R-v3 Boundary Development Report

## Decision

`NO_GO_REJECT_JOINT_RELEASE_BOUNDARY_CANDIDATE`

All 750 grid records and 30 leave-one-seed-out held-out records completed. The
audit passed every check, and the encrypted P3 test remained untouched.

| Dataset | Global gain (95% CI) | Cross gain (95% CI) |
|---|---:|---:|
| BlogCatalog-v3 | +0.0010 [-0.0001, +0.0022] | +0.0012 [-0.0004, +0.0028] |
| Facebook-MUSAE | +0.0477 [+0.0462, +0.0492] | +0.0472 [+0.0446, +0.0497] |
| PolBlogs-Newman | -0.0030 [-0.0099, +0.0038] | -0.0048 [-0.0153, +0.0057] |
| LastFM-Asia-SNAP | +0.0100 [+0.0053, +0.0147] | +0.0096 [+0.0037, +0.0155] |
| GitHub-Social-SNAP | +0.0435 [+0.0426, +0.0445] | +0.0435 [+0.0419, +0.0451] |
| Deezer-Europe-SNAP | +0.0096 [+0.0032, +0.0160] | +0.0099 [+0.0037, +0.0160] |

Four datasets now have significantly positive Global and Cross gains, and no
dataset violates the -0.01 mean-drop boundary. Nevertheless, macro Global and
Cross gains are +0.01814 and +0.01776, respectively, below the frozen +0.02
materiality thresholds. The candidate therefore remains a NO-GO.

P3R-v3 exhausts the single permitted boundary-follow-up motivated by P3R-v2.
Further tuning on the same validation benchmark would create increasing
adaptive-overfitting risk. The joint release is retained as an informative
secondary mechanism result, not selected as the paper's primary method, and no
fresh-source confirmation or P3 test access is authorized.
