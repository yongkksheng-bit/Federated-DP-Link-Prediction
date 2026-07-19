# P1 Mechanism-Feasibility Closeout

Closed: 2026-07-19 (Asia/Shanghai).

## Decision

**GO to P2 source and pilot protocol with a provisional public-coarsened
affinity release family. Real-data access remains closed until that protocol is
committed.**

P1 did not select a final neural architecture. It established that a
low-dimensional, sensitivity-one, inference-closed structural statistic can
carry private link signal under edge-DP and identified the conditions under
which that signal fails.

## Evidence chain

1. Reference block release: preregistered GO on two assortative synthetic
   domains, 60 records and 30 paired seeds.
2. Stress matrix: ADVANCE across 22/22 required cells and 1600 records; public
   group quality and release sparsity were the main failure axes.
3. Generalized affinities: the soft pair-feature candidate beat all fixed
   public-only controls but was REJECTED because it underperformed hard-group
   DP in both domains.
4. Post-hoc hard-control audit: 80/80 comparisons cleared the previously frozen
   +0.02 and paired-CI thresholds. This selects a provisional P2 family but is
   explicitly not confirmatory evidence.

## Provisional mechanism family

The candidate family is a **public-coarsened affinity release**:

- derive a fixed low-dimensional partition or coarsening from public node
  inputs only;
- release Gaussian-perturbed private edge counts/affinities over public cells;
- use unique edge ownership and an L2-sensitivity-one vector query;
- report individually visible client messages and ideal secure aggregation as
  separate regimes; and
- score links only from the DP release and public inputs.

This is a mechanism family, not yet a named paper method. P2 may add a
hierarchical or residual construction only after deriving its joint sensitivity
and registering an untouched pilot comparison.

## Known boundaries

- At 50% public-group corruption, the mixed blog reference loses practical
  value.
- Higher release dimension exposes Gaussian and visible-message penalties.
- At 20 clients in the sparse blog regime, visible-message cross AUC is 0.5680
  versus 0.6002 under ideal secure aggregation.
- The continuous soft pair-feature map suffers errors-in-variables attenuation
  and is closed as a failed candidate.
- All evidence is synthetic. No claim about a real graph or journal-level
  utility is admissible.

## P2 admission requirements

Before any real graph is downloaded or parsed, P2 must commit:

1. dataset provenance, license, immutable checksums, and public/private field
   classification;
2. client ownership and candidate-pair construction independent of test edges;
3. development/validation/sealed-test boundaries and one-time access logging;
4. untouched pilot seeds or domains for confirmatory validation of the
   provisional family;
5. public-only, random, nonprivate oracle, matched DP hard release, and relevant
   external baseline roles;
6. exact RDP accountant, visibility model, release dimension, and failure gate.

P1 is closed without authorizing a first claim, final method, or real-data run.
