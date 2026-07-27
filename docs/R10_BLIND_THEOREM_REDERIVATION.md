# R10 Blind Theorem Re-Derivation

Audit date: 2026-07-28 (Asia/Shanghai).

Status: `INTERNAL_AI_ASSISTED_PASS_AFTER_EXPLICIT_CONDITION`

This review was performed from the manuscript statements, appendix proofs,
accountant implementation, and frozen protocol artifacts without using the
conclusions of the R7 or R8 theorem reports. It is an internal adversarial
check, not the independent human expert sign-off required before submission.

## Theorem 2: role-wise transcript privacy

For a role-labelled neighboring database, exactly one of the training,
certification, or research-evaluation roles can contain the changed canonical
edge.

- A training-role change is governed by the training RDP mechanism; appending
  conditional certification and the activation decision is post-processing.
- A certification-role change leaves the training-release distribution
  unchanged; the uniform conditional RDP bound can therefore be integrated
  over that common distribution.
- An evaluation-role change is not read by the deployed mechanism.

The resulting adaptive role-wise bound is the maximum of the training and
certification RDP curves. The reported order-wise sum is conservative on the
same role-labelled database. It does not prove raw pre-partition graph DP.
The Gaussian certification query has sensitivity at most `sqrt(2)` because
one add/remove edge changes the bounded sum and count by at most one each.

Verdict: valid under the stated role-labelled adjacency and uniform
conditional-RDP assumptions.

## Theorem 3: finite-holdout no-harm

For values in `[-1,1]`, the one-sided sampling-without-replacement bound

`Pr(sample_mean - population_mean >= t) <= exp(-n t^2 / (2 f_N))`

has the correct range-two constant. Replacing `f_N` by one is conservative.
On the two Gaussian good events, `S_L <= S`, `n_L <= n_C <= n_U`, and a
positive corrected numerator gives `S_L / n_U <= S / n_C`. The union bound
therefore yields the stated three-part failure allocation.

The original prose left one conditioning requirement implicit: given the
frozen finite population `H`, its certification-assignment bits must be
independent of the training release `R`. The manuscript now states this
assumption explicitly and conditions the displayed probability on `n_C`.
Uniformity in valid `n_C` permits averaging back to a statement conditional
on `(R,H)`. Invalid counts cause abstention.

Verdict: valid after the explicit conditional-independence clarification.
The guarantee remains finite-population and protocol-specific. Public,
deterministic SHA-256 is not claimed to provide information-theoretic
randomness; the standard-model deployment uses a secret-key PRF and adds its
distinguishing advantage.

## Theorem 4: necessary count

For `n/chi` independent Bernoulli blocks replicated `chi` times, Le Cam plus
Pinsker gives the classical term of order `chi / alpha^2`. The
add/remove-to-replacement conversion uses
`epsilon_r = 2 epsilon` and
`delta_r = (1 + exp(epsilon)) delta`. Under maximal coupling, the expected
replacement Hamming distance is `n alpha / 2`; substituting it into the cited
private Le Cam inequality yields the exact `2 D_star / alpha` term.

For pure DP, solving the defining inequality produces order
`1 / (epsilon alpha)`. For approximate DP, the term can become weak when
delta dominates. The manuscript correctly limits the near-matching claim to
pure DP and sufficiently small delta, and does not claim an AUC lower bound or
Gaussian minimax optimality.

Verdict: the principal-rate statement is defensible with the manuscript's
current restrictions. External review should independently verify the exact
constants and the applicability conditions of the cited private Le Cam
result.

## Remaining human gate

An independent privacy/statistics expert who did not author the code or prose
must complete `docs/R9_EXTERNAL_EXPERT_SIGNOFF.md`. This internal report cannot
be represented as peer review, external validation, or expert endorsement.
