# P2.1 Confirmatory Validation Report

Decision: **ADVANCE TO TEST FREEZE.** No test payload was decrypted.

The validation gate and fixed runner were committed at `ab99598`. Ten records
cover two untouched domains and five new seeds under the same
`(epsilon,delta)=(4,10^-6)` visible-message release.

| Dataset | Metric | Candidate AUC | Public cosine | Paired gain (95% CI) |
|---|---|---:|---:|---:|
| PolBlogs | Global | 0.7450 | 0.7096 | +0.0354 [0.0272, 0.0435] |
| PolBlogs | Cross | 0.7393 | 0.7087 | +0.0306 [0.0215, 0.0396] |
| LastFM-Asia | Global | 0.8385 | 0.8343 | +0.00415 [0.00323, 0.00507] |
| LastFM-Asia | Cross | 0.8381 | 0.8342 | +0.00398 [0.00298, 0.00498] |

The fixed residual is positive in all four cells and every paired interval
excludes zero. The LastFM effect is real but smaller than the final +0.02
absolute gate; validation does not weaken that preregistered requirement.

The next commit must freeze the one-time decryption runner, result schema, and
access log. No implementation or scientific parameter may change after that
commit and before the single batched test execution.
