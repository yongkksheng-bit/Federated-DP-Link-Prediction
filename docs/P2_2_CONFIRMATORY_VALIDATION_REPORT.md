# P2.2 Confirmatory Operational Validation

Status: **READY FOR ONE-TIME TEST RUNNER FREEZE.**

The fixed validation runner was committed as `ec9f4fa` before execution. All
ten records use that commit, the fixed `conditioned_b8_lambda_0.1` candidate,
release dimension 1,088, edge sensitivity one, and individually visible client
messages. All records report `test_accessed=false`.

Validation has an operational role only and did not select or alter the
candidate. Its paired diagnostics over public cosine were:

| Domain | Global AUC gain (95% CI) | Cross AUC gain (95% CI) |
|---|---:|---:|
| GitHub Social | +0.05037 [+0.04964, +0.05110] | +0.05021 [+0.04941, +0.05101] |
| Deezer Europe | +0.03499 [+0.03240, +0.03758] | +0.03508 [+0.03165, +0.03852] |

These values establish that the parser, public coarsening, capacity estimate,
DP mechanism, baselines, and metrics execute coherently on both untouched
source schemas. They are not the confirmatory decision. The preregistered
one-time encrypted test still requires every dataset-metric cell to have mean
gain at least `+0.02`, paired interval lower bound above zero, and superiority
to random and matched zero-private-signal controls.
