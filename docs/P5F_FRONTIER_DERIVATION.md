# P5F Federated Edge-DP Privacy-Utility Frontier

## Scope

This phase characterizes when an inference-closed private structural release is
information-bearing under the frozen federated threat model. It does not claim
that a release-energy index alone determines downstream AUC.

## Trust-model penalty

Let one row-bounded aggregation query have signal `S=A Z` in `R^(n x d)` and
per-client Gaussian standard deviation `sigma`. With disjoint canonical edge
ownership, visible client messages compose in parallel for privacy, but the
server sums `K` independently perturbed full messages. Therefore

`W_visible ~ N(0, K sigma^2 I)`,

whereas an ideal secure-aggregation functionality permits

`W_ideal ~ N(0, sigma^2 I)`.

For release dimension `p=nd`, expected squared noise norms are exactly
`K p sigma^2` and `p sigma^2`. Thus visible-message observation incurs a factor
`K` noise-energy penalty, or `sqrt(K)` in noise norm, without changing the
nominal RDP calibration of each sensitivity-bounded query.

## Signal and degree frontier indices

Define the research diagnostic

`F_signal = ||A Z||_F^2 / E||W||_F^2`.

If every public encoding row has norm at most one, then the aggregation row for
node `u` has norm at most its private training degree `d_u`. Consequently,

`F_signal <= F_degree = sum_u d_u^2 / E||W||_F^2`.

`F_degree` is an encoder-independent feasibility upper bound for this release
family. For `t=log(2/beta)`, the Laurent--Massart chi-square bound additionally
places the Gaussian noise norm, with probability at least `1-beta`, in

`sigma_eff [sqrt(max(0,p-2 sqrt(p t))), sqrt(p+2 sqrt(p t)+2t)]`.

These statements are release-level theorems, not AUC guarantees. P5F tests
whether the indices predict empirical improvement over public-only inference
across privacy budgets, graph domains, and server visibility models.

Exact signal norms and degrees are internal benchmark diagnostics computed on
public research datasets treated as private for simulation. They are not part
of the deployed DP output and must not be exposed by a real private service.
