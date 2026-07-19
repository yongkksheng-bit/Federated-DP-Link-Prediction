# P2 Confirmatory Pilot Protocol

Frozen before source acquisition: 2026-07-19 (Asia/Shanghai).

## Question

Does a sensitivity-one, public-coarsened edge-affinity release retain private
link signal beyond fixed public descriptors under the primary server-visible
edge-DP model on both a blog and a social graph?

This pilot validates a mechanism family, not a final model name or a superiority
claim over neural link predictors.

## Mechanisms and controls

The primary candidate releases one Gaussian-perturbed 136-dimensional vector
per client, with unique edge ownership. Because one edge affects one client and
one coordinate, each visible message has L2 sensitivity one; client mechanisms
compose in parallel over disjoint edge records. The server sums the visible
messages. Ideal secure aggregation is secondary and receives one centrally
noised aggregate with the same global sensitivity.

Controls are:

1. random scores;
2. the strongest preregistered fixed similarity computed from public node
   descriptors only;
3. a zero-private-signal release with matched Gaussian noise;
4. the same coarsened affinity statistic without noise, reported only as an
   unattainable utility ceiling; and
5. the matched DP hard coarsened release.

No control may receive test labels, test edges, a different split, a different
candidate set, or a larger tuning budget.

## Privacy configuration

The pilot fixes add/remove-edge adjacency, `(epsilon, delta)=(4, 10^-6)`, one
Gaussian release, and the complete RDP order grid implemented in
`fed_dp_lp.accounting`. Result records must include the full RDP curve, selected
order, calibrated standard deviation, release dimension, client count, message
visibility, per-client edge counts, client node counts, source hashes, split
commitments, code commit, and config hash. A nominal noise multiplier is not a
privacy result.

## Endpoints and paired analysis

Primary metrics are Global AUC and Cross-client AUC. Intra-client AUC is
reported but does not determine the gate. Five frozen seeds are paired across
all methods. For each dataset and primary metric, report the mean paired gain
and a two-sided 95% Student-t confidence interval over the five paired seeds.

## Go/No-Go gate

The primary visible-message DP release advances only if, on both datasets and
for both Global and Cross-client AUC:

- its mean gain over the strongest fixed public-only score is at least 0.02;
- the lower endpoint of the paired 95% CI for that gain is above zero; and
- it exceeds random and the matched zero-private-signal control.

The formal epsilon must be reproduced by the executable RDP accountant and all
required provenance fields must be present. Missing cells, source-count
mismatches, test access before freeze, or post-test tuning force NO-GO.

Passing authorizes a broader P3 benchmark. It does not authorize a first claim,
public-data redistribution, or publication of an unverified privacy theorem.
