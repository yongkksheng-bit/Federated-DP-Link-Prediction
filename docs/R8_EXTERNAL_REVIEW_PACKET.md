# R8 External Privacy/Statistics Review Packet

## Reviewer instruction

Please review independently. Do not assume the R7/R8 PASS conclusions are
correct. The desired output is a signed or attributable memorandum listing:

- errors;
- missing assumptions;
- acceptable but narrow claims;
- required corrections; and
- a final `GO`, `GO WITH REVISION`, or `NO-GO`.

No sealed holdout access is needed or permitted.

## Minimal files

1. `manuscript/main.tex`
2. `manuscript/sections/03_problem.tex`
3. `manuscript/sections/04_method.tex`
4. `manuscript/sections/05_theory.tex`
5. `manuscript/sections/09_appendix.tex`
6. `src/fed_dp_lp/accounting.py`
7. `src/fed_dp_lp/private_certificate.py`
8. `src/fed_dp_lp/r5_holdout.py`
9. `configs/r5_graph_phase_confirmatory.json`
10. `results/r5_graph_phase_confirmatory/records_strict.jsonl`
11. `results/r5_graph_phase_confirmatory/summary.json`

R7/R8 reports may be read only after the independent derivation.

## Privacy questions

1. Under the stated role-labelled adjacency, is the adaptive max-RDP theorem
   correct for the released joint transcript `(R, noisy certificate,
   decision, scores)`?
2. Is uniform conditional RDP of certification for every fixed `R`
   sufficient after integrating over a common training-release distribution?
3. Does the sequential RDP sum remain valid on the registered role-labelled
   database, and does the paper clearly avoid claiming raw-graph adjacency?
4. Does any server-visible or inference-time path reread private topology?
5. Is `sqrt(2)` the correct add/remove sensitivity of `(bounded sum, count)`
   given inference closure and graph-independent corruption?
6. Are visible-message and ideal-secure-aggregation noise/trust assumptions
   correctly separated?

## Statistics questions

1. Conditional on a population fixed independently of assignment outputs and
   the realized count, is the certification subset uniform without
   replacement?
2. Is the one-sided Serfling penalty correct for values in `[-1,1]`?
3. Do the Gaussian sum/count events and use of `n_L`, `n_U`, and positive
   corrected numerator yield a valid lower certificate?
4. Does conditioning on the DP training release invalidate any sampling step?
5. Is the failure probability correctly union-bounded?
6. For a PRF deployment, is adding PRF distinguishing advantage sufficient?

## Lower-bound questions

1. Are the block-replicated hard instances compatible with single-record
   add/remove adjacency?
2. Is the KL expansion and `chi/alpha^2` rate correct under the stated domain?
3. Is the add/remove-to-replacement conversion correct?
4. Does the cited private Le Cam result imply the exact `2D_star/alpha` term
   with the constants used?
5. Is the `1/(epsilon alpha)` simplification valid for pure DP, and is the
   approximate-DP limitation now adequate?

## Stop conditions

Return `NO-GO` immediately if:

- raw-graph adjacency is required for the theorem as written;
- one certification edge changes multiple utility records;
- the certificate lower bound can exceed the target lower confidence bound on
  its stated good events;
- the RDP conversion or composition is incorrect; or
- the finite-population theorem requires adaptive randomness not disclosed in
  the paper.

## Artifact commands

```powershell
python -m pytest -q
python scripts/audit_r7_theory_contract.py
python scripts/audit_r8_red_team.py
python scripts/reproduce_r7_artifact.py
python scripts/reproduce_r8_submission.py
```

The last command rebuilds figures and the manuscript from tracked evidence
without reopening the sealed holdout.
