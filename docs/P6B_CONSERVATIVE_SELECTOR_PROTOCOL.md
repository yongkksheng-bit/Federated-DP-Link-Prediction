# P6B Conservative Feasibility Selector Protocol

## Question

Can training/validation-only graph properties safely decide whether to enable
the frozen GAP-style edge-DP structural channel, while falling back to
public-only link scoring when evidence is insufficient?

P6B does not claim to select among arbitrary DP mechanisms. Its action space
contains exactly two choices for each dataset, privacy budget, and visibility
cell: use the frozen P5F GAP-style score, or use its matched public-cosine
baseline.

## Inputs and target

The selector uses the audited P6A domain means and the P5F privacy
recoverability value. Its seven frozen features capture privacy
recoverability, public-baseline headroom, common-neighbor advantage, hub
dominance, missing descriptors, and two recoverability interactions.

The target is the five-seed mean P5F Global-AUC gain over public cosine. All
inputs are development/validation evidence. P3 tests, P5FC confirmatory
records, and unacquired future sources are prohibited.

## Domain-blocked conservative prediction

Evaluation is leave-one-dataset-out (LODO). For each held dataset, a
standardized ridge model is fitted on the other five domains. A safety margin
is then computed without the held domain: each of those five training domains
is nested-held-out in turn, and the maximum positive cell-level overprediction
is retained. The structural channel is activated only when

`predicted gain - safety margin >= 0.02 AUC`.

This construction deliberately favors abstention. The margin protects against
optimistic transfer from the five observed training domains; it is not a
formal distribution-free guarantee for a new graph domain.

## No-harm and nontriviality gate

A selector passes only if all conditions hold across the 60 outer-LODO cells:

1. it activates at least 15% of cells and at least three held datasets;
2. no activated cell has negative observed mean gain;
3. at least 80% of activations realize the registered material gain of 0.02;
4. it captures at least 40% of the positive-mean-gain oracle utility;
5. every dataset's average policy gain is nonnegative; and
6. the lower endpoint of a paired 95% t interval over six dataset-average
   policy gains is above zero.

The activation and dataset-coverage requirements prevent the vacuous
always-public policy from passing. The no-harm conditions prevent aggregate
positive results from hiding a damaged domain.

## Decision

Passing every gate authorizes design of a new fresh-source confirmation
protocol. It does not authorize downloading a candidate dataset or opening any
existing test. Failure permanently rejects this selector specification on the
current evidence; it may not be repaired by retuning its features, ridge, safety
margin, or thresholds on the same outcomes.
