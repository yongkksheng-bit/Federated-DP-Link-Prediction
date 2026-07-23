# R5 Finite-Population No-Harm Theorem

## Why R5 changes the certification split

The original P3 validation edges were used to select the projection dimension
and hop count of the frozen GAP-style candidate. They therefore cannot also
serve as an independent utility certificate. R5 leaves the selected candidate
unchanged and partitions the still-encrypted P3 test positives, at their
one-time opening, into disjoint certification (`C5`) and evaluation (`Q5`)
roles using a protocol-frozen edge-keyed random hash.

No test edge, score, count, or graph statistic was inspected when this rule,
its salts, the certificate threshold, or the decision gates were frozen.

## Finite target population

Fix a dataset, split seed, DP training release `R`, and the sealed P3 positive
holdout population `H={e_1,...,e_N}`. For each edge define

`d_R(e)=U_{s_R}(e)-U_{s_0}(e) in [-1,1]`,

where `U` compares the positive edge with the registered deterministic
endpoint corruption. The finite-population target is

`Delta_H(R)=N^{-1} sum_{e in H} d_R(e)`.

This is a pairwise ranking estimand on the registered finite holdout. It is not
identical to ROC-AUC and is not a claim about future temporal edges or another
graph domain.

## Registered random partition

An edge-keyed SHA-256 random value assigns each holdout edge independently to
`C5` with public probability `p_C=1/3`; the complement is `Q5`. The assignment
uses a frozen salt and does not inspect endpoints beyond their canonical key,
graph statistics, model scores, or labels other than membership in the sealed
positive holdout.

Under the registered random-oracle interpretation, conditional on the realized
certification count `n`, `C5` is a simple random sample without replacement
from `H`. Adding or removing an edge does not change any existing edge's hash
assignment.

## Lemma: graph overlap does not inflate the sampling factor

Conditional on `(R,H,n)`, the values `{d_R(e):e in H}` are fixed bounded finite
population values. Their shared nodes and graph dependence are irrelevant to
the randomness of selecting `C5`. By the one-sided Serfling inequality,

`Pr(hat_Delta_C-Delta_H >= t | R,H,n)`

`<= exp(-n t^2 / (2 f_N))`,

where

`f_N=1-(n-1)/N <= 1`.

Thus the earlier R1 concentration condition is valid conservatively with
`chi=1`; retaining `f_N` yields a tighter finite-population correction. This
argument certifies only the finite registered holdout and does not establish
i.i.d. graph-edge generalization.

## Private certificate

The certification query is `(S,n)` with

`S=sum_{e in C5} d_R(e)`.

Its add/remove-edge L2 sensitivity is at most `sqrt(2)`. The Gaussian mechanism
releases a noisy sum and count. Let `L_emp` be the noise-corrected empirical
lower bound from R1 and define

`B_FP=sqrt(2 f_N log(1/beta_FP)/n_L)`,

using the conservative private lower count `n_L` in the denominator and the
public holdout size `N` only in the research audit. The deployment-safe
implementation may set `f_N=1` when `N` is not public. R5 reports both, but the
activation decision uses the conservative `f_N=1` bound.

Activate only if

`L_pop=L_emp-B_FP >= gamma`.

With failure allocations `beta_S`, `beta_n`, and `beta_FP`,

`Pr(Activate and Delta_H(R)<gamma | R,H)`

`<= beta_S+beta_n+beta_FP`.

The proof is the R1 union-bound proof with Serfling replacing the assumed
graph-dependent concentration condition.

## Privacy accounting

The training and certification mechanisms operate on disjoint registered
roles, but R5 deliberately takes no parallel-composition credit. It sums their
RDP curves and converts the result once to `(epsilon_total, delta_T+delta_C)`.
This conservative choice avoids relying on the historical P3 split generator
as a stable edge-level partition mechanism.

Each epsilon-grid cell is an alternative deployment. Releasing all cells on
one private graph would require composition across cells and is not claimed.

## Scope

Certified:

- finite sealed-holdout pairwise utility of one frozen DP structural branch;
- a no-harm activation decision relative to the public branch; and
- post-processed scores from the selected inference-closed branch.

Not certified:

- standard ROC-AUC itself;
- future, temporal, or cross-domain utility;
- public release of the sealed research metrics; or
- simultaneous deployment of every diagnostic privacy cell.
