# P4R Real-Stress Execution Note

The first two execution attempts produced no result files. Both were stopped
during deterministic public SVD encoding of the 22,470 by 4,714
Facebook-MUSAE feature matrix; the second attempt exceeded 90 minutes. No gate
or P3 test result was observed, so this is an implementation abort rather than
a scientific NO-GO.

The runner now caches each public-only SVD encoding atomically by dataset,
requested dimension, and random seed. Cache metadata binds feature shape and
nonzero count; every future result records the cache path and SHA-256, and the
audit verifies it. This does not change the frozen RAP mechanism, privacy
accountant, split, baseline, or gate. It only permits safe resume after public
preprocessing.

Follow-up diagnosis found only 314,583 nonzeros in the Facebook feature matrix
(0.297% density). The same frozen randomized SVD completed in 1.40 seconds when
BLAS was limited to one thread; the long attempts were caused by pathological
thread oversubscription, not data scale. The cache implementation now limits
thread pools only while computing the deterministic public SVD. This changes
neither its algorithm, iteration count, random seed, nor output contract.
