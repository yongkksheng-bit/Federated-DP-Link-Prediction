# R8 Theorem Red-Team Audit

Audit date: 2026-07-26 (Asia/Shanghai).

## Verdict

`PASS_AFTER_CLAIM_NARROWING`

The core certified-fallback result survives the internal adversarial audit.
Three assumptions were previously too implicit and have now been promoted
into theorem or immediately preceding setup:

1. the finite target population is fixed independently of assignment outputs;
2. the ideal Bernoulli/random-oracle analysis and a secret-key PRF deployment
   are alternative contracts, with PRF distinguishing advantage added in the
   latter; and
3. the inverse-`epsilon` lower-bound headline is pure-DP (or
   sufficiently-small-`delta`) rather than uniform over approximate DP.

## Theorem 2: role-wise transcript privacy

### Attack

Could adaptive certification leak an edge already protected by training, or
could sequential summation repair a raw-graph split that reassigns existing
records?

### Result

The max-RDP proof is valid for the registered role-labelled database:

- a training-role edge changes the distribution of `R`, while certification
  is the same Markov kernel appended to `R`;
- a certification-role edge leaves `R` identically distributed, and the
  conditional certificate mechanism is uniformly RDP for every fixed `R`;
  and
- evaluation-role edges are not read by the deployed mechanism.

The executable unstable-partition attack adds one raw edge to an index-based
split and reassigns six existing edges. It demonstrates that sequential RDP
summation cannot upgrade an unstable raw-graph transform. The manuscript now
forbids that interpretation in the abstract, problem definition, method, and
theorem discussion.

### Residual scope

The guarantee is not raw pre-partition graph DP. Whether role-labelled
adjacency is adequate is an application and venue judgment, not an
accountant error.

## Theorem 3: finite-holdout no-harm

### Sensitivity attack

The scorer is fixed by released training state; endpoint corruption has no
graph input. One certification-edge add/remove changes one bounded value in
`[-1,1]` and one count, giving exact worst-case L2 sensitivity `sqrt(2)`.

### Algebra attack

R8 searched 5000 adversarial good-event configurations over count, mean,
Gaussian standard deviation, and bounded noise deviations. There were 2560
valid-certificate cases and no lower-bound violation. The maximum signed
violation was `-4.9166e-6`.

This is corroboration of the deterministic inequalities, not a replacement
for their proof.

### Randomization attack

Independent Bernoulli assignment is uniform conditional on sample size; R8
enumerates this exactly for a finite population.

The public-hash counterexample then constructs the population after observing
the hash. All 200 selected records enter certification, so the realized rate
is `1.0` rather than `1/3`. The sampling theorem is therefore invalid for
post-salt adaptive population construction.

R5 is not this counterexample: its encrypted holdout was fixed before
assignment outputs were inspected. The paper now states this prerequisite.
For deployment it recommends either:

- ideal auditable randomness after population freeze; or
- a committed secret PRF key hidden from data providers until freeze.

The statistical theorem is exact under ideal Bernoulli assignment/ROM. A PRF
implementation adds its distinguishing advantage.

## Theorem 4: necessary count

### Classical term

For block-replicated Bernoulli hard instances with `chi | n`, product KL and
Le Cam yield the `chi/alpha^2` term under the stated parameter domain.

### Privacy term

For approximate DP the defensible statement is the exact requirement
`n >= 2 D_star / alpha`, with `D_star` defined by the manuscript equation.
R8 reproduces the pure-DP closed form exactly:

`D_star = log(0.9/(2 eta))/(20 epsilon)`.

At `epsilon=1`, `eta=0.1`, increasing `delta` from `0` to `0.4` reduces
`D_star` from `0.07520` to `0.02400`. A universal approximate-DP
`1/(epsilon alpha)` headline is therefore unsafe.

The theorem and abstract now claim matching principal rates for pure DP and
sufficiently small `delta`; general approximate DP retains the exact
`D_star` form.

## Machine-readable audit

`results/r8_red_team/audit.json` records all attacks and checks. A PASS on a
counterexample check means the invalid upgrade was successfully exhibited and
is explicitly excluded, not that the invalid protocol is safe.

## Human-review boundary

This is an internal red-team exercise conducted with the authors' repository
and assumptions. It is not independent external peer review. The external
packet identifies the remaining questions a privacy/statistics expert must
answer without relying on this audit's conclusion.
