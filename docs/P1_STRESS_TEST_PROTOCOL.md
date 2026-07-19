# P1 Synthetic Stress-Test Protocol

Frozen before execution: 2026-07-19 (Asia/Shanghai).

## Objective

Map the boundary of the sensitivity-one block release that passed the P1
reference gate. This protocol tests whether the GO depended on perfect public
groups, low release dimension, one privacy budget, or five clients.

The graph generator, domains, adjacency, output contract, candidate construction,
and RDP accountant remain unchanged from the reference protocol. No real data
may be accessed.

## Paired design

- Domains: `social_assortative`, `blog_mixed` from the reference protocol.
- Seeds: `0..19`, paired within every stress cell.
- Delta: `1e-6`; one Gaussian release; L2 sensitivity one.
- Metrics: global, intra-client, and cross-client ROC-AUC.
- Controls: constant public-only, seeded random, and true-probability oracle.

## Stress axes

### A. Privacy x public-group misspecification

- `epsilon in {0.5,1,2,4,8}`.
- Exact corrupted-label fractions `{0,0.10,0.25,0.50}`.
- Ideal secure aggregation.
- Original public-group resolution and five clients.

A corrupted node is assigned uniformly to a different public group. The true
latent group and graph are unchanged.

### B. Release dimension x visibility

- Public refinement factors `{1,2,4}`. Each true group is split into that many
  balanced public subgroups, producing `G`, `2G`, or `4G` public groups.
- `epsilon in {1,4}`.
- Visibility in `{ideal_secagg, visible_messages}`.
- Five clients and no label corruption.

Refinement preserves the true group but increases release dimension and reduces
per-coordinate capacity.

### C. Federation scaling in the sparse-release regime

- Clients `{2,5,10,20}`.
- Public refinement factor 4, epsilon 4, no corruption.
- Both visibility models.

The underlying graph and candidates remain paired; only the fixed public home
map and canonical edge ownership are regenerated for each client count.

Total expected records: `2 domains x 20 seeds x 40 cells = 1600`.

## Frozen advancement gate

P1 stress testing advances only if all of the following hold in both domains,
for global and cross-client AUC:

1. Under ideal secure aggregation, every cell with `epsilon>=2` and corruption
   at most 25% improves over public-only by at least 0.02 AUC and its paired 95%
   CI excludes zero.
2. At epsilon 4, ideal-secagg refinement factors 1 and 2 each improve over
   public-only by at least 0.02 AUC with paired 95% CI excluding zero.
3. Every record contains the calibrated RDP curve, source commit, release
   dimension, client count, visibility model, and candidate counts.
4. Tests and deterministic replay pass, with no raw edge arrays written to
   results.

Corruption 50%, epsilon below 2, refinement factor 4, and visible-message
federation scaling are boundary diagnostics. Their failure does not change the
advancement decision and may not be hidden.

Passing authorizes design of a stronger candidate release on synthetic data.
It does not authorize real-data access.
