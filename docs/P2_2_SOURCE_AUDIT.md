# P2.2 Confirmatory Source Audit

Audited after source-registration commit `08fa3e3` and parser commit `890e999`.
Both archives were absent locally before registration and were acquired only
after the confirmatory protocol, candidate, seeds, and test gate were frozen.

## Immutable source bytes

| Dataset | SHA-256 | Bytes |
|---|---|---:|
| GitHub Social | `56c0c1c2c460dc4c7bf89357b1fec020f45e2ecebab81d131d073b10e28ec031` | 2,396,031 |
| Deezer Europe | `dd66a73f8d8690b5bc300ba378883fb2c2f6316aec8917b6a2428e352fc9e498` | 2,622,306 |

## Parser audit

| Dataset | Nodes | Canonical undirected edges | Public feature dimension | Public feature nnz |
|---|---:|---:|---:|---:|
| GitHub Social | 37,700 | 289,003 | 4,005 | 690,358 |
| Deezer Europe | 28,281 | 92,752 | 31,241 | 958,475 |

Both node and edge counts exactly match the registered SNAP statistics. Neither
archive contains a self-loop or duplicate canonical edge. Feature and target
files cover identical node universes, but target labels are not included in the
public descriptors.

GitHub contains 690,374 raw feature entries, including 16 repeated node-feature
indices; sparse canonicalization correctly yields 690,358 unique nonzeros.
Deezer contains 6,159 nodes with empty public feature lists. These nodes remain
zero vectors. We do not impute them with private degree/neighborhood data or
with the node-classification target.

The machine-readable aggregate audit is
`data/manifests/p2_2_source_audit.json`. Raw archives remain local-only; source
availability is not treated as permission to redistribute dataset bytes.
