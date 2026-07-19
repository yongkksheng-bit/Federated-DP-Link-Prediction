# P3.1 Internal Matched Validation Report

Status: **PASS TO EXTERNAL BASELINE AUDIT.**

The protocol and runner were frozen at `61ddb4b` before execution. The run
produced all 150 expected validation records: six datasets, five seeds, and
five epsilon targets. An independently committed audit verifies the complete
record grid, hashes, exact sensitivity, RDP calibration, dimensions, payload
bytes, finite metrics, and untouched test state with zero failures. P3 test
access remains zero.

## Primary epsilon=4 diagnostic

| Dataset | Eight-bin Global AUC | Gain over public cosine (95% CI) | Gain over matched zero signal (95% CI) |
|---|---:|---:|---:|
| BlogCatalog-v3 | 0.5991 | +0.0483 [+0.0468, +0.0498] | +0.0494 [+0.0440, +0.0549] |
| Facebook-MUSAE | 0.9378 | +0.0167 [+0.0159, +0.0174] | +0.0156 [+0.0152, +0.0160] |
| PolBlogs | 0.7400 | +0.0362 [+0.0307, +0.0416] | +0.0304 [+0.0194, +0.0415] |
| LastFM-Asia | 0.8461 | +0.0152 [+0.0139, +0.0165] | +0.0145 [+0.0133, +0.0156] |
| GitHub Social | 0.6650 | +0.0541 [+0.0536, +0.0546] | +0.0559 [+0.0504, +0.0614] |
| Deezer Europe | 0.6385 | +0.0343 [+0.0312, +0.0373] | +0.0521 [+0.0428, +0.0614] |

Cross-client gains over public cosine remain positive throughout the epsilon
grid. At epsilon 0.5 they range from +0.0074 (LastFM) to +0.0540 (GitHub); at
epsilon 4 they range from +0.0152 to +0.0540. The calibrated Gaussian standard
deviations are 10.6074, 5.3500, 2.7207, 1.4050, and 0.7416 for epsilon
0.5, 1, 2, 4, and 8.

## What the ablations do and do not show

The eight-bin release is consistently separated from public-only and matched
zero-private-signal controls, demonstrating that the utility is carried by the
private DP count statistic rather than public descriptors or noise alone.

Eight bins do **not** uniformly dominate four bins. At epsilon 4, eight bins
improve Global AUC over four bins by +0.0034 on LastFM and about +0.0003--0.0005
on Facebook/GitHub, are indistinguishable on BlogCatalog, and are slightly lower
on Deezer/PolBlogs. The selected eight-bin method remains fixed by P2.2
confirmation; four bins must be reported as a strong communication-efficient
variant rather than suppressed. Its logical client payload is 21,760 bytes per
round versus 43,520 bytes for eight bins with five clients and float64 counts.

Visible-message and ideal-SecAgg eight-bin AUCs are nearly identical in all six
domains at epsilon 4 (all paired differences within about 0.0004). Thus secure
aggregation changes the adversary and noise placement but provides little
utility advantage in these high-count cells. Cryptographic SecAgg overhead was
not implemented; reported SecAgg bytes are logical vector lower bounds only.

## Boundary

These are validation diagnostics, not final P3 test evidence. They cannot alter
the selected method. The next stage is accountant and implementation audit for
the mandatory DPLP-family and GAP-style external baseline tracks before any P3
test runner is frozen.
