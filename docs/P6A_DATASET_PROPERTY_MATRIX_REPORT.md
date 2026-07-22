# P6A Dataset Property Matrix Report

## Status

`COMPLETE_DEVELOPMENT_CHARACTERIZATION`

All 30 registered dataset-seed records were generated and independently
audited. The audit reproduced all summaries and input hashes, found no missing
or non-finite property, and confirmed that no P3 test artifact was accessed.
P6A is descriptive development evidence, not a new-method or confirmatory
result.

## Continuous property matrix

Values are five-seed means. AUCs use only the frozen P3 validation candidates;
all structural scores and topology statistics use the corresponding
training-positive graph.

| Dataset | Nodes | Public AUC | CN AUC | PA AUC | Modularity | Clustering | Degree CV | Degree Gini | Cross-edge fraction | Feature coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BlogCatalog-v3 | 10,312 | 0.551 | 0.939 | 0.951 | 0.236 | 0.312 | 2.74 | 0.71 | 0.801 | 1.000 |
| Facebook-MUSAE | 22,470 | 0.921 | 0.908 | 0.847 | 0.816 | 0.232 | 1.75 | 0.62 | 0.800 | 1.000 |
| PolBlogs-Newman | 1,490 | 0.704 | 0.918 | 0.930 | 0.429 | 0.167 | 1.63 | 0.69 | 0.795 | 1.000 |
| LastFM-Asia | 7,624 | 0.831 | 0.802 | 0.794 | 0.825 | 0.129 | 1.60 | 0.60 | 0.802 | 0.977 |
| GitHub-Social | 37,700 | 0.611 | 0.793 | 0.903 | 0.460 | 0.104 | 5.27 | 0.69 | 0.799 | 1.000 |
| Deezer-Europe | 28,281 | 0.604 | 0.686 | 0.754 | 0.704 | 0.078 | 1.23 | 0.54 | 0.801 | 0.782 |

`CN` denotes common neighbors and `PA` preferential attachment. The complete
mean and sample-standard-deviation matrix is stored in
`results/p6a_dataset_property_matrix/summary.json`.

## Domain interpretation

The matrix supports a heterogeneous, conditional view rather than a universal
edge-DP mechanism claim.

- **BlogCatalog is structure-dominant.** Public descriptors are barely above
  random ranking, whereas common-neighbor and degree-product scores are both
  above 0.93. It is the clearest domain in which a private structural channel
  has substantial potential headroom.
- **Facebook and LastFM are public-signal strong.** Their public AUCs are 0.921
  and 0.831. A DP structural release must clear a much harder incremental-
  utility threshold and should be allowed to fall back to public-only scoring.
- **GitHub is hub-dominated.** Its degree CV is 5.27 and preferential-
  attachment AUC is 0.903, well above its public AUC. A method can look strong
  by reproducing hub popularity without learning transferable pair structure.
- **PolBlogs is structurally easy but semantically special.** Both its public
  political descriptor and local topology are predictive. It is useful for
  mechanism checks but is too small and specialized to carry a general claim.
- **Deezer is a mixed, incomplete-feature domain.** Public coverage is only
  0.782 and all three validation AUCs are moderate. It is an important stress
  case for abstention or conservative channel selection.

These labels are descriptive. They are not yet a frozen decision rule.

## Federated-setting limitation

All six P3 domains use the same edge-independent, balanced five-client home
assignment. Consequently, their mean cross-client edge fractions are all near
the random-partition expectation of `1 - 1/5 = 0.8`. This is useful for
controlled method comparison, but it does not characterize natural
cross-silo heterogeneity.

A future confirmatory benchmark must therefore include at least one dataset
with a defensible natural client identity and nonzero held-out cross-client
links. A natural partition with zero cross-client edges cannot validate the
paper's cross-client link-prediction claim.

## Evidence-role lock

- The six datasets above remain development domains.
- Flickr and Reddit2 remain permanently consumed P5FC confirmatory evidence and
  cannot be reused for rule selection.
- Pokec, LiveJournal, and an independent blog/interest network remain
  unacquired candidates. Candidate status is not permission to download them.
- No fresh source may be acquired until a conditional feasibility rule,
  abstention behavior, metrics, and success gate are frozen in a new protocol.

## Authorized next step

P6A authorizes development of a conservative feasibility selector on the six
development domains. The selector should predict whether a private structural
channel provides a *material paired gain over the public baseline*, and should
abstain to public-only scoring when evidence is insufficient. Leave-one-
dataset-out evaluation and an explicit no-harm criterion are mandatory.

It does not authorize P3 test access or fresh-source confirmation.
