# R10 Dataset Use and Redistribution Audit

Audit date: 2026-07-28 (Asia/Shanghai).

This is a research-governance audit, not legal advice. Source availability,
an associated code license, and permission to cite a dataset are not treated
as equivalent to permission to redistribute the dataset.

## Dataset decisions

| Dataset | Authoritative source evidence | Local scholarly use | Redistribution decision |
|---|---|---|---|
| BlogCatalog v3 | Syracuse Data Lab landing page provides the download, statistics, and a required repository acknowledgment, but displays no dataset-specific license | Author confirmation required before submission | Do not redistribute raw or processed record-level bytes |
| Facebook-MUSAE | SNAP documents the dataset and citation; the pinned MUSAE repository supplies the historical files. The repository GPL license is a code license, not established here as a dataset license | Author confirmation required | Do not redistribute raw or processed record-level bytes |
| Political Blogs | Mark Newman's source page states that network data on the page are freely available for scientific use and requests citation | Permitted for the registered scientific study, subject to source citation | Continue not redistributing raw bytes |
| LastFM Asia | SNAP provides the download, task description, statistics, and source citation but no dataset-specific license on the landing page | Author confirmation required | Do not redistribute raw or processed record-level bytes |
| GitHub Social | SNAP provides the download, task description, statistics, and source citation but no dataset-specific license on the landing page | Author confirmation required | Do not redistribute raw or processed record-level bytes |
| Deezer Europe | SNAP provides the download, task description, statistics, and source citation but no dataset-specific license on the landing page | Author confirmation required | Do not redistribute raw or processed record-level bytes |

## Important license boundary

The SNAP BSD page licenses SNAP software. It is not used as evidence that
every third-party dataset in the SNAP collection is BSD-licensed. Likewise,
the MUSAE repository's GPL-3.0 code license is not represented as a license
for the Facebook records.

## Repository compliance

- Raw archives, edges, node identifiers, and record-level processed datasets
  remain untracked and local.
- The public artifact contains source URLs, immutable checksums, aggregate
  statistics, split audits, configurations, and code.
- Dataset citations and source acknowledgments remain mandatory.
- A future data-release package must use downloader scripts or source
  instructions instead of bundling third-party bytes unless explicit written
  permission or dataset-specific redistribution terms are obtained.

## Author sign-off

- [ ] Corresponding author reviewed every current source page.
- [ ] Corresponding author confirmed the intended local scholarly use is
  consistent with applicable source terms and institutional requirements.
- [ ] Authors confirmed that no raw or record-level third-party data are
  included in the Git repository, manuscript source archive, or supplement.
- [ ] Authors confirmed all requested dataset citations and acknowledgments.

## Source pages

- https://blogcatalog3.datasets.syr.edu/
- https://public.websites.umich.edu/~mejn/netdata/
- https://snap.stanford.edu/data/facebook-large-page-page-network.html
- https://snap.stanford.edu/data/feather-lastfm-social.html
- https://snap.stanford.edu/data/github-social.html
- https://snap.stanford.edu/data/feather-deezer-social.html
- https://snap.stanford.edu/snap/license.html
