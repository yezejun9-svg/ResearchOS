Source preparation only. Sole future executor/integrator: Root.

Selected files are identified by handoff.json, not by preliminary filenames.
The fixed r332 engine is reused for owned Python/Git, Python flags, original
streams, Job cleanup, 15 Git calls per mode, 1200-second observed deadline,
32-GiB cumulative reads, immutable input validation, and four-file CAS directly
after each source guard. This preparation does not invoke that engine.

Future Root interface:

1. Freeze one request using the schema/fields in request-contract.json. Supply
   the actual timestamp, fresh registration namespace, immutable four original
   copies, source closure review/MF, explicit failure cut, tools, runtime,
   selected engine/builder pins and current immutable source/resource pins.
2. Run pinned Python -I -S -X utf8 <selected-builder> <request-path> <request-SHA>.
   The builder is pure IO. It verifies the closed source chain and creates only
   a fresh registration leaf, original/desired bytes, register/run/seal scripts,
   prepared_refs.json and audit.json. It imports no WinAPI/helper and invokes no
   Git. A changed actual HEAD can only be detected at the later native guard;
   preparation checks the sealed actual HEAD and current source blob bytes.
3. Independent W05 reviewer binds the generated register/run/prepared/audit
   pins and ordered canonical copies with the existing root-registration
   review schema. This review is created after draft generation, so no cycle.
4. Root runs generated run.py <request-path> <request-SHA> <review-path>
   <review-SHA>, using pinned Python flags. It validates that review before
   launching generated register.py with the same arguments in an owned Job.
   Register writes only checkpoint and path_ownership after intent+desired
   bytes and all-four immediate CAS checks. ST/commands remain original bytes.
5. Root runs seal.py <request-path> <request-SHA> only after actual run success.
   It verifies actual registration/native0/Job closure and actual target four,
   produces post-registration audit/handoff/MF, and creates no source scope or
   execution grant. Fresh58/GUI/SQL24/formal acceptance remain OPEN.

No automatic recovery, retry, rollback or replacement of evidence exists.
After partial registration, preserve intent, originals, desireds, actual
canonical bytes, done markers, raw streams and failure receipt. Root must
independently inspect the exact completed prefix and commission a separate
forward-only recovery input. Never rerun a failed namespace.

Pure IO reads have chunk-level observed deadlines, not a hard deadline for a
blocked filesystem call. Python/OS observation is point-in-time, not a whole
lifecycle claim. The preserved bridge tool observation is not an original
native stdout/stderr recording. None of these limitations is promoted to
source/product qualification.

Only preparation constructors and AST/IO checks ran in this namespace.
Candidate imports, helper calls, Git, Go, SQL, Node, HTTP, models and canonical
writes: zero. One read-only display failure 09b17d is preserved with outer1,
native NULL and the explicit output-truncation limitation. No retry occurred.
