# P2.2 One-Time Confirmatory Test Freeze

The one-time runner is frozen at commit
`a4116521205b2a708e0b12fcf4545540647c07a9`. It must execute from a clean
worktree after this freeze document is committed. Before decrypting any payload
it writes `results/p2_2_confirmatory_test/access.json` with status `started`;
the existence of that directory or record permanently forbids a second run.

## Frozen inputs

| Object | SHA-256 |
|---|---|
| Confirmatory config | `b49942bf22aa87ed7954e2b5654cf622b1d5a4ad6eb39243fdf1cfbed141ece1` |
| Source audit | `5ccf13ec1298871808d0a771c9d458ec3c5ff9c48f45b20f96c1299d2bf2b0e0` |
| Split manifest | `3ac722b80644adbc9ddf22da1b2ecc7f99c57a79309eb547e81daba0d44f973c` |
| Non-decrypting split audit | `8c05221da90e76fcb31475c800c036ec4885d9c09ff3f2c3862c54897f516381` |

The encrypted payload hashes and HMAC commitments are inside the frozen split
manifest. The runner verifies both after the access event starts.

## Frozen method and controls

- Candidate: public cosine plus `conditioned_b8_lambda_0.1`.
- Query: one 1,088-coordinate public-cell-pair by public-cosine-bin count
  vector, exact add/remove-edge L2 sensitivity one.
- Privacy: `(epsilon,delta)=(4,10^-6)` from the full fixed-query Gaussian RDP
  curve; every client message is individually visible.
- Controls: public cosine, random score, and zero-private-signal with the exact
  same Gaussian noise realization as the candidate.
- Seeds: `12011, 13007, 14009, 15013, 16001` on both registered datasets.

## Frozen decision

For GitHub Global, GitHub Cross, Deezer Global, and Deezer Cross, GO requires:

1. five complete paired records;
2. mean candidate gain over public cosine at least `+0.02` AUC;
3. paired 95% CI lower bound over public cosine above zero;
4. paired 95% CI lower bounds over matched zero-private-signal and random score
   above zero;
5. dimension, sensitivity, RDP curve, client partition, hashes, and access
   provenance present and consistent.

Every condition in all four cells must pass. Otherwise the decision is NO-GO,
the candidate is rejected, and neither the test nor its threshold may be reused.
