# P5FC Fresh-Source Frontier Confirmation

Frozen before source acquisition on 2026-07-22 (Asia/Shanghai).

## Question

Does the P5F first-hop signal/noise energy index retain a strong monotone
association with link-prediction gain over public-only inference on graph
sources that played no role in constructing the index or selecting prior
backbones?

## New sources

The confirmatory sources are GraphSAINT Flickr, an online photo-sharing graph,
and GraphSAINT Reddit2, an online discussion graph. Only `adj_full.npz` and
`feats.npy` are allowlisted. Node-classification labels and upstream node-split
roles are prohibited and will not be downloaded. Their omission prevents both
task-label leakage and reuse of a split designed for a different task.

The GraphSAINT repository distributes its code under MIT, but that repository
license is not treated as proof of dataset-specific redistribution rights.
Raw and processed graph data therefore remain local and ignored by Git. Only
URLs, source IDs, hashes, byte counts, and aggregate integrity statistics may
be committed.

## Frozen method

Both datasets use the same graph-independent public encoder (`d=32`), one-hop
GAP-style sensitivity-`sqrt(2)` aggregation, RDP accountant, five-client
balanced hash assignment, candidate construction, and cosine decoder. There is
no dataset-specific hyperparameter selection. Labels and source roles never
enter the encoder, split, decoder, or analysis.

Canonical undirected edges are formed by removing self-loops, symmetrizing, and
deduplicating the source adjacency. Per seed, deterministic keyed SplitMix64
hash
ranks reserve at most 50,000 validation positives and 100,000 test positives,
balanced as closely as possible between intra- and cross-client strata. All
other positive edges are training edges. Equal-count nonedges are sampled
within the same strata. Validation is limited to parser and audit sanity; the
confirmatory gate is evaluated once on the frozen test runner.

## Confirmatory analysis

The design contains 100 run records and 20 dataset/epsilon/visibility cells.
The primary statistic is Spearman correlation between cell-mean
`log10(F_signal)` and cell-mean Global-AUC gain over public cosine. Passing
requires pooled rho at least 0.6, rho at least 0.6 within each dataset, and an
exact permutation p-value at most 0.05 within each dataset. It also requires
the exact factor-five expected noise-energy separation, complete RDP curves,
finite records, and no missing cells.

Failure rejects the general frontier claim. It may not be repaired by tuning,
replacing a source, changing a threshold, or reopening the same test payload.
Passing supports only a release-level feasibility diagnostic; it does not make
the index a universal AUC threshold or a theorem about downstream utility.
