# P1 Synthetic Feasibility Protocol

Frozen before execution: 2026-07-18 (Asia/Shanghai).

## Purpose

P1 asks whether any inference-closed edge-DP structural release has a
nontrivial utility regime under the frozen P0 contract. It does not select the
paper's final architecture and cannot support a manuscript result.

## Reference release

Nodes have fixed public group labels. For every unordered public group pair,
clients compute the number of private training edges in that block. Each edge
contributes to exactly one coordinate, so the vector query has add/remove-edge
L2 sensitivity one.

Two server visibility models are compared:

- `visible_messages`: each client's count vector is independently Gaussian
  perturbed before the server sees it; the aggregate contains `K` independent
  noise vectors;
- `ideal_secagg`: the server sees only the summed count vector with one
  calibrated Gaussian noise vector.

The released block densities and public group labels define all pair scores.
Inference may not access training edges.

## Synthetic domains

Two preregistered stochastic-block domains are used:

| Domain | Nodes | Groups | Within probability | Between probability | Train-edge retention | Clients |
|---|---:|---:|---:|---:|---:|---:|
| `social_assortative` | 240 | 4 | 0.18 | 0.025 | 0.70 | 5 |
| `blog_mixed` | 300 | 5 | 0.12 | 0.045 | 0.65 | 5 |

Public groups and client homes are balanced and fixed by each seed. Existing
edges are independently retained for the private training graph; unretained
edges are held-out positives. True nonedges are negatives. Candidate identities
are not passed to the release mechanism.

## Frozen privacy and repetition

- Edge adjacency: P0 add/remove adjacency.
- Target: `epsilon=4`, `delta=1e-6`.
- RDP orders: `1.25, 1.5, 1.75, 2..64, 128, 256`.
- One release (`steps=1`).
- Seeds: `0..29`, paired across all methods and visibility models.
- Gaussian scale is solved from the complete RDP curve and recorded.

## Comparators and metrics

- `public_only`: one constant score for every pair (AUC 0.5).
- `random`: seeded scores independent of graph data.
- `nonprivate_oracle`: true generating block probabilities.
- `nonprivate_counts`: unnoised training block-density release.
- `dp_block_counts`: the reference release under each visibility model.

Report global, intra-client, and cross-client ROC-AUC. No composite metric is
used. Each result records configuration, seed, privacy curve, selected RDP
order, noise standard deviation, release dimension, sensitivity, client sizes,
edge counts, candidate counts, and source commit.

## Go/no-go rule

The reference release passes P1 only when **ideal secure aggregation** meets all
conditions in both domains for global and cross-client AUC:

1. paired mean improvement over `public_only` is at least `0.02`;
2. the paired 95% confidence interval for that improvement excludes zero;
3. paired mean improvement over `random` has a 95% interval excluding zero;
4. mean performance does not exceed the nonprivate oracle by more than `0.02`
   AUC (a finite-sample sanity tolerance); and
5. all privacy, adjacency, inference-closure, integrity, and determinism tests
   pass.

`visible_messages` is diagnostic: failure there quantifies the federation noise
penalty and does not override an ideal-secagg GO. If ideal-secagg fails either
domain, P1 is NO-GO for this release family; no hyperparameter retuning is
allowed under this protocol.

## Analytic feasibility inequality

For blocks `a` and `b`, candidate capacities `M_a,M_b`, retained-density gap
`Delta_p`, and aggregate count-noise standard deviation `s`, distinguishability
requires approximately

`Delta_p > z * s * sqrt(M_a^-2 + M_b^-2) + sampling_error`.

Here `s=sigma` for ideal secure aggregation and `s=sqrt(K)*sigma` for visible
independently privatized messages. The experiment checks whether observed
ranking follows this predicted separation.
