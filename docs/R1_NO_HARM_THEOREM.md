# R1 Private Certification and No-Harm Theorem

## Target utility

Fix a realized DP training release `R`. For certification edge `e`, let

`d_R(e)=U_{s_R}(e)-U_{s_0}(e) in [-1,1]`,

where both utilities compare the edge with the protocol's public deterministic
endpoint-corrupted pair.

Let

`Delta_R = E[d_R(e) | R]`

under the registered target-domain certification distribution. Positive
`Delta_R` means that the DP structural branch improves this pairwise ranking
utility over the public branch.

This is not standard ROC-AUC unless the registered corruption distribution
matches the negative-pair distribution defining that AUC.

## Noisy sufficient statistics

For `n` certification records, define

`S=sum_i d_R(e_i)` and `hat_Delta=S/n`.

Certification releases

`S_tilde=S+Z_S` and `n_tilde=n+Z_n`.

Let public bounds `b_S,b_n` satisfy

`Pr(|Z_S|>b_S)<=beta_S`

and

`Pr(|Z_n|>b_n)<=beta_n`.

For the isotropic Gaussian mechanism with coordinate standard deviation
`tau`, one may use

`b_j = tau*Phi^{-1}(1-beta_j/2)`.

In the ideal aggregate, `tau=sqrt(2)*sigma_C`. In the visible-message sum with
equal independent client noise, `tau=sqrt(2K)*sigma_C`.

Define

`S_L=S_tilde-b_S`,

`n_L=n_tilde-b_n`, and

`n_U=n_tilde+b_n`.

The mechanism must fall back to public-only unless `S_L>0`, `n_L>=n_min>0`,
and `n_U>0`. Otherwise define the empirical lower certificate

`L_emp=S_L/n_U`.

## Statistical assumption

Conditional on `R`, assume the registered certification sampling process
satisfies the one-sided concentration condition

`Pr(hat_Delta-Delta_R >= t | R)
 <= exp(-n*t^2/(2*chi))`

for all `t>0`, with a public registered dependence factor `chi>=1`.

For conditionally independent bounded records, Hoeffding gives `chi=1`.
For graph-dependent records, `chi` must be justified by a sampling or
dependency argument. Setting `chi=1` merely because records are edges is
invalid.

For failure allocation `beta_stat`, define

`B_stat(n_L)=sqrt(2*chi*log(1/beta_stat)/n_L)`.

The population lower certificate is

`L_pop=L_emp-B_stat(n_L)`.

## Theorem 2: one-sided no-harm activation

Let `gamma>=0` be a frozen material-improvement threshold. Activate the
structural branch only if all validity checks hold and

`L_pop >= gamma`.

Then, conditional on every training release `R` for which the statistical
assumption holds,

`Pr(Activate and Delta_R<gamma | R)
 <= beta_S+beta_n+beta_stat`.

The same statement holds unconditionally over the DP training randomness.

### Proof

With probability at least `1-beta_S-beta_n`, both Gaussian-noise events hold.
On this event,

`S >= S_tilde-b_S=S_L`

and

`n <= n_tilde+b_n=n_U`.

Because activation requires `S_L>0`,

`hat_Delta=S/n >= S_L/n_U=L_emp`.

Also `n>=n_L`. By the registered concentration condition, except on an event
of probability `beta_stat`,

`Delta_R >= hat_Delta
 - sqrt(2*chi*log(1/beta_stat)/n)`.

Using `n>=n_L` and `hat_Delta>=L_emp` gives

`Delta_R >= L_emp-B_stat(n_L)=L_pop`.

Therefore activation implies `Delta_R>=gamma` whenever all three good events
hold. A union bound proves the conditional claim. Integrating over `R` proves
the unconditional statement.

## Corollary 3: certified fallback policy

Let the deployed policy use `s_R` on activation and `s_0` otherwise. Under
Theorem 2, the probability that the policy activates a branch whose target
utility is worse than the public branch by any amount is at most the registered
failure probability when `gamma=0`.

For `gamma>0`, activation certifies a material rather than merely nonnegative
advantage.

Abstention is always permitted and is not evidence that the structural branch
is harmful.

## Multiple candidates and repeated certificates

The theorem covers one frozen structural branch and one certification release.
Selecting the best of multiple branches, trying several corruption maps,
repeating the certificate, or adapting `gamma` consumes privacy and statistical
multiplicity. Those extensions require explicit composition and simultaneous
error control.

## What is and is not certified

Certified:

- the sign and materiality of expected protocol-defined corrupted-pair utility
  on the registered target-domain distribution;
- a binary branch decision released through an edge-DP mechanism.

Not certified without an additional argument:

- standard global, intra-client, or cross-client ROC-AUC;
- temporal or cross-domain generalization;
- every individual pair score;
- utility under graph-dependent rejection negative sampling; or
- utility of an inference path that rereads private graph state.
