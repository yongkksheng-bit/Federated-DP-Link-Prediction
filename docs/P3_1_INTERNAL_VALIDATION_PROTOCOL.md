# P3.1 Internal Matched Validation Protocol

P3.1 is validation-only and cannot alter the selected P2.2 method. It evaluates
the six P3 domains, five frozen seeds, and epsilon in `{0.5,1,2,4,8}` under the
complete fixed-query RDP accountant. The expected output is 150 records. P3
encrypted tests remain untouched.

## Fixed comparison matrix

All private count queries have exact add/remove-edge L2 sensitivity one:

- one public-score bin: 136 coordinates;
- four public-score bins: 544 coordinates;
- selected eight-bin query: 1,088 coordinates.

Every residual uses weight 0.1, smoothing one, and clipped log enrichment. This
isolates score-conditioning resolution rather than retuning each ablation.
Public cosine, random score, and the exact nonprivate eight-bin statistic are
fixed references. The zero-private-signal control uses the same eight-bin
visible-message Gaussian draw as the selected method in each seed/epsilon cell.

The primary visible-message mechanism adds independently calibrated noise to
every visible client vector. The ideal-SecAgg mechanism adds one calibrated
noise vector after aggregation and is a different adversary model, not a
privacy-equivalent implementation shortcut.

## Metrics and systems boundary

Every method reports Global/Intra/Cross ROC-AUC and average precision. Records
also contain the full RDP curve, release dimension, logical float64 client and
server payload bytes, method wall time, process peak working set, client node
counts, and client train-edge counts. Ideal-SecAgg payload figures exclude
cryptographic protocol overhead and are explicitly a logical lower bound.

P3.1 passes operationally only if all 150 records are present, all methods and
metrics are finite, dimensions and sensitivities match the protocol, every
record says `test_accessed=false`, and the P3 split audit remains untouched.
Utility values are diagnostic and cannot be used to modify the primary method.
