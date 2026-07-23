# R7 Closeout

Closed: 2026-07-24 (Asia/Shanghai).

## Status

`R7_INDEPENDENT_AUDIT_COMPLETE`

## Passed gates

- Clean GitHub clone of technical commit
  `fbe71506e29884c73c894b14ca14fef67ef3d785`.
- 101/101 software tests passed.
- 1500/1500 frozen R5 records independently reconstructed.
- Every composed RDP curve and epsilon reproduced to `1e-12`.
- Certification sensitivity independently enumerated as `sqrt(2)`.
- Endpoint corruption confirmed graph-independent.
- R5 primary summary, 50 diagnostic cells, gates, and decision reproduced
  without differences.
- Three publication figures rebuild byte-for-byte.
- Nine-page IEEE manuscript compiles with no undefined references, overfull
  boxes, clipping, overlap, or blank-page defect.
- Clean-built manuscript is byte-identical to the tracked audited PDF:
  SHA-256
  `93235995768b4f1507a012f73418007c39477399419db04999fd46553ae2b237`.
- Final clean build leaves no tracked working-tree changes.
- Sealed P3/R5 holdout was not decrypted, regenerated, or revisited.

## Claim corrections

1. The privacy guarantee is explicitly for the registered role-labelled edge
   database; sequential RDP summation does not upgrade it to raw
   pre-partition graph adjacency.
2. The finite-population sampling theorem explicitly uses a
   random-oracle/PRF-style interpretation of the edge-keyed SHA-256 map.
3. Production deployment should use a committed secret PRF key or auditable
   random draw after population freeze when providers could adapt to a public
   salt.
4. FedHGPP is now cited as a 2026 federated edge-private recommendation
   predecessor. The novelty is private target-domain deployment
   certification and fallback, not federated private LP itself.

## Delivered

- `scripts/audit_r7_theory_contract.py`
- `scripts/reproduce_r7_artifact.py`
- `results/r7_independent_audit/theory_contract.json`
- `results/r7_independent_audit/reproduction.json`
- `docs/R7_THEOREM_AUDIT.md`
- `docs/R7_REPRODUCIBILITY_REPORT.md`
- `docs/R7_LITERATURE_REFRESH.md`
- `output/pdf/certfed_lp_r7_audited.pdf`

## Residual pre-submission work

R7 is an internal independent artifact audit, not external peer review.
Before submission:

1. obtain an external privacy/statistics re-derivation of Theorems 2--4;
2. repeat the literature search on the actual submission date;
3. apply venue-specific anonymization, ethics/data-availability statements,
   and artifact URL; and
4. do not alter the R5 claim or access the sealed holdout without a new
   preregistered protocol.

These are submission-governance tasks. No failed technical R7 gate remains.
