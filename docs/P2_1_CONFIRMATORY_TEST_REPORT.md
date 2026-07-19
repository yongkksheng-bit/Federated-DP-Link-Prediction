# P2.1 One-Time Confirmatory Test Report

Decision: **NO-GO under the preregistered cross-domain materiality gate.**

The one-time runner was frozen at `fa523d2`. It wrote its access record before
decrypting, verified all 10 encrypted payload hashes and keyed commitments, and
completed exactly once. A second execution is forbidden.

## Primary visible-message result

| Dataset | Metric | Candidate AUC | Gain over public cosine (95% CI) | +0.02 gate |
|---|---|---:|---:|---|
| PolBlogs | Global | 0.7413 | +0.03447 [0.03017, 0.03878] | pass |
| PolBlogs | Cross | 0.7401 | +0.03369 [0.03021, 0.03716] | pass |
| LastFM-Asia | Global | 0.8453 | +0.00407 [0.00302, 0.00511] | fail |
| LastFM-Asia | Cross | 0.8458 | +0.00439 [0.00332, 0.00545] | fail |

All four cells have positive paired intervals. The candidate also beats random
and matched zero-private-signal controls with intervals above zero. PolBlogs
passes every gate. LastFM demonstrates reproducible private structural value,
but its approximately +0.004 gain is below the frozen +0.02 minimum. Since all
four cells were required, the protocol decision is NO-GO.

## Interpretation

The result rejects a strong claim that this simple 136-dimensional residual
produces a practically large cross-domain improvement. It does not show that
the residual is noise or that inference-closed edge-DP link prediction is
impossible: LastFM's effect is small but paired, positive, and larger than the
matched zero-private-signal perturbation.

The correct diagnosis is representational. A single block-rank residual adds
substantial value when public labels leave unresolved blog structure, but adds
only a small correction when high-dimensional public music preferences already
rank social links well.

## Consequence

- Do not weaken the +0.02 gate, rerun the test, change seeds, or reclassify this
  protocol as GO.
- Preserve this result as confirmatory negative evidence.
- A P2.2 method must condition private residuals on public-score regions rather
  than use one residual per coarse block, or use a low-rank DP residual release
  that retains more within-block variation.
- P2.2 may use prior development/validation sources for design, but any new
  confirmatory claim requires newly registered untouched sources and splits.
