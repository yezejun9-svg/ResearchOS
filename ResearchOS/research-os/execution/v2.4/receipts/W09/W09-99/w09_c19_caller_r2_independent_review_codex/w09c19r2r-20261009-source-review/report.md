# W09 C19 Caller r2 independent Source review

SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL.

The independent review passed 573 checks over 194 pinned inputs. Source resource gate passes conditionally on Root completing the concrete scope registration and issuing the explicit canonical vector before actual preparation. Actual resource gate, Git/Go/producer execution, and formal consumers remain NOT_RUN. No new mechanical failures occurred.

## Exact delta and reused conclusions

Verified the candidate HDF and MF exact handoff pins, all 21 manifest members, the prior accepted caller review and its manifest members, and the original caller packet. Independently recomputed both complete byte-level diffs and inverse reconstructions. Every original function and the entire execution/Job/cleanup body remain unchanged, except the preparation ready receipt gains the explicit vector reference. Each caller adds exactly one binding function; both definitions are AST-identical to the reviewed function artifact.

Choice reconstruction exactly recovers the original JSON object. The four CP364 canonical pins and checkpoint revision move to historical provenance only. Runtime original_input_refs no longer include those stale pins. The original six v6 Source references, selected test order (ChainInvalidation then ExplicitOriginAndUnknown), expected assertions, compiler inventory, one producer invocation, owned Job boundaries, failure retention, and cleanup guards are preserved. All five fixed candidate/output/environment paths remain identical and absent at review time.

## Dynamic canonical binding

Preparation takes CP3 plus VECTOR3; producer takes choice2, CP3, isolation-ready2 and VECTOR3. The vector path must be explicit, absolute, resolve under the W09/W09-99 receipt namespace, and use canonical-input-vector.json. Its declared size is a positive non-bool integer no greater than 65536. The reader requests declared bytes + 1, then checks exact length and SHA before parsing JSON.

The parsed vector has the expected schema, positive integer revision, and exactly four unique references resolving to the fixed checkpoint/path_ownership/step_state/commands paths. Each ref has exactly path/sha256/bytes; hashes are lowercase hexadecimal and each declared size is positive, non-bool and no greater than 64 MiB. All four are compared to current observed bytes; checkpoint SHA/size/revision must match the explicit CP3. Ref ordering is normalized to the fixed four-file order.

These are bounded vector reads. The inherited initial read_bytes calls on the four fixed canonical files remain unchanged; this review does not claim a new streaming cap on those initial reads. Their exact pins and the vector pin are subsequently acquired by the existing capped SourceReadGuard before actual owned execution. Original expected canonical refs are passed to the guard, preserving drift detection between observation and acquisition.

Preparation writes the vector ref into its exact ready receipt. Producer verifies the explicitly pinned ready, compares its vector ref with the freshly validated vector ref before creating its output, and holds the vector and all four canonical refs through execution. A same-size vector mutation fails SHA; a different vector path or hash fails ready binding. No latest resolution or authority parser was added.

Independent tests execute only the inspected binding FunctionDef against in-memory streams. Positive synthetic revisions 3 and 371, reversed reference order, bounded reads, invalid vector size/hash/path/schema/fields/revision, missing/extra/duplicate/foreign refs, invalid ref types/caps/hashes, mismatched CP3 and changed bytes for each canonical file were checked. No actual vector file or caller top level was executed.

## Root registration and execution boundary

The proposal is concrete but unapplied: add the Root-owned c19_fixture_producer scope while preserving existing Exact4 ownership; record the corresponding worker; reconcile active construction parents under the max-two rule; preserve accepted W09-01/02 and do not invent W09-99 acceptance or formal-route registration. Complete canonical changes first, then issue one fresh exact vector and pass the same CP3 and VECTOR3 to both stages. Do not rewrite pinned canonical bytes/vector during the run.

This Source gate does not certify that registration has happened, authorize a third active construction parent, or qualify actual Job/resource closure. Root must inspect actual receipts before downstream independent review and two same-run formal consumers in their established order. Formal consumers remain NOT_RUN_REGISTRY_UNBOUND and formal acceptance increment is zero.

## Review integrity

Immutable input pins were rechecked under the accepted OS SourceReadGuard; the guard closed with no retained handles/errors. Shared canonical files were observed before/after and excluded from this review's held handles; all four remained unchanged at revision 364. Review writes are confined to this new namespace. No candidate, Main, canonical, prior sealed packet, actual worktree, Git, Go, producer, SQL, API, private key or model operation was performed. Author failure 922 remains the original sealed provenance and is not a new review failure. Full read and reviewer-run tool I/O is retained.

