# Evidence Policy

## Evidence states

Every artifact must be classified as one of:

- **Protocol**: committed before the corresponding access or execution.
- **Diagnostic**: useful for development but prohibited from headline claims.
- **Admitted evidence**: passed integrity, privacy, statistical, and leakage
  audits under a frozen protocol.
- **Closed evidence**: a preregistered failure retained without retuning.

Generated output is not admitted evidence merely because a script completed.

## Minimum experimental controls

Headline utility requires matched comparisons against:

- public-input-only inference;
- seeded random scores;
- noise-only or zero-private-signal controls;
- a tuned non-private oracle;
- matched private objective and architecture ablations;
- relevant independently implemented external baselines.

Primary comparisons require paired seeds, confidence intervals, and an effect
threshold frozen before metric access. Statistical significance without a
practical effect is insufficient.

## Privacy evidence

A formal privacy result must record:

- the neighboring-dataset definition;
- the complete per-record computation;
- clipping position and norm;
- public versus private randomness;
- sampling assumptions;
- every server-visible mechanism;
- composition orders and values;
- delta and resulting epsilon;
- private parameter or release dimension;
- the exact released object and deployment interface.

Training-time DP does not automatically cover embeddings or scores recomputed
from a private graph.

## Test boundary

Test identities and labels remain sealed until the final model, protocol,
baselines, seeds, and analysis plan are committed. Test access is one-time and
must leave a machine-readable access record.

