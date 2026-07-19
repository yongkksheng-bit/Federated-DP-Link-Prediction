# P2.1 Untouched Confirmatory Protocol

Frozen before acquiring either confirmatory source.

## Fixed method

The candidate is fixed from P2.1 development:

`score(u,v) = public_cosine(u,v) + 0.05 * centered_rank(R_block[u,v])`,

where `R_block` is the same one-shot, sensitivity-one Gaussian edge-count
release and the residual lies in `[-1,1]`. The release and every deployed score
are inference-closed: after release, scoring reads only public node inputs,
public cells, and `R_block`.

No transform, residual weight, epsilon, delta, client count, split ratio, seed,
or gate may change after source acquisition.

## New domains

- `polblogs-newman`: a directed political-blog hyperlink graph transformed to
  one simple undirected edge per unordered linked pair. Political leaning is a
  fixed public two-dimensional one-hot descriptor. Each public label is divided
  into eight balanced SHA-256 subcells without reading a link.
- `lastfm-asia-snap`: an undirected mutual-follower social graph. Public artist
  features and country labels form the public descriptor; 16 cells are fit from
  those descriptors only.

These sources were not used by P1, P2, or P2.1 development. Existing P2 test
payloads remain unopened and are not admissible for this protocol.

## Confirmatory discipline

Five new seeds share methods, clients, candidates, and splits. Development code
may verify source schemas and validation execution, but it may not select a new
weight or residual. Test identities are encrypted before any metric is run.
After an implementation/hash freeze, all five test seeds are opened once in a
single append-only command.

The candidate passes only if, on both datasets and for both Global and
Cross-client AUC, its mean paired improvement over public cosine is at least
+0.02 and the paired 95% Student-t interval lies above zero. It must also beat
random and matched zero-private-signal controls. Any missing or failed cell is
NO-GO. Ceiling-normalized gains may be diagnostic but cannot replace the
absolute gate.

## Rights and reporting

Raw data remain local. Mark Newman's source describes its network collection as
free for scientific use; SNAP does not display a LastFM-specific license.
Neither source is redistributed by this repository. Aggregate checksums,
normalization counts, and audit metadata may be tracked.
