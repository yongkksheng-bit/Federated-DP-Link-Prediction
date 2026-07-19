# P1 Pair-Feature Release Protocol

Frozen before execution: 2026-07-19 (Asia/Shanghai).

## Motivation

The reference P1 gate used a constant public-only comparator and assortative
SBMs whose public groups nearly determine the ranking. That experiment remains
valid as a sensitivity/noise existence test, but it is not sufficient evidence
that private edges add utility beyond nontrivial public features.

This protocol introduces arbitrary heterophilic/mixed block affinities and
stronger public-only scores. It tests a soft pair-feature sufficient-statistic
release against hard-group DP counts under exactly the same Gaussian accountant.

## Candidate release

Every node has a fixed public unit-norm feature `x_u in R^d`. For candidate pair
`{u,v}`, define the symmetric pair feature

`psi_uv = svec((x_u x_v^T + x_v x_u^T)/2)`.

The `svec` map scales off-diagonal entries by `sqrt(2)`, preserving Frobenius
norm. Therefore `||psi_uv||_2 <= ||x_u||_2 ||x_v||_2 = 1`.

The private sufficient statistic is

`b(D) = sum_{e in E_train} psi_e`,

which has add/remove-edge L2 sensitivity at most one. The release is
`b_tilde=b+N(0,sigma^2 I)`. A public Gram matrix over all public candidate pairs
defines

`w=(H+lambda I)^-1 b_tilde`,

where `lambda=1e-3*trace(H)/dim(H)`. Scores `psi_uv^T w` are post-processing and
never reread private edges.

Visible-message and ideal-secagg variants follow the frozen P0 visibility
models. The hard-group DP control uses `argmax(x_u)` and the same epsilon,
delta, sensitivity, clients, candidates, and random seeds.

## Generalized synthetic domains

Two fixed symmetric affinity matrices are used rather than a single within/
between probability:

- `heterophilic_social`: 320 nodes, 4 latent groups, 5 clients, 65% train-edge
  retention; diagonal affinities are low and selected cross-group affinities
  are high.
- `mixed_blog`: 360 nodes, 5 latent groups, 5 clients, 65% retention; both
  within- and cross-group affinities vary non-monotonically.

Public features equal one-hot latent centers plus isotropic Gaussian corruption
at scales `{0.25,0.5,1.0}`, followed by row normalization. Latent identities and
affinity matrices are unavailable to the mechanisms.

## Frozen matrix

- Seeds: `0..29`, paired across all cells.
- Epsilon: `{1,2,4}`; delta `1e-6`; one release.
- Feature corruption: `{0.25,0.5,1.0}`.
- Visibility: `{ideal_secagg, visible_messages}`.
- Expected records: `2 x 30 x 3 x 3 x 2 = 1080`.

Each record contains both soft pair-feature DP and hard-group DP results.

## Public-only controls

- constant score;
- public cosine similarity and its negation;
- same-hard-label and different-hard-label indicators;
- seeded random score;
- true affinity probability as a non-admissible oracle upper reference.

The candidate must beat each fixed public-only control; no test-dependent
selection among controls is permitted.

## Frozen gate

The candidate advances only if:

1. In both domains, under ideal secure aggregation, every cell with
   `epsilon>=2` and feature corruption at most 0.5 improves global and
   cross-client AUC over **each** non-random public-only control by at least
   0.02, with paired 95% CI excluding zero.
2. At epsilon 4 and corruption 0.5, its paired difference from hard-group DP is
   no worse than -0.02 AUC in global and cross-client mean.
3. At epsilon 4 and corruption 1.0, it exceeds hard-group DP in cross-client
   mean AUC. This is the preregistered test of reduced hard-assignment reliance.
4. All accountant, sensitivity, inference-closure, schema, and deterministic
   replay checks pass without raw edges in results.

Visible-message cells and epsilon 1 are mandatory diagnostics. Failure of any
required condition rejects this candidate without retuning this protocol.
Passing still does not authorize real-data access.
