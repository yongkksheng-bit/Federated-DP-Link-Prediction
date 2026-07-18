# P0 Full-Text and Citation Audit

Audit date: 2026-07-18 (Asia/Shanghai).

## Evidence levels

- **F1**: full paper inspected from an author, publisher, proceedings, or archival preprint source.
- **F2**: publisher-rendered article text or substantial official preview inspected, but equations, tables, or appendices may be unavailable.
- **A**: authoritative abstract and bibliographic record only.
- **M**: citation-index metadata used only to discover a source. It cannot establish a technical claim.

Unknown fields remain unknown. A title containing "differential privacy" or "federated graph" is not evidence of an edge adjacency definition, transcript guarantee, or private link-prediction output.

## Priority 2025--2026 verification

### FedGNNLDP (Computers & Security, 2026)

- Identity: Yaqi Liu, Yue Zhang, Pinzhen He, and Shuzhen Fang, [FedGNNLDP](https://doi.org/10.1016/j.cose.2025.104757), volume 161, article 104757.
- Evidence: **F2**. The publisher page exposes the introduction, method overview, section summaries, and references; the complete licensed PDF was not publicly available during this audit.
- Ownership: subgraphs of a larger graph are distributed across clients.
- Mechanism: the exposed method description randomizes selected dimensions of per-node embedding features to produce epsilon-LDP features before federated training. It explicitly contrasts this with perturbing uploaded parameters.
- Claimed protected data: node features or labels and, in prose, graph topology. The exposed text does not provide an ordinary add/remove-edge adjacency definition for the complete federated transcript.
- Task: the exposed experiment section discusses GNN prediction accuracy, LDP impact, and runtime. A link-prediction-specific released scorer and cross-client candidate protocol were not established by the accessible text.
- Relation: mandatory near predecessor for locally perturbed federated graph training, but not evidence that the target add/remove edge-DP LP output contract has already been solved.

### PrivFGL (TrustCom, 2025)

- Identity: Songyan Zhang, Hanyu Lu, and Hongfa Ding, [PrivFGL](https://doi.org/10.1109/TRUSTCOM66490.2025.00307), pp. 2606--2611.
- Evidence: **A**. IEEE identifies document 11354599, but neither an accessible full paper nor an author manuscript was available during this audit.
- Verified from the abstract: PrivFGL attributes DP-FGL utility loss to noise-amplified client heterogeneity and applies a local Personalized Data Transformation module to perturbed client data. It evaluates two datasets against one heterogeneity-oriented method.
- Not verified: graph ownership, graph task, neighboring-dataset definition, clipping unit, accountant, adversary, test-edge message passing, and released output.
- Backward-reference signal: the available bibliography is dominated by heterogeneous DP-FL and personalized data transformation, with only a small graph-learning component. This helps classify the paper but does not replace its missing method text.
- Relation: adjacent DP-FGL utility method. It cannot yet be admitted as an edge-DP LP baseline or used to support an exact novelty claim.

### PPGNN (arXiv, 2026)

- Identity: Longzhu He et al., [Towards Personalized Differentially Private Learning for Decentralized Local Graphs](https://arxiv.org/abs/2607.04777).
- Evidence: **F1**.
- Ownership and adversary: users locally hold node features; an untrusted server collects perturbed features.
- Privacy object: personalized LDP for node features and privacy-level choices. The paper explicitly gives the server the node set and complete adjacency matrix and states that the topology remains intact during training.
- Task: the formal and empirical pipeline is node-feature-private graph learning, with node classification as the instantiated downstream task.
- Relation: current decentralized private graph-learning competitor, but it does not protect ordinary graph edges and therefore does not overlap the target edge-DP contract.

### Privacy-Assured Analytics on Decentralized Graphs (TrustCom, 2025)

- Identity: Longji Li, Yifeng Zheng, Songlei Wang, Zhongyun Hua, Lei Xu, and Yansong Gao, [Privacy-Assured Analytics on Decentralized Graphs: The Case of Graph Learning](https://doi.org/10.1109/TRUSTCOM66490.2025.00162), pp. 1396--1405.
- Evidence: **A**. The exact paper was discovered through backward and same-venue tracing. Full technical fields remain unverified.
- Relation: mandatory unresolved competitor because its title and ownership language directly approach the decentralized-private-graph intersection. P0 cannot be declared complete until its adjacency, task, and output are inspected or an explicit access limitation is recorded for submission.

## Earlier works promoted by backward tracing

### Solitude (IEEE TIFS, 2022)

- Identity: Wanyu Lin, Baochun Li, and Cong Wang, [Towards Private Learning on Decentralized Graphs with Local Differential Privacy](https://doi.org/10.1109/TIFS.2022.3198283).
- Evidence: **F1**, using the archival author manuscript.
- Ownership: each user holds a local graph view, including an adjacency list and node features; a curator collects locally randomized reports.
- Privacy: formal edge-LDP and feature-LDP collection mechanisms.
- Task: node classification is instantiated. The paper says the collected noisy graph can support link prediction, but it does not evaluate or release a federated LP scorer.
- Relation: a strong predecessor for decentralized edge-private graph collection. It rules out novelty based only on distributed edge ownership plus edge-LDP.

### LGA-PGNN (IEEE TIFS, 2024)

- Identity: Xinjun Pei et al., [Privacy-Enhanced Graph Neural Network for Decentralized Local Graphs](https://doi.org/10.1109/TIFS.2023.3329971).
- Evidence: **A/F2**. The publisher bibliographic record and substantial abstract/reference trail were available; a complete accessible manuscript was not located during this pass.
- Verified scope: decentralized local graphs, local-DP perturbation, local neighborhood augmentation, attribute-inference and link-stealing attacks.
- Not established in this pass: an ordinary add/remove-edge federated transcript guarantee or a private LP release.
- Relation: strong near predecessor for decentralized graph LDP and topology attack evaluation.

## Forward citation tracing

### FedGNNLDP citations found as of the audit date

Citation-index discovery returned three 2026 papers. Their primary sources show that none establishes the target static federated edge-DP LP contract:

1. *Secure and Differentially Private Federated Graph Learning for Molecular Property Prediction* addresses graph-level molecular property prediction.
2. [DG-CoLearn](https://arxiv.org/abs/2605.31427) handles collaborative dynamic graphs and evaluates link prediction, but its client-oblivious privacy model trusts a coordinator with global topology and is not differential privacy.
3. [CA-LDP](https://doi.org/10.3390/sym18040689) publishes a synthetic graph from decentralized edge reports under adaptive LDP and evaluates node classification and link-inference resistance; it is not federated LP model training.

### PrivFGL citations found as of the audit date

No indexed citing paper was found. This is not evidence that no citation exists; the paper is recent and citation indexes lag.

## Additional forward-risk items

- [FedLink](https://openreview.net/forum?id=D7PiCkdiqN) and [DG-CoLearn](https://arxiv.org/abs/2605.31427) make broad novelty based on federated link prediction unsafe even without DP.
- [CA-LDP](https://doi.org/10.3390/sym18040689) and Solitude make novelty based on decentralized edge-LDP collection unsafe even without federated LP.
- PPGNN makes novelty based on personalized private decentralized graph learning unsafe, but its public-topology assumption cleanly separates it from private-edge LP.

## Citation-tracing conclusion

The surviving gap is narrower than the initial keyword search suggested. A future contribution must distinguish itself simultaneously from decentralized edge-LDP graph collection and reconstruction, federated LP without formal edge-DP, federated graph training with feature/representation/update perturbation, and centralized edge-DP LP.

The exact intersection remains provisional: ordinary add/remove-edge DP for the complete federated transcript and an inference-closed LP output, with cross-client candidates and utility beyond public inputs. This is a working gap, not a submission-ready "first" claim.

## Open verification queue

1. Obtain or author-contact the full PrivFGL paper.
2. Obtain the full TrustCom 2025 privacy-assured analytics paper.
3. Inspect the full LGA-PGNN definitions and experimental task tables.
4. Trace forward citations of Solitude, LGA-PGNN, DPLP, GAP, FKGE, and FedLink in at least two independent indexes immediately before submission.
5. Re-run the frozen query families immediately before freezing P1 and again before manuscript submission.
