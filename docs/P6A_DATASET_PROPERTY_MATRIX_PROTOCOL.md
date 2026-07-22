# P6A Dataset Property Matrix Protocol

## Purpose

P6A begins the pivot from a universal mechanism claim to a conditional
feasibility analysis. It measures graph-domain properties that may explain
when an edge-DP structural channel adds link-ranking utility beyond public
node descriptors. It does not select a new private mechanism and does not make
a confirmatory claim.

## Evidence roles

The six P3 domains are development evidence: BlogCatalog-v3, Facebook-MUSAE,
PolBlogs-Newman, LastFM-Asia, GitHub-Social, and Deezer-Europe. Their five
frozen seeds define 30 dataset-seed records.

Flickr and Reddit2 remain one-time P5FC confirmatory evidence. They may be
discussed as prior outcomes but may not enter P6A fitting, threshold selection,
or proxy construction. Pokec, LiveJournal, and an independent blog/interest
network are candidate future confirmation domains. They must not be acquired
until a later source protocol, decision rule, and success gate are frozen.

## Data boundary

P6A may read public node descriptors, frozen public client homes, training
positives, and validation positives/negatives. Structural properties are
computed from the training-positive graph only. Validation edges are used only
as candidate labels for public-cosine, common-neighbor, and
preferential-attachment AUCs.

P6A must not read a sealed P3 test payload, the P3 test key, or any P5FC test
record. Every output record must state `test_accessed=false` and carry hashes
of its development array, public layout, frozen configuration, and P3 split
audit.

## Property families

1. **Public signal:** public-feature validation AUC, descriptor coverage, and
   descriptor density.
2. **Local structural signal:** common-neighbor and preferential-attachment
   validation AUCs from the training graph.
3. **Topology:** density, mean degree, degree CV/Gini, largest-component
   fraction, sampled average clustering, degree assortativity, and Louvain
   modularity/community count.
4. **Federated geometry:** fraction of training edges crossing frozen client
   homes.

Continuous values are primary. Any labels such as feature-dominant,
structure-dominant, or hub-dominated are descriptive summaries and cannot be
used as a method-selection rule without a separately frozen protocol.

## Completion gate

P6A is complete only if all 30 unique dataset-seed records are finite, all six
five-seed summaries are reproduced by an independent audit, all registered
input hashes are current, and no prohibited test artifact is accessed.

Completion authorizes exploratory feasibility-boundary modeling on the six
development domains. It does not authorize acquisition of a fresh confirmation
source or access to P3 tests.
