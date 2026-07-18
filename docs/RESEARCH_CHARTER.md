# Research Charter

## Fixed problem

The project studies link prediction when graph edges are distributed across
federated clients and the admitted mechanism must satisfy a formally specified
add/remove edge-level differential-privacy guarantee.

The paper title is fixed as **Differentially Private Link Prediction in
Federated Setting**. The method, objective, architecture, datasets, and claimed
contribution are not fixed.

## Scientific objective

Determine when private structural information can improve link prediction
beyond public-input-only inference, and design a mechanism only when a derived
privacy-utility feasibility condition predicts a measurable advantage.

## Required contribution layers

1. A precise adjacency relation, adversary view, federation contract, and
   released-output definition.
2. A mechanism whose implementation matches its sensitivity and privacy
   accountant.
3. A deployment path that distinguishes model release, embedding release, and
   bounded score queries.
4. Matched empirical evidence that isolates objective, federation, privacy,
   and public-input effects.
5. Reproducible source, split, seed, parameter-count, clipping, noise, and
   accounting records.

## Stop rules

- No real-data experiment before a committed source and evaluation protocol.
- No private experiment before a non-private oracle demonstrates capacity.
- No test access before all model and hyperparameter choices are frozen.
- No method may continue after a preregistered dual-domain gate fails.
- No claim may be stronger than the exact metric and output covered by its
  theorem or experiment.

## Prohibited inheritance

No file, code fragment, configuration, dataset copy, split, cache, result,
figure, table, or manuscript paragraph may be imported from any predecessor
workspace or legacy archive. General scientific ideas may be reconsidered only
through independently sourced literature and a new derivation.

