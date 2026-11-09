"""Freeze offline preparation only; no supervisor import, process or network."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
R4 = BASE.parent / "owned-model-resource-stage-b" / "revision-04"
V1_REVIEW = BASE / "reviews" / "independent-supervisor-review-01"
OLD_MANIFEST_SHA = "1b8004fc8f11fd11dc49ad0793f688f25cc69c581166b3a156293f1a996e1fe9"
OLD_REVIEW_SHA = "bed62d14124fd98c90a52f3981f51fb556622a023b5170becec353baad0389b4"
COUNTEREXAMPLE_SHA = "c1c291826e6d42d819843019de46b24e5bd67e00d9e8badffbd4a379909eff4e"
OLD_CHECKS_SHA = "e1dfaf5eb2e7b2adde736108a345b80b997bdb17df3d44416155f1283495d21f"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as stream:
        if isinstance(value, dict):
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        else:
            stream.write(value)


assert not (HERE / "MANIFEST.json").exists(), "Existing freeze: read back, never replay"
assert digest(BASE / "MANIFEST.json") == OLD_MANIFEST_SHA
old = json.loads((BASE / "MANIFEST.json").read_bytes())
for item in old["files"]:
    assert digest(BASE / item["relative"]) == item["sha256"], item["relative"]
r4 = json.loads((R4 / "PREPARED-MANIFEST.json").read_bytes())
for item in r4["files"]:
    assert digest(R4 / item["relative"]) == item["sha256"], item["relative"]
for name, pin in (("source-review.json", OLD_REVIEW_SHA),
                  ("counterexample.json", COUNTEREXAMPLE_SHA),
                  ("offline-checks.json", OLD_CHECKS_SHA)):
    assert digest(V1_REVIEW / name) == pin
assert not (BASE / "attempt-01").exists()
assert not (R4 / "run-01").exists()
log = (HERE / "mock-tests-attempt-01.log").read_text(encoding="utf-8-sig")
assert "Ran 15 tests" in log and "OK" in log and "FAILED" not in log
source_pin = digest(HERE / "supervise.py")
test_pin = digest(HERE / "test_supervise.py")
common_zero = {"real_Popen_calls": 0, "controller_runs": 0, "native_backend_runs": 0,
               "model_GPU_starts": 0, "real_HTTP_requests": 0, "private_key_reads": 0,
               "D_writes": 0, "formal_increment": 0, "counter_reset": False}
scope = {
    "schema": "researchos.model-resource-supervisor-scope.v1",
    "status": "PREPARED_NOT_AUTHORIZED_TO_RUN", "owner": "codex:/root/runtime_readiness",
    "revision": 2, "preparation_baseline_checkpoint": 593,
    "predecessor_manifest_sha256": OLD_MANIFEST_SHA,
    "predecessor_blocking_review_sha256": OLD_REVIEW_SHA,
    "repair_scope": "SUP-P1-001 only: acquired-handle cancellation coverage; necessary revision manifest paths",
    "controller": str(R4 / "controller.exe"), "controller_sha256": r4["controller_sha256"],
    "controller_scope_sha256": r4["scope_sha256"],
    "r4_conditional_review_sha256": "627a3d31af529584495e739c5f892b732a3d1eef6c86b326dd09629a48c0282f",
    "endpoint": "http://127.0.0.1:43861", "original_r4_run_directory": str(R4 / "run-01"),
    "supervisor_attempt_directory": str(BASE / "attempt-01"),
    "attempt_scope": "GLOBAL original attempt-01, shared with predecessor; revision grants no extra launch",
    "outer_wait_seconds": 180, "kill_confirmation_seconds": 5,
    "maximum_launches": 1, "maximum_kill_attempts": 1, "maximum_confirmation_waits": 1,
    "stdout_stderr": "DEVNULL", "original_Popen_object_required": True,
    "real_run_requires": "Independent revision02 review plus separately hash-bound new public D Root scope/current checkpoint; no actual run authorization in this packet",
    "timeout_or_uncertain_policy": "UNKNOWN/inconclusive; no retry, no late RESULT promotion, resource_ready false",
    "limitations": "No guarantee for power loss, externally killed supervisor, repeated asynchronous interruption during cleanup or non-returning OS calls; no R4 logger IO while child active",
    "inference_limit": 0, "formal_increment": 0, "counter_reset": False,
}
write("SCOPE.json", scope)
write("CHECKS.json", {
    "schema": "researchos.model-supervisor-offline-checks.v1", "revision": 2,
    "started_chunk": "339a72", "session": 71626, "terminal_chunk": "6fd518", "actual_batch_exit": 0,
    "mock_test_exit": 0, "mock_test_count": 15, "py_compile_exit": 0,
    "python": "C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe",
    "python_sha256": "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b",
    "raw_mock_log_sha256": digest(HERE / "mock-tests-attempt-01.log"),
    "new_regression": "First line and first opcode after fake handle assignment each inject KeyboardInterrupt; same fake kill1+wait5, UNKNOWN, no launch retry",
    "path_regression": "ROOT revision02; ATTEMPT original global attempt01; R4 original run01/controller/scope/43861",
    "old16_pins_checked": len(old["files"]), "old16_changed": 0,
    "r4_15_pins_checked": len(r4["files"]), "r4_pins_changed": 0, **common_zero,
})
write("AUTHOR-DIAGNOSTICS.json", {
    "schema": "researchos.model-supervisor-author-diagnostics.v1", "revision": 2,
    "blocking_origin": "SUP-P1-001", "origin_source": "Independent v1 review; reference existing origin, do not duplicate failure index",
    "blocking_report": str(V1_REVIEW / "source-review.json"), "blocking_report_sha256": OLD_REVIEW_SHA,
    "counterexample_sha256": COUNTEREXAMPLE_SHA, "old_offline_checks_sha256": OLD_CHECKS_SHA,
    "original_counterexample_terminal_chunks": ["e8d40e", "c2eeaf"],
    "original_counterexample": "v1 first KeyboardInterrupt at line129 after fake handle assignment escaped; fake events empty; real child0",
    "source_repair": "process=None; factory assignment and wait in one try; except branches by returned original process object",
    "verification": "6fd518 exit0: 15pure mocks incl actual line/opcode injection plus py_compile; independent review pending",
    "old_fixture_failure_preserved": {"origin": "SUPERVISOR-MOCKS-01-DEFAULT-TEMP-ACL", "terminal_chunk": "edb15c", "exit": 1, "fixture_errors": 3,
                                      "source_and_log": str(BASE / "failed-attempt-01"),
                                      "diagnostics_sha256": digest(BASE / "AUTHOR-DIAGNOSTICS.json")},
    "old_BUILD01": "Reference only; Root already owns pending original origin; no duplicate index or reset",
    "uncertainty": "v1 freeze output truncation resolved by readback182914/a6b870; no replay; any future transport outcome remains UNKNOWN until readback",
    "old_v1_frozen16_unchanged": True, "old_R4_frozen15_unchanged": True, **common_zero,
})
write("ROOT-AUTHORIZATION-TEMPLATE.json", {
    "schema": "researchos.root-model-supervisor-authorization.v1", "actor": "codex:/root",
    "project_id": "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", "status": "TEMPLATE_NOT_AUTHORIZATION",
    "checkpoint_revision": 0, "checkpoint_sha256": "<FILL_NEW_D_CHECKPOINT_SHA256_AFTER_ROOT_WRITES_IT>",
    "controller_sha256": r4["controller_sha256"], "controller_scope_sha256": r4["scope_sha256"],
    "supervisor_manifest_sha256": "<FILL_REVIEWED_REVISION02_MANIFEST_SHA256>",
    "supervisor_scope_sha256": digest(HERE / "SCOPE.json"), "endpoint": "http://127.0.0.1:43861",
    "max_controller_launches": 1, "inference_limit": 0, "attempt_directory": str(BASE / "attempt-01"),
})
write("README.md", """# Revision02: offline repair, not runtime authorization

