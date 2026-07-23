# R5 Confirmatory Report

## Decision

`PASS_NONVACUOUS_CERTIFIED_POLICY`

The one-time runner at commit `dcdbf2e` accessed all 30 sealed P3 payloads
exactly once. The independent output audit passed every registered
completeness, provenance, numerical, and privacy-accounting check.

## Primary result

The primary cell was frozen before access:

- training target epsilon: 4;
- certification target epsilon: 4;
- visibility: individually visible client messages;
- composed privacy: approximately `(epsilon=5.6640, delta=2e-6)` after adding
  the two RDP curves and converting once;
- records: six datasets times five seeds, or 30 records.

The certified policy activated 15 of 30 records, covering three datasets. It
made zero material false activations under the finite registered holdout target
and achieved mean disjoint-`Q5` pairwise policy gain `+0.08543`.

| Dataset | Activated | Mean full-holdout advantage | Mean Q5 policy gain | Mean candidate global AUC gain |
|---|---:|---:|---:|---:|
| BlogCatalog-v3 | 5/5 | +0.2621 | +0.2618 | +0.3320 |
| GitHub Social | 5/5 | +0.1260 | +0.1257 | +0.1948 |
| PolBlogs | 5/5 | +0.1254 | +0.1251 | +0.1757 |
| Deezer Europe | 0/5 | +0.0337 | 0.0000 | +0.0429 |
| Facebook MUSAE | 0/5 | -0.0543 | 0.0000 | -0.0517 |
| LastFM Asia | 0/5 | -0.0146 | 0.0000 | +0.0041 |

Deezer illustrates conservative abstention rather than a failure: its finite
holdout advantage was mildly positive, but the mean certificate lower bound
was `-0.0028`, below the registered material threshold `gamma=0.02`.
Facebook and LastFM correctly fell back when the pairwise structural advantage
was negative or negligible.

## Diagnostic phase grid

The full `5 x 5 x 2` training-epsilon, certification-epsilon, and visibility
grid contains 1500 unique records. It is diagnostic and did not enter the
confirmatory decision. No diagnostic cell contained a material false
activation. Increasing training epsilon expanded safe activation coverage.
Ideal secure aggregation generally activated more cells than visible messages,
as predicted by its lower aggregate noise, but it remains a separately labelled
trust model.

## Interpretation

R5 does not show that a private structural graph channel is universally useful.
It shows something narrower and more defensible:

1. utility is heterogeneous across target graphs;
2. a direct target-domain private certificate can identify material gains and
   otherwise fall back to a public-only predictor;
3. the registered policy was nonvacuous on three of six social/blog networks;
4. its safety and nonvacuity held on a disjoint one-time holdout.

The candidate remains a GAP-style inference-closed LP adaptation, not an
official GAP reproduction and not a novel architecture. The publishable
methodological contribution is the certified no-harm deployment policy,
finite-population theorem, conservative joint RDP accounting, and empirical
privacy-utility phase behavior.

## Scope and limitations

- The theorem certifies deterministic-corruption pairwise ranking utility, not
  ROC-AUC itself.
- The finite-population result concerns the registered sealed holdout, not
  temporal or cross-domain generalization.
- Every epsilon-grid cell is an alternative mechanism. Releasing the full grid
  on one private graph would require additional composition.
- The historical P3 split manifest records that the payloads were untouched at
  creation time. `data/manifests/r5_test_access.json` is the authoritative
  superseding record after the R5 one-time access.
