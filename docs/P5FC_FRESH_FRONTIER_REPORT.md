# P5FC Fresh-Source Frontier Confirmation Report

## Confirmatory decision

`REJECT_GENERAL_FRONTIER_CLAIM`

The one-time test was accessed once. The experiment may not be rerun, retuned,
or repaired by replacing either source. The independent artifact audit passed
all completeness, hash, RDP, sensitivity, statistic-reproduction, and
single-access checks.

## Registered results

| Dataset | Cells | Spearman rho | Exact two-sided p | Dataset gate |
|---|---:|---:|---:|---|
| Flickr-GraphSAINT | 10 | 1.000 | 5.51e-7 | pass |
| Reddit2-GraphSAINT | 10 | -0.552 | 0.105 | fail |
| Pooled | 20 | 0.758 | not registered | rho only passes |

The pooled statistic cannot rescue the claim because the protocol required
both new datasets to pass. Flickr behaves as a noise-limited graph: increasing
the signal/noise energy ratio raises mean Global-AUC gain from -0.004 to 0.081
under visible messages and from 0.006 to 0.105 under ideal secure aggregation.

Reddit2 is not monotone. Mean Global-AUC gain peaks at 0.176 for visible
messages at epsilon 2 and at 0.174 for ideal secure aggregation at epsilon 1,
then falls as epsilon and the energy ratio increase. At epsilon 8 the gains are
0.134 and 0.106, respectively. These values remain materially positive, but
they contradict the registered monotone-frontier claim.

## Scientific interpretation

`F_signal` measures the magnitude of a released structural channel relative to
Gaussian noise. It does not measure whether that channel is aligned with
held-out link rankings, whether equal-weight channel fusion is calibrated, or
whether low-noise propagation introduces structural bias or oversmoothing.
The fresh result therefore falsifies the proposed interpretation of
`F_signal` as a general one-dimensional privacy-utility frontier.

The Reddit2 shape is consistent with, but does not prove, a two-regime account:
noise removal first reveals useful topology and then exposes bias in the
structural channel, producing an interior utility optimum. This is a post-test
hypothesis and cannot be claimed as confirmed by P5FC.

## Admissible next step

Do not continue the monotone Shape C claim. A scientifically defensible pivot
is an explicitly two-axis phase diagram separating release energy from
structural alignment/bias. Any alignment proxy must be defined without test
links, developed only on synthetic or development data, and frozen before an
entirely new source confirmation. P5FC remains a permanent negative result and
must be reported in the project audit trail.
