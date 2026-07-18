# P0 Reviewer Objection Register

## Newly elevated objection

0. **The gap ignores decentralized edge-LDP graph learning.**
   Solitude already provides formal edge-LDP collection for decentralized
   user-held adjacency lists. PDGL additionally provides pure edge-LDP
   collection, add/remove-edge DP model training, secure feature/label
   handling, and secure node-classification inference using three
   non-colluding servers. LGA-PGNN studies LDP learning and link-stealing
   attacks on decentralized local graphs. FedGNNLDP, PrivFGL, CA-LDP, and
   PPGNN further crowd the space. The required response is not "we also
   distribute a graph." It is an
   ordinary add/remove-edge guarantee for the complete federated transcript,
   an inference-closed LP output, explicit cross-client candidates, and
   matched utility beyond public inputs. No "first" statement is admissible
   despite PDGL's node-classification rather than LP task.

## Novelty

1. **FKGE already performs differentially private federated link prediction.**
   Response requirement: distinguish KG embedding-record privacy from ordinary
   graph add/remove-edge privacy and compare the released outputs directly.
2. **ICDE 2024 DPLP already solves edge-private link prediction.**
   Response requirement: show why federated ownership and cross-client outputs
   alter sensitivity, transcript visibility, or deployability.
3. **GAP already provides edge-DP training and inference.**
   Response requirement: demonstrate a federated LP-specific mechanism or
   theorem not obtained by mechanically applying GAP.
4. **FedGNNLDP and CE-FedGNN already provide formal private FGL.**
   Response requirement: compare adjacency units, adversaries, output objects,
   tasks, and cross-client edge handling without dismissive wording.
5. **PDGL already protects decentralized edges and closes node inference.**
   Response requirement: do not claim decentralized edge privacy as novelty.
   Establish why candidate-pair scoring, cross-client LP, federated transcript
   visibility, and a private score service create a distinct mechanism problem.

## Privacy correctness

6. What changes when one edge is removed, including negatives, batches,
   normalization, scheduling, and client ownership?
7. Does the server see each client update or only a secure aggregate?
8. Which exact objects are DP, and does prediction reread the private graph?
9. Is the accountant valid for adaptive composition and the implemented
   sampling scheme?
10. Are node identities and attributes genuinely public? If not, why is
   edge-level DP adequate?
11. Does an unrestricted score API permit averaging or reconstruction attacks?

## Utility and causality

12. Does improvement come from private edges or from public features, labels,
    architecture, negative sampling, or test leakage?
13. Can the non-private version beat the strongest public-only comparator?
14. Is the DP noise norm commensurate with the private release dimension?
15. Are intra- and cross-client results both meaningful and adequately sized?
16. Are all baselines run under the same splits, privacy outputs, accountant,
    tuning budget, and test-access policy?

## Statistical and systems evidence

17. Are seeds paired, confidence intervals valid, and practical-effect gates
    frozen before access?
18. Is secure aggregation implemented, simulated, or merely assumed?
19. Are communication, memory, and privacy costs reported for the same output?
20. Can every table cell be traced to a source hash, config hash, commit, and
    machine-readable result?
21. Was the sealed test accessed only after the final freeze?

An unanswered objection blocks the corresponding headline claim.
