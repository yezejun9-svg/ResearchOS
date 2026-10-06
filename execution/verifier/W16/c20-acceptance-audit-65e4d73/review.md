# acceptance.audit source review

Verdict: `NEEDS_FIX_SOURCE_ONLY`. Reviewed commit `65e4d73`, limited to the new `ops/ci/acceptance_audit.py` and `tests/evolution/test_acceptance_audit.py`, with existing receipt formats inspected for compatibility. No tests, candidate/native executions, or adversarial probes were run by this reviewer.

## P1: require hash coverage for every consumed file

At `acceptance_audit.py:51`, `check_hashes` accepts any nonempty hash inventory. Subsequent reads at lines 54, 60 and 77-80 consume `stdout.txt`, `before.json` and the four C20 artifact files without requiring those specific files to appear in the verified inventory. An omitted inventory entry is therefore not a failure, even though that file supplies an audited conclusion. Matching the remaining listed hashes does not bind the omitted evidence.

Require every consumed child file to pass a single bounded inventory lookup before reading. Require the expected raw output path and a positive, in-range one-based line number when following assertion references; the current code ignores the recorded raw path and permits Python negative indexing for line zero. The existing test exercises only the low-level hash loop and cannot detect missing coverage of files consumed later by `main`.

## P1: bind rejection to the evaluated candidate

At lines 77-82, wildcard lookup picks a single rejection artifact and checks only `status=REJECTED`. It does not read/bind the corresponding normal regression record, check the candidate ID/experiment ID, or compare stable/candidate artifact references with the locator/build/proof aggregates. The protected descriptors are linked only by project ID. A same-project rejection of a different candidate is not evidence that the candidate whose private result is being audited was rejected.

Resolve the C20 artifacts under the same candidate prefix and bind the rejection object's ID, project, experiment and sealed build references to the matching regression candidate/execution. Bind its normal `holdout_proof_hash` and `holdout_summary` to the already checked private-benefit/locator conclusion. This is ordinary public provenance checking and does not require exporting or reevaluating private rows.

## P2: preserve exact audited input identities

The output at lines 99-100 records upstream invocation IDs but no immutable input receipt hashes and has an empty `hashes` object. Add the exact invocation and child-report references/hashes, plus the checked child inventory (or its pinned digest), so later review can recover which bytes this audit accepted. A mutable ID alone is not a durable integrity receipt.

## Integration compatibility to resolve

Line 50 requires upstream child `report.status=PASS`. The already reviewed evolution receipt from `0503ede` uses `status=PARTIAL` and `fixture_assertion_status=PASS`, appropriately retaining broader formal-A16 limits. If the new runner retains this format, otherwise successful fixture evidence will fail here. Check the explicit fixture assertion status and exit code for this limited scope, or document an agreed updated child schema without converting a partial formal status into acceptance.

The intended scope wording is sound: exact W16/C20 selection; two explicit existing dispatcher receipts; public integrity/conclusion checks; `independent_acceptance=NONE`; no LIVE, promotion or whole-W16 acceptance. Keep these boundaries in the repaired implementation. Required command completion and independent protected objective recomputation remain separate from this source review.
