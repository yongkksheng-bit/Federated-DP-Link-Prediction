# R6 Manuscript Contract

## Fixed title

**Differentially Private Link Prediction in Federated Setting**

The title is fixed by the project. The manuscript must make its privacy output
and deployment scope explicit enough that the title is not read as protecting
arbitrary raw embedding release or a graph-backed unrestricted API.

## Paper object

The paper introduces **CertFed-LP**, an architecture-agnostic deployment policy
for federated ordinary-graph link prediction:

1. train one frozen inference-closed structural branch with edge-DP;
2. privately estimate its target-domain pairwise utility advantage over a
   public-input-only branch on disjoint certification edges;
3. activate only when a one-sided private lower certificate exceeds a frozen
   material-gain threshold; and
4. otherwise return the public branch.

The GAP-style structural branch used in R5 is an audited mechanism adaptation,
not an official GAP reproduction and not the paper's architectural novelty.

## Admissible headline claims

1. A training-only cross-domain selector cannot provide a distribution-free,
   nontrivial no-harm guarantee without a transport assumption.
2. CertFed-LP provides a finite-target-population no-harm activation guarantee
   for the registered bounded corrupted-pair utility.
3. Training and certification are jointly edge-DP under the stated
   role-labelled adjacency and inference-closure contract; the R5
   implementation reports conservative sequential RDP composition.
4. The sufficient and necessary certification counts match in their principal
   dependence on effect gap, privacy budget, and dependence factor, up to
   constants and logarithms.
5. In the preregistered one-time R5 test, the primary policy activated 15/30
   cells across three of six datasets, observed zero material false
   activations, and achieved mean disjoint-Q5 pairwise gain +0.08543.

## Forbidden claims

- no "first" claim;
- no claim that private structure, GAP, or any objective universally improves
  link prediction;
- no description of the GAP-style candidate as CertFed-LP itself;
- no claim that the certificate is a confidence bound for ROC-AUC;
- no claim of temporal, cross-domain, or individual-edge utility;
- no use of target epsilon 4 as the total R5 privacy budget;
- no claim that secure aggregation itself supplies DP;
- no claim that all 1500 diagnostic cells are jointly released under one
  privacy budget; and
- no claim that sealed research metrics are deployment outputs.

## Primary empirical unit

The only confirmatory primary cell is:

- training target epsilon 4;
- certification target epsilon 4;
- visible client messages;
- composed epsilon approximately 5.6640 at delta 2e-6;
- six datasets by five frozen seeds.

The remaining training-epsilon, certification-epsilon, and visibility grid is
diagnostic.

## Main-text evidence

| Claim | Evidence |
|---|---|
| Why direct target certification is needed | R1 non-identifiability theorem |
| Complete privacy output | R1 privacy theorem plus R5 sequential fallback |
| No-harm guarantee | R5 finite-population theorem |
| Feasibility and near-matching rate | R3 upper boundary and R4 lower bound |
| Nonvacuous real-graph behavior | R5 one-time confirmatory result |
| Candidate/reference fairness | same descriptors, train edges, split, DP accountant, and inference closure |

## Secondary or appendix-only evidence

- synthetic certificate calibration;
- detailed 1500-cell phase grid;
- ideal secure aggregation;
- historical failed architectures and learned selectors;
- implementation and source manifests; and
- full per-record provenance.

## Required reviewer-facing caveats

The primary estimand is deterministic-corruption pairwise ranking advantage.
ROC-AUC is secondary. The finite-population theorem concerns the registered
holdout. A deployed service must select one privacy cell before release. The
candidate learner can be replaced, but every replacement requires its own
training accountant and inference-closure proof.
