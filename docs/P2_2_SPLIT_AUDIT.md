# P2.2 Confirmatory Split Audit

Prepared once from code commit `686cafe`; no confirmatory metric was computed
during preparation and no test payload was decrypted.

| Dataset | Nodes | Edges | Public dim. | Train / Val / Encrypted test positives |
|---|---:|---:|---:|---:|
| GitHub Social | 37,700 | 289,003 | 4,005 | 202,301 / 28,900 / 57,802 |
| Deezer Europe | 28,281 | 92,752 | 31,241 | 64,925 / 9,275 / 18,552 |

Five new seeds were generated per dataset. Positive and negative test counts
are matched within intra-/cross-client strata. GitHub has 7,540 nodes per
client; Deezer has 5,656--5,657. All 16 public cells are nonempty and contain at
least 653 nodes. Deezer's 6,159 zero-descriptor nodes remain present and are
coarsened from the frozen public feature pipeline without private imputation.

Development files contain train and validation arrays only. The ten test
payloads are Fernet encrypted under a P2.2-only local key. The tracked manifest
contains aggregate counts, HMAC commitments, and encrypted-payload SHA-256
values but no pair identities. The non-decrypting audit reports `PASS`, ten hash
matches, `test_decrypted=false`, and zero test accesses.
