# R2A Private-Certificate Synthetic Protocol

## Purpose

R2A asks whether the R1 one-sided certificate is both safe and statistically
nontrivial at practical privacy budgets. It tests only bounded synthetic utility
records. It does not execute a graph learner and cannot establish link-
prediction utility.

## Synthetic record law

Each certification contribution is in `{-1,+1}`. For registered mean `mu`,
an independent block sign equals `+1` with probability `(1+mu)/2`. The sign is
replicated `chi` times, giving public dependence factor `chi`. Counts are
divisible by every registered `chi`.

This construction is deliberately high variance. `chi=1` is conditionally
independent; `chi=5` tests whether the registered dependence penalty prevents
overconfident activation.

## Privacy and visibility

The query is the utility sum and private count, with L2 sensitivity `sqrt(2)`.
For each target certification epsilon and `delta=1e-6`, absolute Gaussian noise
is calibrated from the complete one-release RDP curve.

Under ideal secure aggregation, one noise vector is added. Under visible
messages, every client uses the same locally private release and the decision
sees the sum of `K` independent noises. Privacy does not multiply by `K`, but
the aggregate noise variance does.

R2A does not combine this budget with training because no trainer is executed.

## Certificate

Failure probability `0.05` is frozen as:

- `0.01` for sum noise;
- `0.01` for count noise; and
- `0.03` for bounded-record sampling.

The material threshold is `gamma=0.02`. A trial activates only when the R1
population lower certificate reaches `gamma` and the noisy count lower bound
is at least 50.

## Grid

The complete grid contains:

- six true means from `-0.10` to `0.20`;
- counts 500, 2,000, and 10,000;
- epsilon 0.5, 1, 2, 4, and 8;
- 1, 5, and 20 clients;
- visible and ideal visibility; and
- dependence factors 1 and 5.

Each cell receives 5,000 deterministic Monte Carlo trials.

## Gate

Safety is primary. Across every cell with `mu<gamma`:

1. the maximum rate at which the lower certificate exceeds the true mean must
   be at most 0.05;
2. the maximum false-activation rate must be at most 0.05; and
3. each rate's one-sided 95% binomial upper bound must be at most 0.06.

Nontriviality prevents an always-abstain pass:

- for `mu>=0.10`, `n=10,000`, epsilon at least 2, and `chi=1`, ideal power must
  be at least 0.80;
- visible-message power must be at least 0.70 for at most five clients; and
- at least 20% of all positive-mean cells must activate.

The accountant must reproduce every stored epsilon within `1e-10`. Any failure
stops CertFed-LP before graph experiments.

## Evidence boundary

R2A reads no graph, P3 artifact, P5F/P6 outcome, sealed test, restricted paper,
or future source. Passing authorizes only R2B end-to-end synthetic protocol
design.
