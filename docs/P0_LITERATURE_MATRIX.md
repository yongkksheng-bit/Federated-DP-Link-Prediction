# P0 Literature Matrix

Search date: 2026-07-18. Classification is based on primary papers or official
proceedings pages where available. An entry is an exact predecessor only when
its task, ownership model, adjacency unit, and released output all overlap.

## Exact and near predecessors

| Work | Task and ownership | Formal privacy object | Relation to this project |
|---|---|---|---|
| De and Chakrabarti, [Differentially Private Link Prediction with Protected Connections](https://doi.org/10.1609/aaai.v35i1.16078), AAAI 2021 | Centralized ranked link recommendation on a graph with designated protected connections | A graph privacy definition restricted to marked protected node pairs; noisy transformed ranking scores | Exact LP and formal privacy, but not federated ownership and not ordinary add/remove privacy for every private edge |
| Peng et al., [Differentially Private Federated Knowledge Graphs Embedding](https://doi.org/10.1145/3459637.3482252), CIKM 2021 | Asynchronous peer-to-peer alignment across multiple cross-domain knowledge graphs; triple classification and KG link prediction | PATE-style DP for generated embeddings; neighboring datasets differ by one embedding in the generator input | Covers federated, DP, and LP, so a broad "first federated DP link prediction" claim is false. It is not an add/remove edge-DP method for a partitioned ordinary graph |
| Sajadmanesh et al., [GAP](https://www.usenix.org/conference/usenixsecurity23/presentation/sajadmanesh), USENIX Security 2023 | Centralized private GNN, evaluated primarily on node classification | Add/remove edge-DP and node-DP for cached noisy multi-hop aggregations; inference is post-processing because raw adjacency is not queried again | Establishes the inference-closure standard and a strong aggregation-perturbation baseline, but is not federated LP |
| Ran et al., [Differentially Private Graph Neural Networks for Link Prediction](https://doi.org/10.1109/ICDE60146.2024.00133), ICDE 2024 | Centralized subgraph-based GNN link prediction | Edge-private subgraph extraction with neighborhood- and path-subgraph sensitivity analysis | Closest formal edge-DP LP predecessor. Any method must compare against its extraction/sensitivity strategy; it does not address federated edge ownership |
| Lin et al., [Solitude](https://doi.org/10.1109/TIFS.2022.3198283), IEEE TIFS 2022 | A curator learns from adjacency lists and features held by decentralized users; node classification is instantiated | Formal local edge-DP and feature-LDP collection; the server reconstructs and calibrates a noisy graph | Strong predecessor for decentralized edge-private graph collection. It mentions LP as a possible downstream task but does not evaluate or release a federated LP scorer |
| Pei et al., [LGA-PGNN](https://doi.org/10.1109/TIFS.2023.3329971), IEEE TIFS 2024 | GNN learning from decentralized local graphs | LDP perturbation plus local graph augmentation; evaluates attribute-inference and link-stealing attacks | Strong decentralized graph-privacy near predecessor. Full adjacency and output-contract fields remain under verification; no private LP release was established in this pass |
| Tang and Hu, [A Privacy-Enhancing Mechanism for Federated Graph Neural Networks](https://doi.org/10.3390/sym17040565), Symmetry 2025 | Federated GNN link prediction on CoraML with GAT/GCN/GraphSAGE | Client-side gradient clipping and local noise, described as LDP against inference attacks | Direct near predecessor for federated LP with local perturbation. The accessible paper does not establish the same add/remove-edge output contract targeted here |
| Yao et al., [Federated Link Prediction on Dynamic Graphs](https://openreview.net/forum?id=D7PiCkdiqN), NeurIPS NPGML Workshop 2025 | Dynamic federated link prediction with bounded history buffers | No formal add/remove edge-DP guarantee identified in the paper abstract | Exact federated LP task, but primarily an efficiency and temporal-heterogeneity contribution |
| FedGNNLDP, [Federated graph neural network with locally differential privacy](https://doi.org/10.1016/j.cose.2025.104757), Computers & Security 2026 | Subgraphs of a larger graph distributed across clients | Randomizes selected dimensions of per-node embedding features to produce epsilon-LDP features before federated training | Mandatory feature-LDP FGL predecessor. The publisher-exposed method text does not establish ordinary add/remove-edge adjacency, complete-transcript accounting, or an LP-specific released scorer |
| Guo et al., [CE-FedGNN](https://arxiv.org/abs/2605.26243), 2026 preprint | Coupled federated graphs with infrequent aggregated representation exchange | RDP-composed metric-DP for released representations under a public-cohort threat model | Important current competitor for cross-client dependencies, but metric-DP in embedding distance is not worst-case add/remove edge-DP |
| He et al., [PPGNN](https://arxiv.org/abs/2607.04777), 2026 preprint | Users hold private node features; the server holds the complete node set and adjacency matrix | Personalized LDP for node features and privacy-level choices | Current decentralized private graph learner, but explicitly leaves topology public and therefore does not protect ordinary graph edges |

## Federated graph-learning neighbors

| Work | Contribution | Missing axis for exact overlap |
|---|---|---|
| Baek et al., [Personalized Subgraph Federated Learning](https://proceedings.mlr.press/v202/baek23a.html), ICML 2023 | Personalized learning when a global graph is split into private interconnected subgraphs | No formal edge-DP link-prediction release |
| FedGCN, [Convergence-Communication Tradeoffs in Federated GCN Training](https://openreview.net/forum?id=ody3RBUuJS) | Cross-client neighbor handling and communication trade-offs | Node classification focus; privacy is not the fixed add/remove-edge output guarantee |
| [FedGraph](https://openreview.net/forum?id=d48HjofVrf), 2025 | Scalable FGL library with cross-client edges, encrypted aggregation, and LP support | Encryption/secure aggregation is not differential privacy |
| PrivFGL, [Differentially Private Federated Graph Learning via Personalized Data Transformation](https://doi.org/10.1109/TRUSTCOM66490.2025.00307), TrustCom 2025 | Uses local personalized data transformation to mitigate perturbation-amplified client heterogeneity | Only the abstract was accessible; graph ownership, task, adjacency, accountant, and released output remain unverified, so it is not yet an edge-DP LP baseline |
| Li et al., [Privacy-Assured Analytics on Decentralized Graphs: The Case of Graph Learning](https://doi.org/10.1109/TRUSTCOM66490.2025.00162), TrustCom 2025 | Exact task and ownership fields pending full-text access | Privacy definition and released output pending full-text access | Mandatory unresolved competitor discovered by backward and same-venue citation tracing |
| [DG-CoLearn](https://arxiv.org/abs/2605.31427), 2026 preprint | Collaborative dynamic graphs with cross-client edges; evaluates node classification and LP | Client-oblivious confidentiality model with a trusted coordinator holding global topology; no DP guarantee | Direct current federated or collaborative LP neighbor, but not an edge-DP method |
| [FedGraph-LDP mechanism](https://doi.org/10.3390/sym17040565), 2025 | LDP perturbation of federated GNN gradients | Does not by itself resolve inference that rereads private adjacency |

## Central private graph-learning neighbors

| Work | Relevance |
|---|---|
| GAP, USENIX Security 2023 | Strong edge-DP aggregation and inference-closure precedent |
| DPLP, ICDE 2024 | Strongest centralized formal link-prediction baseline |
| EdgeRefine, [2026 preprint](https://arxiv.org/abs/2607.08659) | Very recent local edge-private graph perturbation; evaluated on node/graph classification rather than federated LP |
| DyGAN-EDP, [Neurocomputing 2026](https://doi.org/10.1016/j.neucom.2026.132926) | Edge-private dynamic graph generation for downstream tasks, including temporal LP |

## Attack and deployment precedents

- GAP explicitly shows why a model trained with DP is not automatically private
  at inference when prediction queries the raw graph again.
- Link-stealing and graph-reconstruction attacks motivate treating embeddings,
  intermediate representations, and unrestricted score APIs as separate
  outputs, not harmless implementation details.
- Secure aggregation hides individual messages from the server but does not
  replace a DP guarantee for the final aggregate or downstream interface.

## Current matrix conclusion

No checked work simultaneously establishes all of the following:

1. one ordinary graph whose private edges are distributed across clients;
2. add/remove edge-level DP against an explicitly stated federated adversary;
3. link prediction including cross-client candidate pairs;
4. a complete server-visible transcript accountant;
5. a released scorer whose inference does not reread an unprotected private
   graph; and
6. utility beyond matched public-input-only and zero-private-signal controls.

This is a provisional intersection gap, not yet a novelty claim. The first
forward and backward citation pass is recorded in
`P0_FULLTEXT_AND_CITATION_AUDIT.md`. Full-text access for PrivFGL and the
TrustCom privacy-assured analytics paper, plus a second pre-submission citation
pass, remain mandatory.
