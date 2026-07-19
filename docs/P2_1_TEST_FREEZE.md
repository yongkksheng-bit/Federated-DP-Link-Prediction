# P2.1 One-Time Test Freeze

This document and the test runner must be committed before decryption.

The final method is unchanged from development: public cosine plus 0.05 times
the centered rank of the visible-message, sensitivity-one DP block release at
`(epsilon,delta)=(4,10^-6)`. Test uses the five encrypted PolBlogs and five
encrypted LastFM payloads generated before validation.

The runner writes `access.json` with status `started` before decrypting the first
payload. Presence of that file permanently prevents a second execution,
including after a crash. It verifies encrypted-payload SHA-256 and keyed test
commitments before evaluation. Results record the full RDP curve, selected
order, calibrated noise, release dimension, clients, candidate counts, source
and config hashes, and the exact code commit.

For each dataset and Global/Cross AUC, GO requires:

1. mean paired candidate gain over public cosine at least +0.02;
2. paired 95% CI lower endpoint above zero;
3. paired 95% CI lower endpoint above matched zero-private-signal; and
4. paired 95% CI lower endpoint above random scoring.

All four dataset-metric cells must pass. Missing output, failed commitment,
execution failure after access starts, or any failed cell is NO-GO. Diagnostic
ideal-secure-aggregation and nonprivate-residual scores cannot rescue a failed
primary visible-message gate.
