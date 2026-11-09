# Expired same-writer attach fixture revision

Status: SOURCE_PREPARED / PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL. No self approval, production readiness, or formal acceptance.

Only TestClientSameWriterRenewsExpiredLease in internal/domain/client_protocol_control_windows_test.go changes. All imports, other tests, production, Main, canonical records, T6 and older Source packages remain untouched by this author.

The old test expected ACKNOWLEDGED although ATT3 synchronously returns the actual committed COMPLETED AttachResult. The revised test requires that original handler response, checks the published result schema, command/method/protocol/session identity, ownership, revision 3, epoch 2 and future expiry; session.get must return the identical snapshot and committed lease. It never overwrites a response or fabricates a terminal/history row.

mixedSessionEvents maps only basic Session identity. BuildSessionSnapshot rejects empty workspace_ref, model_config_ref and core_build_id. The existing expired-lease setup statement now also supplies explicit fixture metadata fixture-workspace, fixture-model and mixed-fixture within this test body. These values are synthetic local fixture inputs, not native/provider evidence.

The original test name, epoch 2/future deadline assertion, original SQL lease read and old expected_revision=1 VERSION_CONFLICT assertion remain verbatim. Revision 3 follows the original fixture revision 1, HandoffEpoch increment and CLIENT_HANDOFF watermark increment in the pinned ATT3 implementation.

Q5 HDF/MF and helper were read as context; this candidate neither imports its new helper nor assumes its active independent review has passed. Required production composition is pinned ATT3. Root owns any composition with Q5 and fresh actual validation.

Static checks: exact inverse recovers the original file bytes; prefix/suffix outside this test body are equal; original assertions remain verbatim; all 57 explicitly frozen source inputs close unchanged. These are Python/text/hash checks, not a Go parser, compile or test result.

Actual Go/SQL/native/model execution: NOT_RUN. The amended positive test remains OPEN until Root composes independently approved sources and runs the real handler fixture. True fresh restore positives remain BLOCKED/PENDING_ROOT_RESOURCE; active asynchronous takeover, historical cached ACK reconciliation and shared TEXT/whole-chain conclusions remain outside this source scope.

Failures preserved once: 853 wrong protocol path (outer 1, Python/native NULL); 854 wrong types.go path followed by successful rg (outer 0, Python/native NULL); 855 Windows process creation rejected command length (all actual exits NULL; no process created). Original input/output are preserved in failure-origin files. Construction retry ran Python with explicit SOURCE_PYTHON_EXIT=0; it grants no runtime authority.

MF excludes itself/HDF to avoid a hash cycle. HDF pins MF and deliverables. Seal invocation and its returned tool result are delivered externally; no final subprocess exit is inferred from a pre-exit file.

