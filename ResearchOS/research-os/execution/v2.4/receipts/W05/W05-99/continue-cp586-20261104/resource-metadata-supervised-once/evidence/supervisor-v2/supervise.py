"""One-use Root entry for the frozen R4 controller. Preparation never launches it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

BASE = Path(r"C:\Users\yqyyds\Documents\Codex\2026-11-04\task\cp586-continuation\owned-model-resource-supervisor-20261104")
ROOT = BASE / "revision-02"
R4 = BASE.parent / "owned-model-resource-stage-b" / "revision-04"
CONTROLLER = R4 / "controller.exe"
CONTROLLER_SHA = "332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297"
R4_SCOPE = R4 / "SCOPE.json"
R4_SCOPE_SHA = "49a78cf270e40f4e76131bd9a1cd98e929548f39d36e9e1d203507f6ab67bdab"
REVIEW = R4 / "reviews" / "independent-source-review-01" / "source-review.json"
REVIEW_SHA = "627a3d31af529584495e739c5f892b732a3d1eef6c86b326dd09629a48c0282f"
PYTHON = Path(r"C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe")
PYTHON_SHA = "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
ENDPOINT = "http://127.0.0.1:43861"
ATTEMPT = BASE / "attempt-01"
R4_RUN = R4 / "run-01"
CHECKPOINT = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\checkpoint.json")
AUTHORIZATION_ROOT = CHECKPOINT.parent / "receipts"
PROJECT_ID = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
OUTER_WAIT_SECONDS = 180
KILL_CONFIRM_SECONDS = 5
CREATE_NO_WINDOW = 0x08000000
RESULT_LIMIT = 256 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_public_json(path: Path, limit: int = RESULT_LIMIT) -> dict[str, Any]:
    # This is called before launch or after a confirmed process exit only.
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("public record exceeds bound")
    value = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(value, dict):
        raise ValueError("public record must be an object")
    return value


def write_new(path: Path, record: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def error_kind(error: BaseException) -> dict[str, Any]:
    # Never serialize exception args, commands, environment values or raw tokens.
    return {"type": type(error).__name__, "errno": getattr(error, "errno", None),
            "winerror": getattr(error, "winerror", None)}


def child_environment(system_root: str, attempt: Path) -> dict[str, str]:
    if not system_root or not Path(system_root).is_absolute():
        raise ValueError("absolute SystemRoot required")
    profile = attempt / "controller-profile"
    return {"SystemRoot": system_root, "WINDIR": system_root,
            "PATH": str(Path(system_root) / "System32"), "USERPROFILE": str(profile),
            "LOCALAPPDATA": str(profile / "AppData" / "Local"),
            "APPDATA": str(profile / "AppData" / "Roaming"),
            "TEMP": str(attempt / "tmp"), "TMP": str(attempt / "tmp")}


@dataclass
class ManagedOutcome:
    record: dict[str, Any]
    # Retain the exact original Popen object/Windows process handle through
    # wait, bounded termination confirmation and receipt preparation.
    process: Any = field(repr=False, default=None)


def bounded_stop(process: Any, reason: str, original_error: BaseException) -> ManagedOutcome:
    record = {"status": "UNKNOWN", "reason": reason,
              "wait_error": error_kind(original_error), "kill_attempted": True,
              "termination_confirmed": False, "automatic_retry": False,
              "resource_ready": False, "reported_proof_complete": False}
    try:
        process.kill()  # Exact original Popen handle; no PID/name lookup.
    except BaseException as error:
        record["kill_error"] = error_kind(error)
    try:
        record["controller_exit_code"] = process.wait(timeout=KILL_CONFIRM_SECONDS)
        record["termination_confirmed"] = True
    except BaseException as error:
        record["confirmation_error"] = error_kind(error)
    # A timeout/error can never be upgraded using a later successful RESULT.
    return ManagedOutcome(record, process)


def run_child_once(env: dict[str, str], *, popen_factory: Callable[..., Any]) -> ManagedOutcome:
    argv = [str(CONTROLLER), "-execute", "-scope", str(R4_SCOPE),
            "-expected-scope-sha256", R4_SCOPE_SHA]
    process = None
    try:
        process = popen_factory(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, shell=False, close_fds=True,
                                creationflags=CREATE_NO_WINDOW, cwd=str(ROOT), env=env)
        # Handle acquisition and FIRST potentially blocking wait share this
        # protected region, including cancellation before wait begins.
        code = process.wait(timeout=OUTER_WAIT_SECONDS)
    except BaseException as error:
        if process is None:
            # No returned handle: outcome is uncertain. Never rediscover or retry.
            return ManagedOutcome({"status": "UNKNOWN", "reason": "POPEN_CONSTRUCTION_UNCERTAIN",
                                   "launch_error": error_kind(error), "automatic_retry": False,
                                   "resource_ready": False, "reported_proof_complete": False})
        reason = ("OUTER_TIMEOUT" if isinstance(error, subprocess.TimeoutExpired)
                  else "WAIT_EXCEPTION_OR_CANCELLATION")
        return bounded_stop(process, reason, error)
    return ManagedOutcome({"status": "CONTROLLER_EXITED_REQUIRES_RESULT_REVIEW",
                           "controller_exit_code": code, "termination_confirmed": True,
                           "kill_attempted": False, "automatic_retry": False,
                           "resource_ready": False, "reported_proof_complete": False}, process)


def complete_reported_proof(result: dict[str, Any]) -> bool:
    try:
        if result["status"] != "METADATA_VERIFIED_OWNED_JOB_CLOSED_ASSETS_UNCHANGED":
            return False
        for name in ("cleanup_proved", "streams_drained", "stage_a_assets_unchanged_after_stop"):
            if result[name] is not True:
                return False
        for name in ("controller_inference_requests", "paid_provider_requests", "old_root_writes", "formal_increment"):
            if type(result[name]) is not int or result[name] != 0:
                return False
        if result["counter_reset"] is not False or result["resource_ready"] is not False or result.get("error"):
            return False
        if result["metadata_get_attempts"] != {"/api/version": 1, "/api/tags": 1}:
            return False
        if any(type(v) is not int for v in result["metadata_get_attempts"].values()):
            return False
        kernel = result["kernel"]
        state, closed = kernel["State"], kernel["Close"]
        if kernel["CleanupProved"] is not True or kernel.get("Error"):
            return False
        if closed["JobClosed"] is not True or closed["PrimarySignaled"] is not True:
            return False
        if closed.get("Errors") not in (None, []) or state.get("Errors") not in (None, []):
            return False
        if type(state["Active"]) is not int or state["Active"] != 0 or state["Complete"] is not True:
            return False
        processes = state["Processes"]
        if type(state["Total"]) is not int or state["Total"] < 1 or len(processes) != state["Total"]:
            return False
        pids = set()
        for process in processes:
            if type(process["pid"]) is not int or process["pid"] < 1 or process["pid"] in pids:
                return False
            pids.add(process["pid"])
            if any(process[name] is not True for name in ("handle_held", "in_owned_job", "new_process_event", "signaled_after_cleanup")):
                return False
            ticks = process["creation_filetime_decimal"]
            if not isinstance(ticks, str) or not ticks.isascii() or not ticks.isdecimal() or int(ticks) <= 0:
                return False
        primary = kernel["Primary"]
        matching = [p for p in processes if p["pid"] == primary["pid"]]
        return (len(matching) == 1 and primary["handle_held"] is True
                and primary["in_owned_job"] is True
                and primary["creation_filetime_decimal"] == matching[0]["creation_filetime_decimal"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def classify_after_exit(outcome: ManagedOutcome, *, result_loader: Callable[[], dict[str, Any]]) -> None:
    record = outcome.record
    if record["status"] == "UNKNOWN":
        return  # Never read/promote RESULT after timeout or uncertain wait.
    if type(record.get("controller_exit_code")) is not int or record["controller_exit_code"] != 0:
        record.update(status="INCONCLUSIVE", reason="CONTROLLER_NONZERO_EXIT")
        return
    try:
        result = result_loader()
    except BaseException as error:
        record.update(status="INCONCLUSIVE", reason="RESULT_MISSING_OR_UNREADABLE",
                      result_error=error_kind(error))
        return
    if not complete_reported_proof(result):
        record.update(status="INCONCLUSIVE", reason="RESULT_PROOF_INCOMPLETE")
        return
    record.update(status="REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED",
                  reported_proof_complete=True, independent_acceptance=False)


def verify_prelaunch(manifest_pin: str, root_scope: Path, root_scope_pin: str) -> dict[str, Any]:
    if os.name != "nt" or Path(sys.executable).resolve() != PYTHON.resolve() or sha256(PYTHON) != PYTHON_SHA:
        raise ValueError("fixed Windows Python required")
    if sha256(ROOT / "MANIFEST.json") != manifest_pin:
        raise ValueError("reviewed supervisor manifest pin differs")
    manifest = read_public_json(ROOT / "MANIFEST.json")
    for item in manifest["files"]:
        path = (ROOT / item["relative"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or sha256(path) != item["sha256"]:
            raise ValueError("supervisor source/test/scope pin differs")
    for path, pin in ((CONTROLLER, CONTROLLER_SHA), (R4_SCOPE, R4_SCOPE_SHA), (REVIEW, REVIEW_SHA)):
        if sha256(path) != pin:
            raise ValueError("frozen R4/review pin differs")
    scope_pin = sha256(ROOT / "SCOPE.json")
    if not root_scope.resolve().is_relative_to(AUTHORIZATION_ROOT.resolve()) or sha256(root_scope) != root_scope_pin:
        raise ValueError("new public D Root scope and exact digest required")
    authorization = read_public_json(root_scope, 64 * 1024)
    expected = {"schema": "researchos.root-model-supervisor-authorization.v1", "actor": "codex:/root",
                "project_id": PROJECT_ID, "controller_sha256": CONTROLLER_SHA,
                "controller_scope_sha256": R4_SCOPE_SHA, "supervisor_manifest_sha256": manifest_pin,
                "supervisor_scope_sha256": scope_pin, "endpoint": ENDPOINT,
                "max_controller_launches": 1, "inference_limit": 0,
                "attempt_directory": str(ATTEMPT), "status": "ROOT_AUTHORIZED_ONCE_AFTER_REVIEW"}
    if any(authorization.get(key) != value for key, value in expected.items()):
        raise ValueError("Root authorization binding differs")
    if type(authorization.get("max_controller_launches")) is not int or type(authorization.get("inference_limit")) is not int:
        raise ValueError("Root authorization limits require exact integer types")
    revision = authorization.get("checkpoint_revision")
    if type(revision) is not int or revision <= 591 or authorization.get("checkpoint_sha256") != sha256(CHECKPOINT):
        raise ValueError("new Root checkpoint binding required")
    checkpoint = read_public_json(CHECKPOINT, 32 * 1024 * 1024)
    if checkpoint.get("revision") != revision or type(checkpoint.get("revision")) is not int or checkpoint.get("project_id") != PROJECT_ID:
        raise ValueError("current checkpoint revision/project differs from Root grant")
    if ATTEMPT.exists() or R4_RUN.exists():
        raise ValueError("one-use attempt/run already exists; readback required, no replay")
    return {"root_scope_sha256": root_scope_pin, "checkpoint_revision": revision,
            "checkpoint_sha256": authorization["checkpoint_sha256"],
            "supervisor_manifest_sha256": manifest_pin, "supervisor_scope_sha256": scope_pin}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--expected-manifest-sha256", default="")
    parser.add_argument("--root-scope", type=Path)
    parser.add_argument("--root-scope-sha256", default="")
    args = parser.parse_args()
    if not args.execute:
        print("PREPARED_NOT_AUTHORIZED_TO_RUN")
        return 0
    try:
        if args.root_scope is None:
            raise ValueError("Root D authorization required")
        binding = verify_prelaunch(args.expected_manifest_sha256, args.root_scope, args.root_scope_sha256)
        ATTEMPT.mkdir()  # Exclusive consumption before any child construction.
        env = child_environment(os.environ.get("SystemRoot", ""), ATTEMPT)
        for directory in (ATTEMPT / "tmp", ATTEMPT / "controller-profile" / "AppData" / "Local",
                          ATTEMPT / "controller-profile" / "AppData" / "Roaming"):
            directory.mkdir(parents=True, exist_ok=False)
        write_new(ATTEMPT / "CONSUMED.json", {"status": "CONSUMED_LAUNCH_OUTCOME_NOT_YET_KNOWN",
                  **binding, "controller_sha256": CONTROLLER_SHA, "controller_scope_sha256": R4_SCOPE_SHA,
                  "outer_wait_seconds": OUTER_WAIT_SECONDS, "kill_confirmation_seconds": KILL_CONFIRM_SECONDS,
                  "environment_keys_only": sorted(env), "automatic_retry": False})
    except BaseException as error:
        print(json.dumps({"status": "BLOCKED_OR_ALREADY_CONSUMED_READBACK_REQUIRED",
                          "error": error_kind(error), "resource_ready": False}))
        return 2
    outcome = run_child_once(env, popen_factory=subprocess.Popen)
    classify_after_exit(outcome, result_loader=lambda: read_public_json(R4_RUN / "RESULT.json"))
    outcome.record.update(binding, controller_sha256=CONTROLLER_SHA, controller_scope_sha256=R4_SCOPE_SHA,
                          outer_wait_seconds=OUTER_WAIT_SECONDS, kill_confirmation_seconds=KILL_CONFIRM_SECONDS,
                          formal_increment=0, counter_reset=False)
    try:
        # Child wait/termination is already finished. Reporting can never delay
        # the timeout/kill path or introduce a pipe/log join while it is active.
        write_new(ATTEMPT / "SUPERVISOR-RESULT.json", outcome.record)
    except BaseException as error:
        print(json.dumps({"status": "UNKNOWN_RECEIPT_WRITE", "error": error_kind(error),
                          "resource_ready": False, "automatic_retry": False}))
        return 3
    print(json.dumps({"status": outcome.record["status"], "resource_ready": False,
                      "automatic_retry": False, "formal_increment": 0}))
    return 0 if outcome.record["status"] == "REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
