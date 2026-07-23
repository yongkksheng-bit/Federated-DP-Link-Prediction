# R2B End-to-End Synthetic Report

## Status

**Terminal decision:** `STOP_CERTFED_LP_END_TO_END_SYNTHETIC_NO_GO`

R2B executed the preregistered end-to-end synthetic protocol without accessing
real data or a held-out test set. The implementation passed transcript,
accounting, replay, and numerical audits. It nevertheless failed the
preregistered power and utility gates because the private certificate never
activated.

This result closes the current CertFed-LP route. The gate will not be rescued by
lowering the material-gain threshold, reallocating failure probability, or
retuning on the same synthetic outcomes.

## Frozen protocol

- Protocol: `R2B_CERTFED_LP_END_TO_END_SYNTHETIC_v1`
- Frozen implementation commit: `c94abfed6cd75bbff22ea9ee044e4cfa648d8387`
- Cells: 2,880
- Graph regimes: four
- Seeds per regime: 30
- Training privacy targets: `epsilon in {1, 2, 4, 8}`
- Certification privacy targets: `epsilon in {1, 2, 4}`
- Transcript models: ideal secure aggregation and individually visible client
  messages
- Clients: five
- Nodes per graph: 800
- Edge split: 60% training, 20% certification, 20% evaluation, assigned by a
  deterministic edge hash
- Material-gain threshold: `gamma = 0.02`
- Failure allocation: 0.01 for sum noise, 0.01 for count noise, and 0.03 for
  sampling uncertainty

The certification split and evaluation split were disjoint. Certification
operated on bounded per-edge utility advantages. Evaluation labels were used
only to score the frozen activation policy.

## Gate result

| Metric | Result |
|---|---:|
| Total cells | 2,880 |
| Harmful cells | 1,500 |
| Beneficial cells | 1,356 |
| Activations | 0 |
| Activation fraction | 0.000 |
| Activated regimes | 0 |
| Harmful activation rate | 0.000 |
| One-sided 95% upper bound on harmful activation | 0.001995 |
| Beneficial activation precision | 0.000 |
| Positive oracle-gain capture | 0.000 |
| Macro policy gain | 0.000 |
| 95% CI for macro policy gain | [0.000, 0.000] |
| Worst-regime mean policy gain | 0.000 |
| Maximum transcript aggregation error | 2.274e-13 |
| Maximum accountant epsilon error | 1.750e-13 |

The safety, transcript, accountant, finiteness, and no-real-data gates passed.
The precision, oracle-capture, nontrivial-activation, regime-coverage, and
positive-macro-gain gates failed.

## Why the certificate was vacuous

The end-to-end graph generator produced approximately 1,100--1,300
certification edges per graph. Across all cells, the largest empirical
certification gain was 0.0683. With the preregistered sampling failure
probability, the sampling penalty alone is approximately

`sqrt(2 log(1 / 0.03) / n) = 0.074--0.082`

over this count range. This already exceeds the largest observed empirical
gain, before subtracting the Gaussian sum/count uncertainty and before
requiring the 0.02 material-gain margin.

The best finite private lower bound was -0.0216. Ideal secure aggregation
improved the number of valid bounds relative to visible messages, but its best
bound was still negative:

| Transcript | Valid finite bounds | Best lower bound |
|---|---:|---:|
| Ideal secure aggregation | 563 | -0.0238 |
| Visible client messages | 278 | -0.0216 |

Per-regime diagnostics give the same conclusion:

| Regime | Mean certification edges | Mean certification gain | Maximum certification gain | Best lower bound |
|---|---:|---:|---:|---:|
| Medium public homophilic | 1,105.5 | -0.0057 | 0.0335 | -0.0520 |
| Moderate public heterophilic | 1,292.6 | 0.0186 | 0.0683 | -0.0216 |
| Strong public homophilic | 1,197.0 | -0.0188 | 0.0272 | -0.0477 |
| Weak public homophilic | 1,205.5 | 0.0055 | 0.0490 | -0.0328 |

R2A established that the certificate can have power for sufficiently large
independent samples and sufficiently strong mean utility. R2B shows that those
conditions are not produced by this end-to-end graph protocol. The distinction
is substantive: the theorem is valid, but the resulting certificate is not
practically informative at the registered graph scale and effect sizes.

## Audit

The independent audit exactly replayed all 2,880 records, the summary, the
configuration hash, and the frozen code commit. It also verified:

- no real-data access;
- no held-out test access;
- finite reported metrics;
- exact visible-message aggregation up to floating-point tolerance;
- RDP accountant reproduction within the preregistered tolerance.

Audit status: `PASS`.

## Scientific consequence

The current CertFed-LP mechanism cannot advance to real-data evaluation. It is
safe because it falls back to the public-only predictor, but it has no
registered power to select the private structural channel. Safety without
nontrivial activation does not constitute a publishable utility method.

The next stage must therefore be a decision stage, not another adaptive
candidate search:

1. retain the R1/R2 results as a rigorous feasibility and sample-complexity
   boundary;
2. do not claim an end-to-end CertFed-LP improvement;
3. do not access real data under this route;
4. require a new theorem-level mechanism or a changed trust/privacy assumption
   before registering another method protocol.
