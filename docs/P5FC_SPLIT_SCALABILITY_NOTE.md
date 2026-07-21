# P5FC Split Scalability Note

Before any source matrix was parsed, split generated, or result observed, the
registered edge-ranking implementation was changed from per-edge SHA-256 rank
to vectorized keyed SplitMix64 rank. Reddit2 has approximately 11.6 million
canonical undirected edges; the original implementation choice would add
substantial Python-object and sorting overhead without changing the scientific
role of the rank.

The revised algorithm remains deterministic, seed-keyed, edge-order
independent, stratified, and without replacement. Dataset choice, source IDs,
positive caps, negative ratio, seeds, privacy budgets, method, and all
confirmatory gates are unchanged. This revision precedes source-integrity
parsing and receives its own Git timestamp before split generation.
