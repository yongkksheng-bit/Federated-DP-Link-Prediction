# P4R RAP Synthetic Feasibility Report

## Frozen decision

`NO_GO_REJECT_RAP`

The audit passed all completeness, privacy, coupling, and no-real-data checks.
The selected configuration was profile energy `gamma=0.2`, profile weight
`1.0`, and prior strength `1.0`.

| Held-out synthetic domain | Global gain over GAP (95% CI) | Cross gain over GAP (95% CI) |
|---|---:|---:|
| Reciprocal social | +0.02333 [+0.01992, +0.02674] | +0.02494 [+0.02145, +0.02844] |
| Reciprocal blog | +0.01827 [+0.01440, +0.02214] | +0.01802 [+0.01358, +0.02246] |

The social domain cleared all gates. The blog confidence intervals exclude
zero, but both mean gains fall below the frozen +0.02 materiality threshold.
RAP-v1 is therefore a final NO-GO and is not reinterpreted.

The selected configuration reached both the maximum profile-energy and maximum
profile-weight boundaries, and selection-set gain increased monotonically over
both axes. Because synthetic graphs can be generated from untouched random
seeds, one boundary follow-up is admissible only if it uses wholly new
selection and held-out seeds. It may not access any real graph. This follow-up
tests release/decoder capacity; it does not relax the +0.02 gate.
