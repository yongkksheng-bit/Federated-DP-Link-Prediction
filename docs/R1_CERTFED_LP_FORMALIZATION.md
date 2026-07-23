# R1 CertFed-LP Formalization

## Scope

R1 defines the mathematical object before any CertFed-LP experiment. The
framework does not attempt to predict a new graph's utility from other graph
domains. It performs a private, target-domain certification and otherwise
falls back to a public-input-only predictor.

The protected individual remains one canonical undirected edge. All statements
use add/remove-edge adjacency unless explicitly marked otherwise.

## Distributed private graph

Let `V` be a public node universe, `X` public node descriptors,
`h: V -> {1,...,K}` a public home-client map, and `o(u,v)` a public edge
ownership rule. Client `k` owns private canonical edge set `E_k`; every edge is
owned exactly once.

Two federated datasets are adjacent when one client gains or loses one
canonical edge and all public objects remain unchanged.

## Data-independent edge partition

A frozen public hash of the canonical edge and a public salt assigns every
edge to exactly one of three logical partitions:

- `E^T`: DP training;
- `E^C`: private utility certification; or
- `E^Q`: sealed research test.

The partition rule does not inspect graph statistics or model scores. Adding or
removing one edge changes at most one partition. Exact fractions are an R2
engineering parameter and must be frozen before data generation.

The test partition is not an input to training or certification. Public release
of a test metric would require a separate privacy statement; a sealed research
evaluation is not part of the deployed output.

## Two inference-closed branches

The public branch is

`s_0(u,v) = F_0(X,u,v; public randomness)`.

The candidate structural branch is

`s_R(u,v) = F_1(R,X,u,v; public randomness)`,

where `R` is the edge-DP training release. Neither branch may reread a private
edge, neighborhood, degree, or unprotected embedding at inference.

The server-visible DP training transcript and `R` are denoted `M_T(E^T)`.
R1 does not prescribe one architecture; any admitted trainer must provide its
complete RDP curve `rho_T(alpha)` under the frozen adjacency and visibility
model.

## Certification records

For a certification edge `e={u,v}`, public seeded map `q` produces one
endpoint-corrupted comparison pair `q(e)`. The map does not reject candidates
that happen to be private edges, because graph-dependent rejection would add an
unaccounted access path. False-negative comparisons are part of the registered
estimand.

For score function `s`, define bounded ranking utility

`U_s(e) = 1{s(e)>s(q(e))} + 0.5*1{s(e)=s(q(e))}`.

The per-edge advantage of the structural branch is

`d_R(e) = U_{s_R}(e) - U_{s_0}(e) in [-1,1]`.

Conditional on a fixed training release `R`, the certification query is

`Q_C(E^C;R) = (S_R,n_C)`

with

`S_R = sum_{e in E^C} d_R(e)` and `n_C=|E^C|`.

Under add/remove adjacency its L2 sensitivity is at most `sqrt(2)`: one edge
changes the sum by at most one and the count by exactly one.

The Gaussian certification mechanism releases

`(S_tilde,n_tilde) = (S_R,n_C) + N(0, 2*sigma_C^2 I_2)`.

The binary branch decision is post-processing of this release.

## Visibility models

In the primary model, the server observes every client message. Each client
therefore noises its local two-dimensional query to sensitivity `sqrt(2)`
before upload. A neighboring edge changes one client's message; client-level
parallel composition applies across disjoint edge owners, while the aggregate
contains the sum of all client noises.

In the secondary ideal-secure-aggregation model, clients contribute unnoised
local sums to the ideal functionality and only one aggregate, calibrated to
global sensitivity `sqrt(2)`, is revealed. Secure aggregation is an explicit
trust assumption, not a DP argument.

## Certified decision

The released noisy sum and count are converted to a one-sided lower bound on
the target-domain utility advantage. CertFed-LP activates `s_R` only when that
bound is at least a registered material gain `gamma>=0`; otherwise it releases
the public-only decision.

The decision certifies the protocol-defined corrupted-pair utility under the
assumptions in the no-harm theorem. It is not automatically a certificate for
standard ROC-AUC, arbitrary negative sampling, future temporal edges, or a
different graph domain.

## Deployment output

The deployed output consists of the DP transcripts, `R`, the binary decision,
and scores computed from the selected inference-closed branch. Unlimited score
queries are post-processing only because both branches use DP/public releases
and public inputs. Any implementation that rereads the private graph falls
outside the theorem.

## R1 exclusions

R1 performs no real-graph experiment, opens no P3 test, reuses no P5FC
confirmatory outcome, and acquires no future source. It does not claim that the
candidate structural learner is useful; it defines when its use can be
certified or refused.
