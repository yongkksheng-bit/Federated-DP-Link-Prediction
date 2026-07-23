# R5 Graph-Phase Confirmatory Protocol

## Question

Can target-domain private certification safely decide when an inference-closed
edge-DP structural branch should replace a public-feature link predictor,
without a learned cross-domain selector and without test-set tuning?

R5 is a confirmatory safety-and-nonvacuity study, not another search for a
universally superior graph model.

## Frozen evidence

- Six P3 social/blog networks and five P3 split seeds are used.
- Their encrypted P3 test payloads have access count zero.
- The candidate is the GAP-style inference-closed LP adaptation already tuned
  on P3 validation at epsilon 4.
- Dataset-specific projection dimensions and hop counts are copied verbatim
  from `results/p3_gap_validation/summary.json`.
- The reference is sparse cosine over the registered public descriptors.

The candidate is an audited style adaptation, not an official GAP
reproduction and not the paper's novel learning architecture.

## One-time test procedure

1. Refuse execution unless the worktree is clean, source/split audits pass,
   sealed hashes match, and no R5 access record exists.
2. Decrypt every P3 test payload once in one batched execution.
3. Partition positive holdout edges into `C5` and `Q5` using the frozen
   edge-keyed Bernoulli hash. Validation edges are never reused.
4. Produce the DP training release from P3 train edges only.
5. Compute candidate-minus-public corrupted-pair advantages on `C5`.
6. Release only a Gaussian-noised sum and count and apply the frozen
   conservative no-harm certificate.
7. Evaluate the frozen branch decision on disjoint `Q5`.
8. Write immutable provenance, accountant curves, hashes, branch decisions,
   and all declared metrics.

## Primary estimand and secondary metrics

The primary estimand is the finite original-P3-test mean pairwise ranking
advantage under a deterministic endpoint corruption with no graph-dependent
rejection. The held-out `Q5` mean tests the activated policy without reusing
certificate records.

Global, intra-client, and cross-client ROC-AUC on the original P3 negative
payload are secondary benchmark metrics. They do not replace the theorem's
registered pairwise estimand.

## Privacy

Training and certification are independently calibrated Gaussian mechanisms.
R5 conservatively adds their RDP curves, even though the registered roles are
disjoint. The primary visibility model exposes every noised client message;
ideal secure aggregation is a separately labelled trust model.

The displayed epsilon grid consists of counterfactual mechanisms. A deployment
selects one frozen cell. The paper must not describe the entire grid as one
jointly released edge-DP transcript.

## Confirmatory decisions

`PASS_NONVACUOUS_CERTIFIED_POLICY` requires:

- no activation whose full finite-holdout advantage is below `gamma=0.02`;
- at least ten activated dataset/seed/privacy/visibility cells;
- activation in at least three datasets;
- nonnegative mean `Q5` policy gain;
- exact accountant reproduction, commitment verification, one test access,
  and no test tuning.

`PASS_SAFETY_BUT_VACUOUS` means all safety/provenance checks pass but the
activation coverage or policy-gain gate fails.

`FAIL_CONFIRMATORY_CERTIFICATE` means a safety or provenance gate fails.

No threshold, candidate, corruption map, privacy grid, or gate may change after
test access. Surprising or negative outcomes are reported rather than repaired
with another test split.
