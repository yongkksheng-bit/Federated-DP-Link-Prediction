# P2 Data, Partition, and Sealed-Test Contract

Frozen before source acquisition: 2026-07-19 (Asia/Shanghai).

## Canonicalization

External node IDs are mapped to contiguous internal IDs by lexicographic order
of their canonical string representation. Self-loops are removed. Each edge is
stored once as `(min(u,v), max(u,v))`; duplicate rows are removed and counted in
the local audit. The parser must compare resulting counts with the source
registry and stop on unexplained differences.

## Public client assignment and ownership

Client membership cannot depend on private graph structure. Nodes are sorted by
`SHA256(dataset_id || home_seed || external_node_id)` and assigned round-robin
to five clients. This `balanced_sha256_rank` map is deterministic, balanced to
within one node, and uses no edge.

The owner of canonical edge `(u,v)`, where `u<v`, is `home(u)`. Every training
edge therefore appears in exactly one client. Cross-client status depends only
on the public home map.

## Public coarsening

The provisional P1 release requires low-dimensional public cells. P2 fixes 16
cells for both domains. Sparse public descriptors are row-normalized, projected
to at most 16 dimensions by deterministic TruncatedSVD, and clustered by
deterministic K-means. Fitting may read public descriptors and node IDs only.
It may not read edges, degrees, labels derived from edges, validation outcomes,
or test identities.

Sixteen cells yield 136 unordered block counts. Adding or removing one uniquely
owned edge changes exactly one count by one, so the joint L2 sensitivity of the
global count vector is one.

## Splits and candidates

For each of five frozen seeds, canonical positive edges are split 70/10/20 into
train/validation/test within public intra/cross strata. Negative pairs are
sampled uniformly without replacement from canonical nonedges at a 1:1 ratio
within the same strata. All methods receive identical clients, candidates,
splits, and seeds.

Split construction is performed by the trusted benchmark owner. Test positive
and negative identities are encrypted into `data/sealed/`; tracked manifests
contain only salted commitments, counts, and schema metadata. No training,
tuning, plotting, or debugging command can load the sealed payload.

## One-time test rule

Development may use synthetic P1 data. P2 may inspect training metadata and
validation metrics only. After source parsing and validation checks, the method,
coarsening, privacy parameters, baselines, and code commit are frozen. A
separate finalization command then evaluates all five seeds in one batch and
writes an append-only access record containing timestamp, commit, config hash,
manifest hash, and result hash.

Failure on sealed test is a scientific failure. The same test payload may not
be used for redesign or retuning.
