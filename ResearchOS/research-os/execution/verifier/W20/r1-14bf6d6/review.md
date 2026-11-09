# R1 fixture release review

Verdict: **NEEDS_FIX_R1_SOURCE_AND_PROCESS_IDENTITY** for `14bf6d6`.

Two P1 findings are confirmed by owned local fixtures. A dirty tracked README and an untracked JSON were packaged successfully while the manifest still claimed the frozen Git revision. A wrong PID record in data directory A caused the stop script to kill independently running fixture B from the same release; A stayed healthy. Both test processes were stopped afterwards.

The original ZIP hash and all 385 manifest entries passed; 344 source entries matched the frozen Git blobs after line-ending normalization. The author 18-case result and two-build equality evidence were hash-verified. These positives do not resolve the two reproduced boundaries.

No W20, clean-Windows A15, final upgrade, LIVE or BOUNDED_AUTO acceptance is granted. Full details and raw references are in review.json, fixture-probe/ and dirty-build/.