Only SUP-P1-001 is repaired: the original process reference starts as None, and factory assignment plus immediate wait share one try. The exception handler distinguishes no returned handle (UNKNOWN, no rediscovery) from the acquired original object (one kill, one wait5, UNKNOWN). Factory return and wait have no filesystem/log/Sync work between them. This removes the reviewed first-cancellation window without changing native R4.

The regression uses actual sys.settrace line and opcode callbacks. In two subcases it raises the first KeyboardInterrupt immediately after the fake object is assigned, before wait starts. Both retain that exact object, call kill once then wait(timeout=5) once, and return UNKNOWN. It does not move a hard-coded source line. Fifteen pure mocks and py_compile passed (6fd518 exit0); no real Popen/native/backend/model/GPU/HTTP was called.

The only source path adaptation is BASE for the original supervisor directory and ROOT=BASE/revision-02 for this reviewed source/manifest/scope. ATTEMPT remains BASE/attempt-01, shared globally with v1. R4 absolute root/run-01, exe332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297, scope49a78cf270e40f4e76131bd9a1cd98e929548f39d36e9e1d203507f6ab67bdab, endpoint127.0.0.1:43861 and maximum launch1 remain fixed. A new source revision grants no new attempt. Existing attempt or run requires readback and blocks replay. Neither exists at freeze.

