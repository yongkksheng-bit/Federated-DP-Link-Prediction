# P5FC Test Audit Correction Note

The first independent post-test audit completed its calculations but failed
while serializing a NumPy boolean into JSON. The experiment had already
finished with the frozen decision `REJECT_GENERAL_FRONTIER_CLAIM`; no test
record, aggregate cell, threshold, statistic, random stream, or decision was
changed. The audit-only correction converts check values to built-in Python
booleans before writing `audit.json`. The one-time test was not rerun.

The initial serialized audit then reported `STOP` because it incorrectly made
scientific gate passage a condition of artifact validity. This was corrected
to verify decision consistency: failed scientific gates must yield
`REJECT_GENERAL_FRONTIER_CLAIM`, while hashes, accounting, completeness, and
statistic reproduction determine audit status. Thus an integrity `PASS` does
not convert the confirmatory scientific `REJECT` into a positive result.
