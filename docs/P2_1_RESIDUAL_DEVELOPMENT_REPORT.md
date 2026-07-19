# P2.1 Residual Development Report

Decision: **ADVANCE to a new untouched confirmatory protocol.**

The candidate grid and maximin selection rule were frozen at `64056e2` before
execution. Ten records use only the previously opened P2 validation split; no
encrypted P2 test was accessed.

## Selected fixed candidate

`public cosine + 0.05 * centered rank(DP block density)`

| Development domain | Metric | Mean gain over public cosine | Paired 95% CI |
|---|---|---:|---:|
| BlogCatalog v3 | Global | +0.04822 | [0.04614, 0.05030] |
| BlogCatalog v3 | Cross | +0.04824 | [0.04675, 0.04972] |
| Facebook MUSAE | Global | +0.00334 | [0.00315, 0.00352] |
| Facebook MUSAE | Cross | +0.00332 | [0.00297, 0.00367] |

All four development cells are positive, both Facebook cells exceed the frozen
+0.002 minimum, and all paired intervals exclude zero. The residual therefore
preserves the strong Facebook public predictor while recovering useful private
structure on BlogCatalog.

## Claim boundary

This is development evidence, not a paper result or confirmatory gate. The
transform and weight are now fixed. They may not be changed after registering
new sources. Existing P2 encrypted tests remain permanently unopened.

P2.1 next requires one new blog domain and one new social domain with immutable
source identities, edge-independent clients, newly sealed splits, and the same
strict five-seed +0.02/paired-CI gate. If a domain's public baseline is already
near its empirical ceiling, both the absolute gain and ceiling-normalized gain
will be reported; the preregistered absolute gate will not be retroactively
weakened.
