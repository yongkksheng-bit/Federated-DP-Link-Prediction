# R8 Pre-Submission Red-Team Protocol

Frozen: 2026-07-26 (Asia/Shanghai).

## Purpose

R8 attempts to falsify, not confirm, the submission claims. It adopts three
hostile reviewer roles:

1. a differential-privacy reviewer attacking adjacency, composition,
   sensitivity, and released-output closure;
2. a statistics reviewer attacking randomization, finite-population coverage,
   feasibility, and lower-bound conditions; and
3. a TIFS reviewer attacking novelty, operational relevance, and claim
   inflation.

R8 is an internal adversarial audit. It must not be represented as an external
expert review.

## Immutable evidence boundary

- R5 sealed holdout is not decrypted, regenerated, queried, or tuned against.
- R5 raw records, access log, commitments, and summary remain immutable.
- R8 may use tracked strict records, public source code, synthetic
  counterexamples, and symbolic/numerical checks.
- Any empirical result requiring new holdout access is out of scope and
  triggers `NO-GO`.

## Claims under attack

### Transcript privacy

- The database and adjacency relation must be stated before the theorem.
- Adaptive max-RDP composition must include the training release in the joint
  transcript and require uniform conditional certification privacy.
- Sequential RDP summation must not be described as repairing an unstable
  raw-graph split.
- Every inference output must be post-processing of released state and public
  inputs.

### Private certificate

- One certification-edge change may affect only one bounded utility and one
  count.
- Endpoint corruption must not inspect the private graph.
- Invalid/noisy counts and nonpositive corrected sums must force abstention.
- The theorem must distinguish pairwise utility from ROC-AUC.

### Randomization

- The target population must be fixed independently of assignment outputs.
- Public deterministic SHA-256 is not information-theoretic randomness.
- A random-oracle model and a secret-key PRF deployment are alternative
  computational contracts, not literally identical mechanisms.
- An adaptive post-salt population construction must be exhibited as a
  counterexample and excluded.

### Feasibility and lower bound

- `alpha`, `gamma`, `chi`, `n`, `epsilon`, and `delta` domains must be stated.
- The classical and privacy lower bounds must concern the same binary
  decision problem and record adjacency.
- The approximate-DP privacy term may be claimed only when its defining
  `D_star` is positive.
- Visible-message `sqrt(K)` scaling is implementation-specific.

## Executable attacks

R8 will add synthetic checks for:

1. uniform conditional subset probabilities under independent Bernoulli
   assignment;
2. failure of random-sample semantics under adaptive public-hash selection;
3. an unstable partition counterexample where one raw-edge change reassigns
   existing records;
4. exhaustive certificate-query sensitivity;
5. certificate lower-bound algebra over adversarial random grids;
6. exact RDP recomputation and summary reconstruction; and
7. lower-bound parameter-domain and `D_star` nonvacuity checks.

## Decision gates

`GO_SUBMISSION_PREPARATION` requires:

- all R7 evidence/accountant gates remain passing;
- every executable R8 attack behaves as predicted;
- every theorem states all assumptions needed by its proof;
- no broad first-of-kind or universal learner claim;
- no raw-graph, future-edge, ROC-AUC, or jointly released-grid upgrade;
- final PDF compiles and passes visual QA; and
- residual need for human external review is disclosed.

`NO_GO_THEORY` is mandatory if:

- one certification edge changes more than one utility record;
- certification or inference rereads private topology;
- the reported accountant fails;
- the finite-population result depends on unreported adaptive
  randomization; or
- the lower-bound headline remains nontrivial where its own assumptions make
  it vacuous.

## Deliverables

- `scripts/audit_r8_red_team.py`
- `tests/test_r8_red_team.py`
- `results/r8_red_team/audit.json`
- `docs/R8_THEOREM_RED_TEAM.md`
- `docs/R8_TIFS_MOCK_REVIEW.md`
- `docs/R8_EXTERNAL_REVIEW_PACKET.md`
- revised manuscript and audited PDF
- `docs/R8_CLOSEOUT.md`
