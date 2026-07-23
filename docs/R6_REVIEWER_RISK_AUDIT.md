# R6 Reviewer-Risk Audit

## Recommendation at R6

**Submission-quality technical draft, but not an unconditional Accept claim.**

The defensible review position is positive Major Revision / borderline Accept
depending on venue expectations. R6 removes the earlier invalid universal
learner narrative and supplies a coherent contribution:

> privately certify whether an inference-closed edge-DP structural branch
> materially helps on the target graph, otherwise fall back to public-only.

## Claims that are now supported

1. Training-only branch selection has no distribution-free nontrivial no-harm
   guarantee over unrestricted target families.
2. The complete released training/certification transcript has an explicit RDP
   accountant and inference-closed output contract.
3. An edge-keyed random certification split yields a finite-population
   one-sided no-harm certificate for the registered pairwise estimand.
4. Sufficient and necessary certification counts match in principal
   dependence on effect gap, privacy, and dependence, up to constants and
   approximate-DP logarithms.
5. The preregistered R5 policy is nonvacuous on three of six networks and
   avoids every harmful primary always-structural cell.

## Claims intentionally excluded

- first federated private link prediction;
- universal structural, GAP, InfoNCE, or BCE superiority;
- a confidence interval for ROC-AUC;
- future-edge or cross-domain no-harm;
- privacy for graph-backed inference or unprotected embeddings;
- simultaneous release of all 50 diagnostic privacy cells;
- official reproduction of GAP, DPLP, PrivFGL, or another predecessor.

## Remaining reviewer risks

### High: role-labelled adjacency scope

R5 uses a frozen role-labelled database and conservative sequential
composition because the historical benchmark split was not designed to prove
edge-stable raw-graph partitioning. The manuscript states this explicitly.
Before submission, an independent privacy reviewer should confirm that the
stated adjacency is acceptable for the intended application and that no prose
silently upgrades it to raw unsplit-graph adjacency.

### High: finite target versus operational future links

The theorem certifies one sealed finite holdout. A production service requires
a temporal certification window, a transport assumption, or repeated privacy
accounting. The title is retained, but abstract, theorem, and conclusion must
continue to say finite-holdout certification.

### Medium: candidate-learner comparison

The candidate is a GAP-style adaptation, not an official reproduction and not
the method novelty. The primary baselines are policy baselines: public-only,
always structural, CertFed-LP, and a non-deployable oracle. Reviewers may still
request the gate around stronger inference-closed learners. This is valuable
future work, not evidence that may be fabricated after the sealed access.

### Medium: only six social/blog networks

The graph family is appropriate for the stated target, and all six have five
seeds. Generalization to temporal, biological, citation, or knowledge graphs
is not established.

### Medium: observed zero errors is not a population error estimate

Zero material false activations in 30 primary and 1500 diagnostic records is
empirical corroboration. Formal safety comes from the per-deployment
certificate, not from treating 0/1500 as a universal error rate.

### Medium: literature moves quickly

The P0 audit includes work through July 2026. A final forward/backward citation
refresh is mandatory immediately before submission, especially for
federated-LP, decentralized graph DP, and private recommendation.

## Pre-submission gates

- [x] Frozen claim contract and evidence map.
- [x] Correct RDP conversion in manuscript and executable records.
- [x] Complete theorem proofs and explicit scope.
- [x] Five-seed preregistered primary result.
- [x] Standard ROC-AUC retained as secondary diagnostic.
- [x] PDF has no undefined references, overfull boxes, clipped figures, or
      unbalanced blank column.
- [ ] Independent re-derivation of Theorems 2--4 by a privacy/statistics expert.
- [ ] Independent reproduction from raw source registry on a clean machine.
- [ ] Final 2026 literature refresh and bibliography expansion if new exact
      predecessors appear.
- [ ] Venue-specific anonymization, ethics/data statement, and artifact link.

## Stop conditions

Do not submit if an independent audit finds any of the following:

1. a result record whose epsilon cannot be reproduced from its RDP array;
2. certification code that performs graph-dependent negative rejection;
3. inference that rereads private topology;
4. a manuscript statement treating diagnostic cells as jointly released;
5. a claim that the finite pairwise certificate directly covers ROC-AUC.
