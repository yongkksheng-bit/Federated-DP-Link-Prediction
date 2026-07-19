# P2.1 Confirmatory Split Audit

Prepared after implementation commit `1d0b14a`; no confirmatory metric was
computed during preparation.

| Dataset | Nodes | Canonical edges | Public feature dimension | Train/Val/Encrypted Test positives |
|---|---:|---:|---:|---:|
| PolBlogs | 1,490 | 16,715 | 2 | 11,700 / 1,671 / 3,344 |
| LastFM-Asia | 7,624 | 27,806 | 7,860 | 19,463 / 2,779 / 5,564 |

PolBlogs has exactly 298 nodes per client. LastFM client sizes are
1,524--1,525. Both public coarsenings contain 16 nonempty cells with at least
two nodes, preserving the frozen 136-dimensional sensitivity-one release.

Five newly seeded splits were created per dataset. Positive and negative counts
are matched within public intra/cross strata. Development arrays are locally
available; test identities are Fernet-encrypted under a new P2.1-only key.
Tracked HMAC commitments and payload hashes reveal no pair identities.

The non-decrypting audit verifies all 10 development cells, disjointness,
aggregate counts, client balance, public-cell support, and encrypted payload
hashes. Status remains `encrypted_never_accessed`, access count zero.
