# R1 Cross-Domain Selector Non-Identifiability

## Setting

Let `T` be any statistic available before observing target-domain certification
records. It may include the public node descriptors, training graph, a DP
training transcript, privacy budget, release-energy diagnostics, and any
finite graph-property vector such as P6A.

A cross-domain selector `A(T)` chooses either the DP structural branch or the
public branch. It does not observe target-domain private utility records.

The target family is unrestricted unless a relation between training-domain
statistics and future link-ranking labels is explicitly assumed.

## Theorem 3: no universal nontrivial no-harm selector

For any selector based only on `T`, there exist two target-domain link
distributions `P_+` and `P_-` such that:

1. the distribution of `T` is identical under both worlds;
2. the structural branch has utility advantage `+a` under `P_+`;
3. the structural branch has utility advantage `-a` under `P_-`,

for some `a>0`.

Consequently, no `T`-measurable selector can both:

- guarantee nonnegative utility relative to public-only on every distribution
  in the unrestricted family; and
- activate with positive probability in every distribution where the
  structural branch has positive utility.

### Construction and proof

Fix the same public universe, descriptors, training graph, privacy mechanism,
and realized statistic `T=t` in both worlds. Consider two nonempty sets of
future edge/comparison records, `A_+` and `A_-`, that are not inputs to `T`.
Choose the fixed score functions so that the bounded advantage is `+a` on
records in `A_+` and `-a` on records in `A_-`.

World `P_+` places its target mass on `A_+`; world `P_-` places the same amount
of mass on `A_-`. All training-only objects and therefore `T` are identical,
while expected target advantages have opposite signs.

Let a randomized selector activate with probability `p(t)`. Its expected gain
relative to public-only is `p(t)*a` in `P_+` and `-p(t)*a` in `P_-`. No-harm in
`P_-` forces `p(t)=0`, which forfeits every positive gain in `P_+`. Requiring a
positive activation probability in `P_+` necessarily produces negative
expected gain in `P_-`.

## Minimax regret corollary

If the action is scored against an oracle that activates in `P_+` and falls
back in `P_-`, then a selector with activation probability `p` has regret

- `(1-p)*a` in `P_+`; and
- `p*a` in `P_-`.

Its worst-case regret is at least `a/2`, achieved at `p=1/2`. Deterministic
selectors have worst-case regret `a`.

## Interpretation

The theorem is an indistinguishable-worlds result, not a claim that useful
cross-domain prediction is impossible under all assumptions. It says that a
finite training-only descriptor cannot provide a universal no-harm guarantee
over an unrestricted target family.

A positive cross-domain theorem must add a transport assumption, such as
bounded covariate shift, invariant conditional utility, or a verified support
condition. P6B did not possess such a guarantee, and its Deezer failure is
consistent with unsupported extrapolation.

Target-domain private certification escapes the construction because its
input distribution differs between `P_+` and `P_-`. It obtains information
about the quantity whose sign determines the branch decision, while preserving
edge privacy through the certification mechanism.

## Claim boundary

The theorem does not prove that P6A properties are useless on average, nor that
every learned selector fails empirically. It rules out a distribution-free,
nontrivial no-harm guarantee from training-only statistics.
