# P2 Split and Seal Audit

The P2 source/pilot protocol was frozen before acquisition at `990df58`; the
corrected split-preparation implementation was committed at `8b97259` before
the successful initialization.

## Frozen layout

| Dataset | Nodes per client | Owned edges per client (range) | Public cells | Release dimension |
|---|---:|---:|---:|---:|
| BlogCatalog v3 | 2,062--2,063 | 62,122--71,525 | 16, all nonempty | 136 |
| Facebook MUSAE | 4,494 | 33,517--34,770 | 16, all nonempty | 136 |

Client membership is the frozen balanced SHA-256 rank assignment and therefore
does not use an edge. Edge ownership is the home client of the lower canonical
endpoint.

## Five sealed splits

| Dataset | Train positives | Validation positives | Encrypted test positives | Encrypted test negatives |
|---|---:|---:|---:|---:|
| BlogCatalog v3 | 233,787 | 33,397 | 66,799 | 66,799 |
| Facebook MUSAE | 119,576 | 17,082 | 34,165 | 34,165 |

Counts are identical across the five frozen seeds; identities differ and are
paired across methods within a seed. Test intra/cross proportions are matched
between positives and negatives.

The tracked split manifest contains HMAC commitments, encrypted payload hashes,
and aggregate counts only. Local keys and payloads are ignored by Git. The
audit checks development-set disjointness and encrypted payload hashes without
decrypting the test files.

## Status

`test_status = encrypted_never_accessed`, `test_access_count = 0`.

No real validation or test metric has been computed. P2 next requires the
registered DP release and controls to run on development/validation only,
followed by a method/config freeze before the one-time batched test command.
