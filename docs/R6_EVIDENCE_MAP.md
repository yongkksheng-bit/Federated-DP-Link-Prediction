# R6 Evidence Map

## Main theorem chain

1. `R1_NONIDENTIFIABILITY_THEOREM.md`: training-only no-harm selection is
   impossible over an unrestricted target family.
2. `R1_PRIVACY_THEOREM.md`: adaptive training and certification transcript
   accounting under role-labelled edge adjacency.
3. `R5_FINITE_POPULATION_THEOREM.md`: random-hash certification removes the
   unproved graph-dependence factor for the registered finite holdout.
4. `R3_FEASIBILITY_BOUNDARY_THEOREM.md`: sufficient certification count and
   minimum detectable effect.
5. `R4_LOWER_BOUND_THEOREM.md`: necessary count with matching principal
   dependence on effect gap, epsilon, and dependence.

## Main empirical chain

1. `configs/r5_graph_phase_confirmatory.json`: preregistered primary cell and
   gates.
2. `data/manifests/r5_test_access.json`: authoritative one-time access record.
3. `results/r5_graph_phase_confirmatory/records.jsonl`: 1500 raw records.
4. `results/r5_graph_phase_confirmatory/summary.json`: decision and diagnostic
   cells.
5. `results/r5_graph_phase_confirmatory/audit.json`: independent completeness
   and accountant audit.
6. `docs/R5_CONFIRMATORY_REPORT.md`: human-readable interpretation.

## Baseline roles

- **Public-only:** sparse cosine over registered public descriptors; safe
  fallback and zero-gain reference.
- **Always structural:** the frozen edge-DP GAP-style LP adaptation; tests
  whether unconditional private-structure deployment is harmful.
- **CertFed-LP:** certified policy; this is the proposed deployment mechanism.
- **Oracle:** activates from Q5 sign and is never deployable; upper reference
  only.

Central DPLP-style and other graph-DP learners are related learning mechanisms,
not substitutes for the policy comparison. They belong in related work and
secondary learner audits, with privacy-scope mismatches labelled.

## Result facts locked for prose

- Primary composed privacy: epsilon 5.6640, delta 2e-6.
- CertFed-LP: +0.08543 mean Q5 policy gain.
- Always structural: +0.07945 mean Q5 gain and 10/30 harmful records.
- Oracle: +0.09112 mean Q5 gain.
- CertFed-LP mean regret to oracle: 0.00568.
- Activated: 15/30, exactly all five seeds on BlogCatalog, GitHub Social, and
  PolBlogs.
- Conservative fallback: all five seeds on Deezer, Facebook, and LastFM.
- Material false activations in primary: zero observed.
- Diagnostic records: 1500/1500; no material false activation observed.
