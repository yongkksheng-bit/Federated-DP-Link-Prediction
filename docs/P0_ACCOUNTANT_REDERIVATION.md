# P0 Accountant Re-Derivation Audit

Audit date: 2026-07-18. This is a theorem-scope audit, not a reproduction of
either method and not an allegation that a published result is invalid.

## Common rules

For RDP order `alpha`, adaptive sequential composition adds RDP costs. Parallel
composition uses a maximum only when neighboring datasets can change at most
one genuinely disjoint component. Executing mechanisms at different times or
pipeline stages does not by itself establish parallel composition.

Pure `epsilon_a`-DP implies `(alpha, epsilon_a)`-RDP for every `alpha>1` as a
safe conversion. A Gaussian query with L2 sensitivity `Delta` and noise
standard deviation `sigma_abs` has the basic per-release bound

`rho_alpha = alpha * Delta^2 / (2 * sigma_abs^2)`.

After composing `rho_alpha`, conversion is

`epsilon(delta) = min_alpha [rho_alpha + log(1/delta)/(alpha-1)]`,

unless a documented tighter conversion is used. Sampling amplification is
valid only for the implemented sampling law and privacy unit.

## PP-HGRL

### Reconstructed protected components

- `D_aux`: client-owned user-user or item-item auxiliary edges processed by
  PGDP before one-shot upload.
- `D_uv`: server-owned user-item interaction edges processed by GEP during
  centralized training.

PGDP allocates `epsilon_a=gamma*epsilon` to randomized response and
`epsilon_d=(1-gamma)*epsilon` to noisy degree release. Adaptive edge sampling
is post-processing, so PGDP is `epsilon_a+epsilon_d=epsilon` pure edge-DP for
the protected auxiliary adjacency list.

The paper bounds one normalized graph-convolution query's edge sensitivity by
one and assigns one GEP application `alpha/(2*sigma^2)` RDP. With `J`
applications and no amplification, safe sequential composition is

`rho_GEP(alpha) = J*alpha/(2*sigma^2)`.

### Joint accounting cases

1. If `D_aux` and `D_uv` are explicitly disjoint protected databases and one
   neighboring change can affect only one component, the joint release admits
   the safe bound

   `rho_joint(alpha) = max(epsilon_PGDP, rho_GEP(alpha))`.

2. If one protected relationship can influence both stages, or the claim is
   made for an undifferentiated HIN edge universe, sequential composition is

   `rho_joint(alpha) <= epsilon_PGDP + rho_GEP(alpha)`.

The paper motivates parallel composition by different execution stages. Stage
separation alone is insufficient; the first case requires the disjoint
relation/ownership interpretation above. A matched baseline must declare which
case it implements and convert the final RDP curve to `(epsilon,delta)`.

PP-HGRL does not provide an independently budgeted pair-score transcript. Its
scores are admissible as post-processing only if deployed embeddings and model
state are DP releases and inference never rereads unprotected graph state.

## CF-DPGNN

Let `g_s(D)` be a gradient for sampled subgraph `s`, clipped to norm `C`. A
private edge may affect multiple overlapping sampled subgraphs. Let `R_e(B)`
be the maximum number of affected subgraphs in a realized minibatch `B`.

Without a tighter coupling argument, the batch-sum sensitivity is bounded by

- `C*R_e(B)` when adjacency only inserts/removes clipped contributions under a
  fixed subgraph universe; or
- `2*C*R_e(B)` when adjacency can replace/change existing clipped gradients.

Thus Gaussian calibration cannot use `C` alone unless the sampler proves
`R_e(B)=1` or an amplification theorem integrates the distribution of `R_e`.
CF-DPGNN supplies a moment expression based on a random maximum node
multiplicity. Before reuse, a reproduction must prove that this random variable
upper-bounds **edge influence multiplicity** for the exact popularity-aware,
without-replacement sampler and that the cited amplification theorem applies to
overlapping graph examples.

For `T` updates, a conservative fallback is to calibrate each update to a
deterministic worst-case `R_max` and compose all `T` RDP costs. This may be
loose but is auditable. The published nominal epsilon is not a matched privacy
budget for this project until the sampler-specific derivation is reproduced.

## Consequences for this project

1. PP-HGRL and CF-DPGNN remain mandatory baselines, but their reported epsilon
   values cannot be copied into a fairness table.
2. Every baseline receives either an independently verified accountant under
   its exact sampler or a conservative common accountant.
3. The proposed method must log the complete RDP curve, selected order,
   `delta`, sampling law, sensitivity bound, number of compositions, and server
   visibility model.
4. Accountant unit tests must cover neighboring synthetic datasets and all
   preprocessing paths before any real-data run.
