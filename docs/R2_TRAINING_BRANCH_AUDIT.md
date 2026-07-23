# R2 Candidate Training-Branch Audit

## Candidate

The provisional structural branch is the existing inference-closed GAP-style
perturb-message-normalize release. Public descriptors are row-normalized, each
undirected training edge contributes one bounded endpoint vector in each
direction, and every released hop is Gaussian perturbed before normalization.
Scores use only the released channels, public descriptors, and query pairs.

This is an adaptation, not an official reproduction of GAP.

## Mathematical admission

Conditional on previous released hops, every row of the current channel has L2
norm at most one. Adding or removing undirected edge `{u,v}` changes the
pre-normalization aggregation by one bounded vector in row `u` and one in row
`v`. The whole-matrix L2 sensitivity is therefore at most `sqrt(2)`.

For `H` released hops with absolute coordinate noise standard deviation
`sigma_abs`, the conservative RDP curve is

`rho_T(alpha) = H*alpha*2/(2*sigma_abs^2)`.

Normalization and pair scoring are post-processing. The release is
inference-closed provided no score path reconstructs or rereads the private
adjacency.

## Implementation limitation found

The current `release_private_aggregations(..., visibility="visible_messages")`
helper directly samples the distribution of the *sum* of `K` independent
client noises. This is utility-equivalent for the final aggregate, but it does
not materialize the individual messages observed by the primary adversary.

Consequences:

- it is not a complete simulator of the primary server transcript;
- it cannot by itself audit per-client message sensitivity, hashes, or
  serialization; and
- it may be used only as an aggregate-utility simulator until a genuine
  per-client release path is implemented and tested.

The ideal-secure-aggregation branch is also a trust-model simulation, not a
cryptographic implementation.

## R2 decision

`ADMIT_MATHEMATICAL_BRANCH_BUT_REQUIRE_TRANSCRIPT_IMPLEMENTATION`

R2A will test the private certification mechanism on synthetic bounded utility
records and will not claim end-to-end training utility. R2B must implement and
audit actual visible client messages before any end-to-end synthetic graph or
real-data execution.
