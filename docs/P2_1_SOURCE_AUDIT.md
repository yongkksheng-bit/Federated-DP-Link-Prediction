# P2.1 Confirmatory Source Audit

Audited after confirmatory protocol commit `178d52b` and before split creation.

## Immutable source bytes

| Source | Bytes | SHA-256 |
|---|---:|---|
| PolBlogs ZIP | 94,090 | `e047df21736fef9037f0450f7d3756ecb16a8e347417723181c0f7e493021ddb` |
| LastFM-Asia ZIP | 6,527,202 | `51acb78a923bb223ed6e61be88f91122fb29adca3f07beff7289cafd98601d47` |

## Canonicalization audit

PolBlogs contains 1,490 nodes and 19,090 raw GML edge blocks. Sixty-five edge
blocks duplicate an existing direction, leaving the advertised 19,025 unique
directed links. Three are self-loops. Collapsing direction and reciprocal links
under the frozen transformation yields 16,715 canonical simple undirected
edges. Public leanings contain 758 label-0 and 732 label-1 blogs.

LastFM-Asia exactly matches its source README: 7,624 feature-complete nodes and
27,806 unique simple undirected edges, with no self-loop, duplicate, reversed,
missing-feature, or out-of-dictionary record. The sparse artist feature space
has 7,842 dimensions and the public target contains 18 country classes.

## Status

**Integrity PASS.** Aggregate evidence is stored in
`data/manifests/p2_1_source_audit.json`. Raw files remain local-only. Source
integrity does not resolve the LastFM dataset-specific license ambiguity.
