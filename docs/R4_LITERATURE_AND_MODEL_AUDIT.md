# R4 Literature and Model Audit

## Primary lower-bound source

Acharya, Sun, and Zhang, "Differentially Private Assouad, Fano, and Le Cam,"
ALT 2021:

https://proceedings.mlr.press/v132/acharya21a.html

Their Theorem 1 provides an approximate-central-DP Le Cam bound in terms of an
expected Hamming-distance coupling. This is the primary tool registered for the
R4 binary utility test.

## Mean-estimation rate reference

Kamath, Singhal, and Ullman, "Private Mean Estimation of Heavy-Tailed
Distributions," COLT 2020:

https://proceedings.mlr.press/v125/kamath20a.html

The paper establishes private univariate mean-estimation rates containing
sampling and privacy terms. R4 treats it as rate-level context, not as a direct
proof for the bounded binary hard pair, because a lower bound over a broader
moment class does not automatically establish a lower bound over the bounded
Rademacher subclass.

## Local-model references

Duchi, Jordan, and Wainwright, "Minimax Optimal Procedures for Locally Private
Estimation":

https://arxiv.org/abs/1604.02390

Duchi and Rogers, "Lower Bounds for Locally Private Estimation via
Communication Complexity," COLT 2019:

https://proceedings.mlr.press/v99/duchi19a.html

These results do not directly apply to the current visible-message model.
Each project client privatizes a statistic of many local edge records; this is
not record-wise local differential privacy.

## Secure aggregation and correlated messages

Chen et al., "The Fundamental Price of Secure Aggregation in Differentially
Private Federated Learning," ICML 2022:

https://proceedings.mlr.press/v162/chen22c.html

Vithana et al., "Correlated Privacy Mechanisms for Differentially Private
Distributed Mean Estimation," 2024:

https://arxiv.org/abs/2407.03289

These works show why a general ideal-versus-visible separation must specify
communication, correlation, collusion, and server-visibility assumptions.
Consequently, R4 will not promote the current independent-Gaussian `sqrt(K)`
effect into an information-theoretic theorem without an additional proof.

## Audit conclusion

- General central approximate-DP lower bound: admissible.
- Non-private dependent-block lower bound: admissible.
- Pure-DP `1/(epsilon alpha)` order: admissible as a special case.
- Approximate-DP finite-constant bound: must be evaluated using the registered
  Acharya expression.
- Generic `sqrt(K)` visible-message minimax penalty: not currently admissible.
- Record-wise local-DP lower bounds: not currently applicable.
