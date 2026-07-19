# P3.2 External Baseline Validation Report

## Audit outcome

Both executable external tracks completed on P3 validation only.

- GAP-style LP adaptation: 180/180 selection-grid records and 150/150
  selected epsilon-curve records; independent audit PASS.
- Closest formal centralized edge-DP pair classifier: 120/120 selection-grid
  records and 150/150 selected epsilon-curve records; independent audit PASS.
- P3 encrypted test access count: zero.

The GAP row is a mechanism adaptation, not an official reproduction. The
central pair classifier is the protocol's closest admissible formal fallback,
not ICDE DPLP, and assumes a trusted curator. A faithful ICDE DPLP reproduction
remains unavailable because no verified official implementation was located
and its path-subgraph sampler/accountant has not been recreated.

## Frozen validation choices

At epsilon 4, the GAP-style adaptation selected `(public dimension, hops)` as
follows: BlogCatalog `(16,2)`, Facebook `(32,1)`, PolBlogs `(8 requested,2)`,
LastFM `(32,1)`, GitHub `(32,1)`, and Deezer `(8,1)`. PolBlogs has one actual
public feature; the requested projection dimension is retained only as the
registered grid label.

The centralized pair classifier selected dimension 8 and learning rate 1.0 on
all datasets except PolBlogs, which selected dimension 4 and learning rate 0.3.

## Primary matched comparison

The table reports five-seed mean Global ROC-AUC with paired 95% t intervals for
the selected P2.2 method minus each external track at epsilon 4. A negative
difference favors the external baseline.

| Dataset | Selected method | GAP-style | Selected - GAP | Central pair DP | Selected - central |
|---|---:|---:|---:|---:|---:|
| BlogCatalog-v3 | 0.5991 | 0.8813 | -0.2823 +/- 0.0033 | 0.5805 | +0.0186 +/- 0.0019 |
| Facebook-MUSAE | 0.9378 | 0.8671 | +0.0707 +/- 0.0012 | 0.8021 | +0.1357 +/- 0.0020 |
| PolBlogs | 0.7400 | 0.8815 | -0.1415 +/- 0.0104 | 0.7129 | +0.0271 +/- 0.0071 |
| LastFM-Asia | 0.8461 | 0.8361 | +0.0099 +/- 0.0043 | 0.7561 | +0.0900 +/- 0.0066 |
| GitHub Social | 0.6650 | 0.8034 | -0.1384 +/- 0.0021 | 0.7233 | -0.0582 +/- 0.0030 |
| Deezer Europe | 0.6385 | 0.6491 | -0.0106 +/- 0.0041 | 0.6548 | -0.0164 +/- 0.0024 |

## Decision

**STOP_BEFORE_TEST_METHOD_DOMINATED.**

The selected conditioned-count release does not survive the mandatory external
baseline audit: the inference-closed GAP-style adaptation is materially better
on three of six domains and also better on Deezer, while the selected method is
clearly better only on Facebook and modestly better on LastFM. Opening the
sealed P3 test cannot repair a validation-level method failure and would waste
the untouched confirmatory evidence.

This result does not invalidate the exact sensitivity-one theorem or the P2.2
confirmatory GO. It invalidates the stronger claim that the selected mechanism
is a competitive Transactions-level primary method across the registered
social/blog benchmark.

## Required next move

Do not tune the selected P2.2 mechanism against these validation results and do
not access P3 test. Close this protocol as a transparent no-go. A successor
method must add an LP-specific, federated contribution that improves upon the
strong cached-aggregation signal without mechanically relabeling GAP. It must
be frozen under a new protocol and evaluated on fresh confirmatory evidence.
