# P5F Audit Correction Note

The first independent audit stopped on `frozen_backbones`. The experimental
records were valid and unchanged. The audit had incorrectly required the
actual encoded width to equal the requested SVD width. PolBlogs has two public
feature columns, so the frozen request `d=8` correctly yields an actual width
of two under the pre-existing public encoder.

The corrected audit verifies three separate facts from the immutable cache:
the cached requested width equals the frozen configuration, the recorded
actual width equals the cached array width, and the recorded hop count equals
the frozen hop count. No experimental result, analysis gate, random stream, or
summary decision was changed after observing results.
