# Data Boundary

Raw and processed graph data are local-only and ignored by Git. This repository
tracks only source metadata, immutable checksums, and split/release audit
records that contain no edge lists, node names, features, or test identities.

P2 source acquisition is permitted only after the source and pilot protocol is
committed. Acquisition does not authorize redistribution. A dataset-specific
license or written permission remains preferable; absent that, artifacts are
restricted to local scholarly evaluation and must not be uploaded.

Expected local layout:

```text
data/raw/                 # downloaded source files; never tracked
data/processed/           # parsed arrays and private edge sets; never tracked
data/sealed/              # encrypted test payloads and local keys; never tracked
data/manifests/           # non-sensitive checksums and audit metadata
```

`data/source_registry.json` is the allowlist consumed by the acquisition
script. A manifest proves which bytes were used; it does not grant rights to
those bytes.
