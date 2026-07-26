# R8 Mock IEEE TIFS Review

## Recommendation

`MAJOR REVISION, POSITIVE`

## Summary

The manuscript studies a deployment problem in federated edge-private link
prediction. Instead of claiming a universally superior graph learner,
CertFed-LP privately tests whether a frozen inference-closed structural branch
improves a public-only scorer on a registered target population and otherwise
falls back. The paper provides role-wise transcript accounting, a private
finite-population certificate, feasibility analysis, and a preregistered
six-network evaluation.

## Strengths

1. The problem is operationally meaningful and the contribution is distinct
   from another encoder architecture.
2. The privacy output is unusually explicit: server-visible training
   messages, released state, certificate statistics, decision, and
   post-processed scores are separated from research-only metrics.
3. The one-time sealed protocol, five seeds, immutable records, exact RDP
   arrays, and clean-clone artifact are stronger than typical empirical FGL
   reporting.
4. The policy result is heterogeneous and falsifiable: it activates only
   15/30 cells and exposes harmful always-structural cases rather than hiding
   them.
5. The revised paper avoids broad first-of-kind and universal-superiority
   claims and positions FedHGPP, DPLP, PDGL, PrivFGL, and private
   recommendation accurately.

## Major concerns

### 1. Adjacency is narrower than many readers will initially assume

The formal guarantee concerns one frozen role-labelled edge, not one edge in
the raw graph before partitioning. This is now disclosed in the abstract and
theorem. It remains a substantive limitation, and the application must
justify why role labels are fixed independently of the protected record.

### 2. The no-harm theorem is finite-population and protocol-dependent

It does not certify future links, temporal transport, or standard ROC-AUC.
The random-sampling step requires the target population to be fixed before
assignment outputs. A public deterministic hash is unsafe against adaptive
population construction. The revised ideal/ROM/PRF distinction is acceptable,
but deployment must implement the stronger contract.

### 3. Candidate quality is not the contribution

The GAP-style branch is an adaptation rather than an official reproduction or
state-of-the-art learner. The paper can be accepted as a certification-policy
paper only if it avoids implying encoder superiority. Demonstrating the gate
around a second strong inference-closed candidate would improve breadth but
cannot be added using the sealed R5 holdout.

### 4. The lower bound is explanatory

The pure-DP principal-rate comparison is now correctly scoped. Approximate DP
uses the exact `D_star` term. The result does not prove minimax optimality of
the implemented Gaussian certificate for arbitrary graph populations.

## Minor concerns

- Six datasets are all social/blog networks.
- Ideal secure aggregation is a trust-model alternative, not a DP result.
- Zero observed false activations is not a universal empirical error rate.
- The paper should provide the public artifact URL and an explicit data/ethics
  statement at submission.

## Required revision for acceptance

1. Independent re-derivation of Theorems 2--4 by a privacy/statistics expert.
2. A precise deployment statement choosing ideal random draw or committed
   secret PRF, rather than public-salt language.
3. Venue-specific artifact, ethics, and data-availability material.
4. A final literature refresh on the submission date.

## Overall assessment

The manuscript is technically careful and potentially publishable in TIFS.
The remaining issues are principally scope and external validation, not a
failed accountant or contradicted primary result. A direct Accept remains
premature; a positive Major Revision recommendation is defensible.
