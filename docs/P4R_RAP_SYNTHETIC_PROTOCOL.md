# P4R RAP Synthetic Feasibility Protocol

The synthetic gate tests whether a reciprocal node-to-public-cell profile adds
information that the matched GAP cosine decoder does not use. In both domains,
each node has a public cell and a latent target-cell preference. Edge
probability increases when one endpoint matches the other's preference and
increases again when the match is mutual. Public features reveal cell identity
but not node-specific preference.

Both GAP and RAP use the same public features, train edges, clients, visible
message adversary, `epsilon=4`, `delta=1e-6`, exact RDP accountant, and
`sqrt(2)` per-release sensitivity. Their semantic Gaussian draws are coupled.
RAP jointly allocates part of the same query energy to its reciprocal profile;
it receives no additional privacy budget.

Ten seeds select one RAP configuration by worst-domain mean Global gain over
GAP. Twenty disjoint synthetic seeds form the held-out gate. Both domains must
show at least +0.02 Global and Cross AUC gain with paired 95% intervals above
zero. Failure rejects RAP before any real graph is accessed. Success authorizes
only a newly frozen real-data development protocol, not P3 validation or test.