Original v1 MANIFEST16 pins, failed fixture sources/logs, independent P1 report and counterexample, uncertainties and R4 freezes remain unchanged. AUTHOR-DIAGNOSTICS references their exact hashes without resetting or duplicating old origins. P1 source repair is not independent acceptance; the new revision needs independent review. Old v1 is still rejected and must not be executed.

Single future Root entry is fixed absolute C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe with -I -S -X utf8 and this revision's supervise.py. Do not run prepare_revision.py/freeze_revision.py again; they are one-use author records, not execution entries. This packet authorizes no actual execution. Root must separately create the public D authorization/current checkpoint bound to reviewed revision02 MANIFEST and SCOPE hashes; the template is deliberately invalid. Global consumption happens before any Popen construction. All inherited secret/proxy/profile values are excluded; only public environment key names are recorded.

Outer wait remains180 seconds, covering pre/post981-asset hashing, native60 and cleanup15 plus margin. stdout/stderr/stdin are DEVNULL, CREATE_NO_WINDOW, no PID/name scan or child pipes. Timeout/error/missing or incomplete RESULT stays UNKNOWN/inconclusive and never implies resource_ready. Even complete reported proof awaits Root review and is not native/qualification/business acceptance. A later RESULT cannot promote timeout. No retries or old scope/modelstore writes are allowed.

No Python code can guarantee progress after power loss, externally killed supervisor, a non-returning OS/Popen construction/termination call or repeated asynchronous interruption during cleanup. The first reviewed acquired-handle cancellation is now protected and tested. R4's logger mutex cannot block the wrapper's wait/kill path because it reads no logs, assets or RESULT while the original process is active. Postterminal reporting may fail, but never grants permission to replay.
""")
files = []
for path in sorted(HERE.rglob("*")):
    if path.is_file():
        files.append({"relative": path.relative_to(HERE).as_posix(), "bytes": path.stat().st_size,
                      "sha256": digest(path)})
write("MANIFEST.json", {
    "schema": "researchos.model-resource-supervisor-manifest.v1", "revision": 2,
    "status": "PREPARED_MOCK_VERIFIED_NOT_AUTHORIZED_TO_RUN", "owner": "codex:/root/runtime_readiness",
    "at": datetime.now(timezone.utc).isoformat(), "preparation_baseline_checkpoint": 593,
    "predecessor_manifest_sha256": OLD_MANIFEST_SHA, "predecessor_blocking_review_sha256": OLD_REVIEW_SHA,
    "source_sha256": source_pin, "tests_sha256": test_pin, "scope_sha256": digest(HERE / "SCOPE.json"),
    "controller_sha256": r4["controller_sha256"], "controller_scope_sha256": r4["scope_sha256"],
    "global_attempt_directory": str(BASE / "attempt-01"), "original_r4_run_directory": str(R4 / "run-01"),
    "old16_pins_checked": len(old["files"]), "old16_pins_changed": 0,
    "r4_15_pins_checked": len(r4["files"]), "r4_pins_changed": 0,
    "mock_count": 15, "mock_exit": 0, "py_compile_exit": 0,
    "independent_review_required": True, **common_zero, "files": files,
})
print(json.dumps({"status": "REVISION02_FROZEN_OFFLINE", "manifest_sha256": digest(HERE / "MANIFEST.json"),
                  "scope_sha256": digest(HERE / "SCOPE.json"), "source_sha256": source_pin,
                  "tests_sha256": test_pin, "file_count": len(files),
                  "global_attempt_exists": (BASE / "attempt-01").exists(), "r4_run_exists": (R4 / "run-01").exists(),
                  **common_zero}))
