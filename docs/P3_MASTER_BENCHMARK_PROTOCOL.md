# P3 Master Benchmark Protocol

## Purpose

P2.2 selected a sensitivity-one public-score-conditioned edge-count release by
an untouched, one-time, two-domain confirmatory GO. P3 no longer asks whether a
candidate should be invented or selected. It asks whether the selected method
survives a broad, matched, reproducible benchmark suitable for a Transactions
submission.

The encrypted P2 and P2.2 tests are exhausted and must never be read again.
P3 uses new edge-independent homes, new split seeds, and new encrypted test
payloads generated after this protocol is committed. Reusing the same raw graph
source does not reuse a candidate pair or an old test payload.

## Six-domain social/blog benchmark

The benchmark contains BlogCatalog-v3, Facebook-MUSAE, PolBlogs, LastFM-Asia,
GitHub Social, and Deezer Europe. This spans blog hyperlinks, page networks,
music/social follow graphs, and developer networks from 1.5K to 37.7K nodes.

Public descriptors are frozen before split generation. Where a feature file is
independent of a node-classification target, that target is excluded. In
particular, Facebook `page_type`, LastFM target, GitHub `ml_target`, and Deezer
gender are not concatenated to public features. PolBlogs political leaning is
retained because it is the source's sole registered public node descriptor; its
special role must be disclosed in every table using it.

Five new seeds use balanced SHA-256 client homes and edge-stratified 70/10/20
train/validation/test splits. Test pairs are encrypted at creation. Validation
can audit code and tune only preregistered baseline grids; it cannot change the
selected P2.2 method.

## Primary method and privacy

The fixed method uses 16 public cells, eight public cosine bins, 1,088 noisy
counts, clipped log enrichment, and residual weight 0.1. Every canonical edge
enters one coordinate, so exact add/remove-edge L2 sensitivity remains one.

The primary adversary sees every client message. Each client therefore runs its
own sensitivity-one Gaussian mechanism. Since one canonical edge has one owner,
parallel composition protects the complete visible transcript. The primary
privacy grid is epsilon in `{0.5,1,2,4,8}` at `delta=10^-6`, with every noise
standard deviation derived from and recorded with the complete RDP curve.
Ideal secure aggregation is a separate adversary model and is reported only as
a secondary systems/privacy ablation.

## Matched comparisons

The minimum internal comparison set is fixed in the machine-readable config:
random and public-only scores, matched zero-private-signal, a nonprivate
conditioned reference, one-bin and four-bin sensitivity-one DP releases, the
selected eight-bin visible release, and the same eight-bin query under ideal
secure aggregation. Candidate and zero-signal controls share Gaussian draws.

Two external tracks are mandatory before test freeze: the closest admissible
formal centralized edge-DP link-prediction baseline (DPLP family) and a GAP-style
inference-closed edge-DP aggregation adaptation. A baseline is called
privacy-matched only after its adjacency, output, sensitivity, composition, and
RDP conversion are independently rederived under this paper's contract.
Nominal epsilon values with incompatible privacy scopes are reported as such,
not silently treated as matched.

## Metrics and statistical discipline

Primary metrics are Global and Cross-client ROC-AUC. Secondary metrics include
Intra-client ROC-AUC, Global/Cross average precision, paired gain over the public
baseline, communication, release size, runtime, and peak resident memory.
Five-seed paired 95% intervals are mandatory. Confirmatory primary comparisons
use Holm correction. Missing or failed cells are reported and never imputed.

## Predeclared analyses

1. privacy-utility curves over the fixed epsilon grid;
2. visible messages versus ideal secure aggregation;
3. one, four, and eight public-score bins;
4. separation from public-only and matched zero-private-signal controls;
5. Global/Intra/Cross behavior;
6. descriptor-sparsity failure boundaries, including Deezer zero vectors;
7. client-count, release-dimension, communication, runtime, and memory scaling.

P3 test access is a single batched event only after split audit, every internal
and external baseline implementation, accountants, validation selections, and
analysis code are committed. No method or threshold may change afterward.
