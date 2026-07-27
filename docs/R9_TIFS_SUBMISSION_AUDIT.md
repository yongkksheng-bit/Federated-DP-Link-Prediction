# R9 IEEE TIFS Submission Audit

Audit date: 2026-07-27 (Asia/Shanghai).

## Official requirements checked

The audit used the IEEE Signal Processing Society Information for Authors,
the TIFS reproducibility page and deep-learning checklist, and IEEE publishing
ethics/AI policies current on the audit date.

Official sources:

- https://signalprocessingsociety.org/publications-resources/information-authors
- https://signalprocessingsociety.org/publications-resources/ieee-transactions-information-forensics-and-security/ieee-transactions
- https://signalprocessingsociety.org/sites/default/files/uploads/publications_resources/docs/Guidelines__deep_learning_submissions.pdf
- https://signalprocessingsociety.org/publications-resources/publication-guidelines/policy-on-using-large-language-models-llms
- https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/

## Passed

- Regular-paper format is IEEE double-column, 10-point journal style.
- The R10 compiled manuscript has 10 pages, below the 13-page initial-submission
  ceiling.
- The self-contained abstract has 239 words, within the required 150--250
  range.
- Method, privacy unit, output contract, split policy, hyperparameter freeze,
  five-seed evaluation, implementation path, and statistical claim boundaries
  are stated.
- Code, configurations, source registries, accountants, immutable results,
  and rebuild scripts have a public repository URL.
- Raw third-party graph data and sealed test identities are not redistributed.
- The manuscript explains why no new human/animal data or IRB process was
  involved and does not describe public social-network fields as inherently
  harmless.
- AI-assisted code, visualization, language editing, and adversarial review
  are disclosed in the acknowledgment.
- The current draft has no undefined references, overfull boxes, clipping,
  overlap, or blank pages.

## Hard gates requiring author input

These cannot be truthfully completed by an automated agent:

- [ ] Replace `Anonymous Authors` with the complete author list, affiliations,
  emails, and corresponding-author designation. All entries must match the
  Author Portal.
- [ ] Confirm every author has an ORCID and approves the final manuscript,
  author order, artifact release, and AI-use disclosure.
- [ ] Add actual funding/conflict-of-interest information, or explicitly
  confirm there is none.
- [ ] State whether the manuscript or a materially related version has ever
  been rejected or submitted elsewhere; upload the required reports and
  response if it is a resubmission.
- [ ] Obtain the independent privacy/statistics review required by
  `docs/R8_EXTERNAL_REVIEW_PACKET.md`.
- [ ] Have every author manually verify all AI-assisted prose, citations,
  proofs, code, and figures. Executable tests do not replace author review.
- [ ] Confirm that local scholarly use of every third-party dataset complies
  with its source terms. The repository correctly avoids redistributing raw
  bytes, but dataset-specific redistribution licenses remain ambiguous. Use
  `docs/R10_DATA_RIGHTS_AUDIT.md` for the per-source decision and sign-off.
- [ ] Select the final TIFS EDICS classifications in the Author Portal.

Ready-to-fill author and portal materials are under `submission/`. The
recommended primary classification is Anonymization and Data Privacy
(`ADP`/historically `IFS-ADP`); the corresponding author must confirm the
label exposed by the live portal.

## Recommended portal package

1. publication-ready main PDF;
2. source archive and figure files if requested;
3. artifact README with the public GitHub URL;
4. any non-public cited manuscripts required for review;
5. prior-review disclosure/response, if applicable; and
6. external theorem-review memorandum as internal submission evidence (not
   represented as peer review).

## Decision

`TECHNICAL_PACKAGE_READY__AUTHOR_AND_EXTERNAL_REVIEW_GATES_OPEN`

The manuscript is not yet eligible for a truthful final submission while any
hard gate above remains unchecked.
