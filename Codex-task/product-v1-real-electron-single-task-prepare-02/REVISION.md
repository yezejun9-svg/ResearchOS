# Revision 02 provenance

Revision 01 was declared frozen with runner SHA-256
`cf26312f9b3fb9f3e33b414a3afac2bbb5fa2f255fbcc0922ab137a2f32e6d49`.
After that declaration, but before independent review or execution, its runner
and `FROZEN.json` were updated in place to lock the original request ID/Task
across polls and reject a second RunRef. That was a freeze-process error. The
earlier `cf26312…` runner bytes and original FROZEN bytes were not found in the
available C workspace; they have not been recreated from memory. The old
declared hash is superseded and must not be used for registration or review.

This directory copies the exact post-correction revision-01 files. Its
`01-current-FROZEN.json` is the current revision-01 metadata copied verbatim,
not the unavailable original freeze. The new `FROZEN.json` records revision-02
file hashes. Revision 01 has not been edited during this provenance repair.

No revision-01 or revision-02 one-task runner was executed. Native prerequisite
remains blocked by the foreground guard before either OK click, so revision 02
is not registered or run-ready. Any further source change requires a new
revision directory; preserve both existing revisions unchanged.
