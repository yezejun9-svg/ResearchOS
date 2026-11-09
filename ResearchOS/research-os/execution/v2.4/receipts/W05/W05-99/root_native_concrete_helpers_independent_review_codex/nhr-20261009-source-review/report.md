# Independent Source review
Status: REQUEST_CHANGES. Candidate helper 853cbd80e0603d7f8134833319d8579065639a1dcd2839976d4f8874e6b0cb18 / 28426; archive 189ebdc33751c4becf98b665e365ba84b0996497c1cb5d04576530c99a7e180c / 4618. Reviewer codex:/root/attach_fixture_source_review is not candidate author.

## NHR-001 — real inspection database pin cannot reach fixture release
At root_concrete_approval_helper.py:334, retained() routes q.database_ref through plain(), whose SHA256 validator at line 62 requires sha256: plus 64 lowercase hex. The existing Root API pin_raw returns a bare hexdigest, and its real whole-fixture inspection places pin(db_path) into database_ref. An existing real inspection receipt confirms that database_ref uses bare 64hex while before_ref uses sha256: prefix. The independent pure-function reproduction using that exact public database_ref raises ValueError("SHA256 pin"). This happens before database existence validation; it is not caused by the historical fixture already being absent. A fresh correctly inspected retained fixture would fail for the same reason.

Repair in a new immutable revision: validate the actual inspection database-ref contract separately from public RawPin; retain exact hash/size/types and path rules. Do not change prior receipts or blanket-normalize evidence. Add a source-level control using the actual producer's inspection shape, then repeat non-author Source review before Root uses release-fixture. No candidate source was changed by this reviewer.

## Other reviewed boundaries
- load_context restricts positive-replay and current phase, reads every declared FrozenInput, checks required controller/harness/program/compiler members, and links Snapshot/Config/case. Current pinned controller declares 4347 FrozenInputs. This review verifies the config pin and candidate handling logic; it does not rehash all 4347 runtime resources or certify a future new config.
- release_source_set enumerates the seven harness source roots, optional vendor, module/toolchain and optional workspace files; validate_release compares the full source path/role set and reads every declared pin.
- Public metadata verifies separate issuer and root-adoption fields; private_resource_ref is not traversed. API still selects the real issuer and enforces runtime authority.
- Native signer result requires integer PID/FILETIME, actual exit 0, no timeout/error, all six Job cleanup flags, zero active processes and no errors; guard closure requires no retained handles. Independent controls reject boolean integers, floating FILETIME, open Job/guard.
- Signing and publication are distinct explicit actions. Publication checks previous approval and signer receipt, exact payload byte substring, and current absolute validity. The original grant interval remains exactly 240 seconds. Helpers do not call controller/API, sign, publish, launch children, execute SQL or refresh time.
- T10 terminal controller and missing original fixture paths are rejected by current_phase / existence checks. This review did not invoke the candidate main or attempt to revive T10.
- Retained release requires an existing whole-fixture inspection pinned to config/snapshot, stable data version/native IDs, both reader closures and public whole-row digest. Its new migrated branch relies on the trusted inspection receipt and matches after rows, target schema and declared original invariants; unchanged-failed compares all before rows/schema versions. No real SQL inspection was performed here.
- Archive explicitly allows only typed-row digest maps and fixed fixture-summary fields, rejects other kinds, validates single JSON filenames and copies exact input bytes without recursively following embedded paths. It is intentionally not a full archive.

## Evidence and limits
107 independent pin/boundary checks passed, including exact candidate HDF/MF pins, 20 manifest members, 18 author input pins, real inspection pin-format reproduction, and before/after equality for 41 input files. A passed reproduction means the incompatibility was confirmed, not that the helper is accepted. Original tool I/O is retained. No Git/Go/native/SQL/model execution, private key reads, approval generation, Main or canonical edits occurred. No product/formal acceptance is claimed.

Tool request parsing failures 897 and 898 were assigned by Root: invalid history.search_contents fields, rejected before command execution; outer/Python/native exits are all NULL. Both exact inputs and outputs are in original-tool-io.json. next899. These are tooling errors, not candidate native failures.

