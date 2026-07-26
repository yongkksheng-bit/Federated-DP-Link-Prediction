# R9 Submission-Date Literature Refresh

Search date: 2026-07-27 (Asia/Shanghai).

## Protocol

The refresh repeated exact-task and near-task searches across publisher pages,
primary papers, arXiv, DBLP, and venue proceedings. Query families covered:

- federated graph link prediction with differential privacy;
- edge-private federated or decentralized graph learning;
- private recommendation over distributed graphs;
- cross-client graph representation release;
- link-inference attacks against federated GNNs; and
- private hypothesis selection and deployment certification.

The search revisited the forward and backward neighborhoods of DPLP, GAP,
Solitude, LGA-PGNN, PDGL, PrivFGL, PP-HGRL, CF-DPGNN, and FedHGPP. Technical
classification used primary papers or publisher records, not search snippets.

## New high-risk neighbors

### CE-FedGNN

Guo et al., [Provably Communication-Efficient and Privacy-Preserving
Federated Graph Neural Networks](https://arxiv.org/abs/2605.26243), arXiv,
2026.

CE-FedGNN explicitly models cross-client graph coupling, infrequently
exchanges moving-average node representations, proves convergence, and gives
RDP-composed metric-DP guarantees for released embeddings under a
public-cohort threat model. It is a close systems neighbor and must be cited.
It does not provide ordinary add/remove-edge DP for the role-labelled edge
database, a private target-domain utility certificate, or a no-harm fallback
policy. It therefore narrows the positioning but does not trigger the exact
predecessor stop condition.

### Federated-GNN link-inference attack

Yang et al., [Poisoning-Based Link Inference Attacks Against Federated Graph
Neural Networks](https://doi.org/10.56553/popets-2026-0042), PoPETs 2026.

The paper demonstrates link inference through observable representation
shifts induced by poisoning in federated GNNs. It strengthens the motivation
for complete output accounting and inference closure. It is an attack paper,
not a private deployment certificate.

## Other screened 2026 neighbors

- Wei et al., [SaGD: A Node-Level Differentially Private Graph Learning
  Framework with Sensitivity-Aware Gradient
  Descent](https://doi.org/10.1145/3774904.3792223), WWW 2026, gives rigorous
  node-DP sensitivity control for centralized graph learning. Its privacy unit,
  task, and deployment output differ.
- Liang et al., [Criticality-Aware Adaptive Local Differential Privacy for
  Privacy-Preserving Decentralized Graph
  Data](https://doi.org/10.3390/sym18040689), 2026, studies adaptive local
  perturbation rather than a central edge-DP certificate.
- FedHGPrompt and FedSkeleton were screened as federated graph/privacy
  neighbors, but their tasks and formal privacy objects do not match the
  registered LP deployment problem.

## Forward/backward trace outcome

The refresh found additional work on metric-private embedding exchange,
node-DP sensitivity, local graph perturbation, and link-inference attacks.
None simultaneously provides:

1. distributed ordinary interaction-edge ownership;
2. an inference-closed, role-labelled add/remove-edge-DP structural branch;
3. a private bounded-utility certificate on a frozen target population;
4. a material-gain activation rule with public-only fallback; and
5. finite-population no-harm and certification-cost bounds.

The manuscript now cites CE-FedGNN and the PoPETs attack and continues to avoid
any "first federated private link prediction" claim.

## Decision

`NO_EXACT_PREDECESSOR_FOUND`

The defensible contribution remains private deployment certification and
fallback under heterogeneous structural utility. This decision is valid for
the 2026-07-27 search date and must be refreshed again if submission occurs
materially later.
