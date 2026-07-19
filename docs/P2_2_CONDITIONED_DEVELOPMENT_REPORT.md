# P2.2 Conditioned-Release Development Report

Decision: **ADVANCE to registration of entirely new confirmatory sources.**

The mechanism, candidate grid, maximin selection rule, and advance threshold
were frozen in commit `faaf699` before this validation-only run. All 20 records
identify that commit, use five seeds per domain, report edge sensitivity one,
and set `test_accessed=false`. No prior test payload was read or reused.

## Selected candidate

The frozen maximin rule selected:

- eight public cosine bins;
- 1,088 released count coordinates (`136 cell pairs x 8 bins`);
- clipped public-bin-conditioned log enrichment;
- residual weight `lambda=0.1`;
- one `(epsilon,delta)=(4,10^-6)` Gaussian release under individually visible
  client messages.

Every canonical training edge enters one coordinate. The vector has exact
add/remove-edge L2 sensitivity one regardless of its dimension.

## Validation-only paired gains over public cosine

| Domain | Global AUC gain (95% CI) | Cross AUC gain (95% CI) |
|---|---:|---:|
| BlogCatalog-v3 | +0.05047 [+0.04798, +0.05295] | +0.05033 [+0.04831, +0.05236] |
| Facebook-MUSAE | +0.01224 [+0.01177, +0.01272] | +0.01221 [+0.01181, +0.01262] |
| PolBlogs | +0.03502 [+0.02667, +0.04338] | +0.03036 [+0.02087, +0.03986] |
| LastFM-Asia | +0.01863 [+0.01674, +0.02051] | +0.01834 [+0.01723, +0.01945] |

The selected candidate's worst mean gain is `+0.01221`. Both LastFM metrics
exceed the preregistered `+0.01` repair threshold. All eight mean gains and all
eight paired interval lower bounds are positive, although interval positivity
was not required by the development gate.

## Interpretation and boundary

This result supports the diagnosed P2.1 bottleneck: public score conditioning
adds useful within-cell resolution while retaining a sensitivity-one query and
inference closure. It does **not** establish a paper claim. Four domains and
their validation splits have now influenced the method and are development
evidence only. P2.2 can proceed solely by registering source identities,
parsers, splits, seeds, and a one-time gate for entirely untouched domains
before acquiring them. Failure of that future gate rejects this candidate
without retuning on its test data.
