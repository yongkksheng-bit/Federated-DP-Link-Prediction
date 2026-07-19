# P3R Dual-Sketch Development Report

## Completion and audit

The frozen protocol produced 4,860 grid records and 30 leave-one-seed-out
held-out records across six datasets. The independent audit passed every
reproducibility and privacy check: current config hash, complete RDP curve,
exact `sqrt(2)` sensitivity, joint dimension at most 32, finite metrics, and
zero encrypted P3 test access.

## Held-out comparison against GAP-style

The table reports paired five-seed Global and Cross ROC-AUC differences. A
positive value favors the P3R dual-sketch candidate.

| Dataset | Global difference (95% CI) | Cross difference (95% CI) |
|---|---:|---:|
| BlogCatalog-v3 | -0.0168 [-0.0180, -0.0156] | -0.0165 [-0.0175, -0.0156] |
| Facebook-MUSAE | +0.0521 [+0.0500, +0.0541] | +0.0510 [+0.0483, +0.0536] |
| PolBlogs | +0.0085 [+0.0012, +0.0159] | +0.0085 [+0.0000, +0.0170] |
| LastFM-Asia | -0.0312 [-0.0357, -0.0267] | -0.0313 [-0.0375, -0.0250] |
| GitHub Social | -0.0148 [-0.0170, -0.0125] | -0.0149 [-0.0167, -0.0130] |
| Deezer Europe | -0.0519 [-0.0560, -0.0479] | -0.0503 [-0.0543, -0.0464] |

Macro mean differences are -0.0090 Global and -0.0089 Cross. Only Facebook
and PolBlogs have positive paired intervals, fewer than the preregistered
minimum of three. The worst dataset drops also exceed the allowed -0.01
boundary. Every utility gate fails.

## Decision

**NO_GO_REJECT_DUAL_SKETCH_CANDIDATE.**

The privacy lemma and the randomized common-neighbor expectation are valid,
but they do not imply a useful finite-dimensional estimator under the primary
visible-message noise. At a fair maximum joint dimension of 32, the identity
sketch spends private release capacity on a high-variance topological channel
and weakens the semantic aggregation that made GAP-style strong. Increasing
the dimension after observing these results would violate the frozen protocol
and would also worsen communication.

The candidate is rejected without P3 test access. Its positive Facebook result
suggests that pair-conditioned information can complement semantic
aggregation, but random identity probes are not the right carrier.

## Next admissible hypothesis

The next P3R candidate should jointly release the strong semantic aggregation
and the already validated low-dimensional conditioned edge histogram under a
single sensitivity budget. This replaces the high-variance random identity
sketch with 1,088 structured LP sufficient statistics. The joint query must
derive its exact sensitivity as a function of the aggregation and histogram
energy allocation before any run; it must again face GAP-style under nested
held-out selection and the unchanged no-go gates.
