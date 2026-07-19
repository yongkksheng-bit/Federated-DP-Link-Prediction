# P2 Source and Rights Registry

Frozen before source acquisition: 2026-07-19 (Asia/Shanghai).

## Selected pilot domains

P2 uses one blog network and one social network:

| ID | Canonical source | Claimed source statistics | Pilot role |
|---|---|---:|---|
| `blogcatalog-v3` | Syracuse University Data Lab | 10,312 nodes; 333,983 undirected edges; 39 groups | blog |
| `facebook-musae` | SNAP metadata plus MUSAE commit `5f90123` | 22,470 nodes; 171,002 raw edge rows; four categories | social |

`blogcatalog-v3` is the original 10,312-node source. It is not the PyG
`AttributedGraphDataset` derivative with 5,196 nodes, 8,189 features, and six
classes. Those two artifacts must never share a dataset label in results.

## Rights boundary

Neither landing page provides an unambiguous dataset-specific redistribution
license. MUSAE's GPL-3.0 repository license applies clearly to repository code
but is not treated here as proof that the graph data itself is GPL-licensed.
Therefore:

- local scholarly evaluation may proceed only under applicable source terms;
- raw, processed, or reconstructable data may not be committed or redistributed;
- manifests may contain URLs, byte counts, hashes, and aggregate statistics but
  no edges, names, features, or test identities; and
- explicit dataset terms or written clarification remains a P2 closeout item.

## Field classification

The benchmark fixes node IDs and listed node descriptors as public under edge
adjacency. Blog group memberships and Facebook description/category fields are
therefore public benchmark inputs. This is a modeling assumption, not a claim
that those fields are harmless in every real deployment.

All edges, degrees, neighborhoods, edge-derived partitions, and graph
normalizers are private. Page names from the Facebook target file are neither
needed nor admitted into tracked artifacts.

## Immutable acquisition

`data/source_registry.json` is the machine-readable URL allowlist. Facebook
files are pinned to an immutable Git commit and expected Git blob IDs. The
BlogCatalog server exposes a versioned upload URL but no content hash; its first
acquisition SHA-256 becomes the project-local immutable identity and any later
byte change must fail closed.

## First-source audit

The post-freeze audit found that BlogCatalog matches all advertised counts:
10,312 nodes, 333,983 unique simple undirected edges, and 39 groups. The MUSAE
Facebook edge CSV contains exactly the 171,002 rows shown by SNAP, but 179 are
self-loops. Removing those loops yields 170,823 canonical simple undirected
edges; there are no duplicate or reversed duplicate rows. The graph has 22,470
feature-complete nodes, 4,714 feature dimensions, and four page categories.

Accordingly, `171,002` is retained as a raw source-row statistic and `170,823`
is the link-prediction graph statistic. This is a documented normalization, not
a silent disagreement with the source.
