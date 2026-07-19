# P2 Source Integrity Audit

Audited after protocol commit `990df5845163e82cfc99fd3853819fa3f1a5f08e`.

## Immutable source identities

| Dataset artifact | Bytes | SHA-256 |
|---|---:|---|
| BlogCatalog v3 ZIP | 976,987 | `173c519328c29f5f37f78d6efeebfd30c5f8d33e121d20b314d81b04fb1b2815` |
| Facebook edges | 1,882,610 | `7c50d8f02a75cc0829577814a1fc14535164daa38d79c3612340c9e9cdbd4022` |
| Facebook features | 2,088,766 | `ea870537646a93642a0008d38aa9bfeff02018070ba97b1f3f469d9622626436` |
| Facebook targets | 1,177,912 | `7bd96eafea3c2ca40f44bfa9e73642194696c21e38c7b29ed409c32ad14075cd` |

## Aggregate integrity findings

| Check | BlogCatalog v3 | Facebook MUSAE |
|---|---:|---:|
| Nodes | 10,312 | 22,470 |
| Raw edge rows | 333,983 | 171,002 |
| Self-loops removed | 0 | 179 |
| Duplicate/reversed rows | 0 | 0 |
| Canonical simple undirected edges | 333,983 | 170,823 |
| Public descriptor dimension | 39 group memberships | 4,714 sparse features + 4 categories |
| Missing descriptor nodes | 0 | 0 |
| Endpoints outside node dictionary | 0 | 0 |

The machine-readable evidence is in
`data/manifests/p2_source_audit.json`. It contains aggregate counts only.

## Status

**Integrity PASS; rights clarification still open.** The bytes and graph schema
are suitable for local P2 preparation. They are not authorized for repository
redistribution, and no pilot result exists yet.
