# P2.2 Confirmatory Protocol

This protocol is frozen before acquiring either source. It follows the
validation-only P2.2 advance recorded in `docs/P2_2_CONDITIONED_DEVELOPMENT_REPORT.md`.
BlogCatalog, Facebook-MUSAE, PolBlogs, and LastFM are development domains and
cannot provide confirmatory evidence for this candidate.

## Untouched sources

1. `github-social-snap`: the SNAP-hosted MUSAE GitHub network, expected to have
   37,700 nodes and 289,003 undirected mutual-follower edges. Public node
   descriptors encode profile/repository attributes.
2. `deezer-europe-snap`: the SNAP-hosted FEATHER Deezer Europe network,
   expected to have 28,281 nodes and 92,752 undirected mutual-follower edges.
   Public node descriptors encode liked artists.

Exact URLs and expected statistics are frozen in
`data/p2_2_source_registry.json`. Raw archives remain local and are never
redistributed. Source hashes, archive members, parser counts, duplicate and
self-loop handling, descriptor dimensions, and node coverage must be audited
before split creation.

## Fixed candidate

The candidate is exactly `conditioned_b8_lambda_0.1`: 16 public cells, eight
fixed public cosine bins, a 1,088-coordinate sensitivity-one edge-count query,
clipped log enrichment, and residual weight 0.1. Public pair capacities use the
same deterministic one-million-pair maximum sample fixed in P2.2 development.
No bin, cell, smoothing, clipping, score, or weight may change after source
acquisition.

The primary adversary sees every client message. Each client therefore applies
the sensitivity-one Gaussian mechanism calibrated by the complete fixed-query
RDP accountant to `(epsilon,delta)=(4,10^-6)`. Ideal secure aggregation is not a
substitute for this primary gate.

## Split and access discipline

Five new edge-independent home/split seeds are fixed in the machine-readable
config. Positive and negative candidate pairs are stratified into intra- and
cross-client subsets. Test payloads must be encrypted immediately during split
preparation. Validation may establish only parser and operational correctness;
it cannot tune or reject candidate parameters. Test decrypt is a single batched
event after code, source audit, split manifest, and test runner are committed.

## One-time GO/NO-GO rule

For **both datasets** and **both Global and Cross AUC**, all of the following
must hold over five paired seeds:

1. mean candidate gain over public cosine is at least `+0.02` AUC;
2. the paired 95% confidence-interval lower bound is greater than zero;
3. the candidate beats random score and a matched zero-private-signal release;
4. every record reports the source/config/split/commit hashes, complete RDP
   curve, sensitivity, dimension, client partition, and test access event.

All four dataset-metric cells must pass. Any missing/failed cell is `NO_GO`.
Failure rejects this mechanism without changing the threshold, retuning on the
test, or accessing the test again.
