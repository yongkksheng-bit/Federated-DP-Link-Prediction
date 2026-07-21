# P4R RAP Fixed Real-Graph Stress Protocol

RAP enters this stage only because its fresh-seed synthetic confirmation passed
all frozen gates. The real-graph configuration is copied verbatim:
`gamma=0.5`, profile weight `2.0`, and prior strength `1.0`. There is no search,
selection, or dataset-specific RAP tuning. Each dataset retains its already
frozen strongest GAP semantic dimension and hop count.

The first query jointly releases semantic aggregation and node-level reciprocal
profiles with exact sensitivity `sqrt(2)`. A two-hop backbone receives one
additional semantic aggregation query, exactly matching GAP's release count.
RDP calibration uses the matched hop count and the primary visible-message
adversary. Inference uses public inputs and cached DP releases only.

This stage reuses legacy P3 development/validation splits and is therefore a
stress test, not fresh confirmation. Five paired seeds compare RAP with the
frozen GAP records at epsilon 4. The unchanged gates require three significant
Global and Cross wins, macro gains of at least +0.02, and no dataset mean loss
worse than -0.01. P3 encrypted test access is prohibited. A pass authorizes
registration of new real sources; it does not authorize the P3 test.
