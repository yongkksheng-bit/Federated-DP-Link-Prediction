# P3 Six-Domain Benchmark Split Audit

P3 split preparation executed once from commit `e63ae88` after the master
protocol and six-domain source contract were committed. No P2/P2.2 sealed test
was read. No P3 test was decrypted.

| Dataset | Nodes | Edges | Public dim. | Train / Val / Encrypted test positives |
|---|---:|---:|---:|---:|
| BlogCatalog-v3 | 10,312 | 333,983 | 39 | 233,787 / 33,397 / 66,799 |
| Facebook-MUSAE | 22,470 | 170,823 | 4,714 | 119,575 / 17,081 / 34,167 |
| PolBlogs | 1,490 | 16,715 | 2 | 11,700 / 1,671 / 3,344 |
| LastFM-Asia | 7,624 | 27,806 | 7,842 | 19,463 / 2,780 / 5,563 |
| GitHub Social | 37,700 | 289,003 | 4,005 | 202,301 / 28,899 / 57,803 |
| Deezer Europe | 28,281 | 92,752 | 31,241 | 64,925 / 9,274 / 18,553 |

Each row is repeated for five frozen seeds. Test positives and negatives are
count-matched within intra-/cross-client strata and encrypted immediately with
a P3-only key. Tracked artifacts contain aggregate counts, HMAC commitments,
and encrypted-payload hashes, never pair identities.

The non-decrypting audit verifies all 30 development files, client balance,
16-cell support, train/validation disjointness, positive/negative disjointness,
and every sealed payload hash. It reports zero failures, status `PASS`,
`test_decrypted=false`, and test access count zero.
