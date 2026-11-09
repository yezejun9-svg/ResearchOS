"""Finite current58 Go runner revision; candidate until Root registration and review.

No Go process may start before whole58_gate.v2 validates exact future authority.
An outer Windows Job and separately witnessed meters must remain live. Every
local invocation is finite, singular, and recorded even after BaseException.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[7]
FINITE = ROOT / "execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_source_preparation_codex/bbeb0e9d8d1b4c8fb367a5c45d80adea/whole58-finite.contract.proposed.json"
EXECUTION = Path(__file__).with_name("whole58-execution.contract.proposed.json")
GATE = Path(__file__).with_name("whole58_gate.v3.proposed.py")

def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": sha(data), "bytes": len(data)}


def pinned_file(claim):
    if not isinstance(claim, dict) or set(claim) != {"path", "sha256", "bytes"}:
        raise ValueError("MALFORMED_PIN")
    path = Path(claim["path"])
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise ValueError("PIN_PATH_NOT_ABSOLUTE_REGULAR")
    actual = pin(path)
    if actual != claim:
        raise ValueError("PIN_DRIFT")
    return path


def source_closure(contract, catalog):
    if catalog.get("commit") != contract["source_commit"] or catalog.get("file_count") != 639:
        raise ValueError("SOURCE_CATALOG_TUPLE_CHANGED")
    files = catalog.get("files")
    if not isinstance(files, list) or len(files) != 639:
        raise ValueError("PUBLIC_SOURCE_MEMBERSHIP_CHANGED")
    seen = set()
    for entry in files:
        relative = entry["path"]
        path = (ROOT / relative).resolve(strict=True)
        if ROOT not in path.parents or relative in seen or not path.is_file() or path.is_symlink():
            raise ValueError("SOURCE_FOREIGN_OR_DUPLICATE")
        seen.add(relative)
        data = path.read_bytes()
        if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
            raise ValueError("SOURCE_BYTES_CHANGED")
    return len(seen)



def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def one_time_json(path, value):
    with path.open("xb") as stream:
        stream.write(encode_json(value))


def load_gate():
    spec = importlib.util.spec_from_file_location("whole58_gate_future", GATE)
    if spec is None or spec.loader is None:
        raise ValueError("PINNED_GATE_LOAD_OPEN")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def guarded_wall(budgets, deadline):
    reserve = (budgets["cleanup_reserve_seconds"] +
               budgets["finalization_reserve_seconds"] +
               budgets["io_reserve_seconds"])
    remaining = deadline - time.monotonic() - reserve
    if remaining <= 0:
        raise TimeoutError("TOTAL_WALL_DEADLINE_BEFORE_LAUNCH")
    return min(budgets["per_invocation_wall_seconds"], remaining)


def run_one(call, argv, cwd, env, out_dir, deadline, budgets, gate, authority):
    """One child; bounded cleanup; null raw pin until drain fully completes."""
    gate.recheck_before_launch(ROOT, authority)
    wall = guarded_wall(budgets, deadline)
    out_dir.mkdir(parents=True, exist_ok=False)
    raw_paths = {"stdout": out_dir / "stdout.raw", "stderr": out_dir / "stderr.raw"}
    started = time.monotonic()
    receipt = {"call": call, "argv": argv, "cwd": str(cwd),
               "environment_names": sorted(env), "started_monotonic": started,
               "timeout_seconds": wall, "actual_exit": None, "stdout": None,
               "stderr": None, "stdout_overflow": False, "stderr_overflow": False,
               "timed_out": False, "drain_incomplete": False, "first_cause": None,
               "secondary_causes": [], "automatic_retry": False,
               "counter_reset": False, "candidate_pass": False,
               "os_child_tree_lifecycle_qualification": False}
    proc = None
    workers = []
    drain_done = {"stdout": False, "stderr": False}
    def fail(code, detail=None):
        item = {"code": code, "detail": detail}
        if receipt["first_cause"] is None:
            receipt["first_cause"] = item
        else:
            receipt["secondary_causes"].append(item)
    def drain(pipe, label, cap):
        count = 0
        try:
            with raw_paths[label].open("xb") as stream:
                while True:
                    chunk = os.read(pipe.fileno(), 65536)
                    if not chunk:
                        break
                    kept = min(len(chunk), max(0, cap - count))
                    if kept:
                        stream.write(chunk[:kept])
                        count += kept
                    if kept < len(chunk):
                        receipt[label + "_overflow"] = True
                        if proc is not None:
                            proc.kill()
                        break
        except BaseException as exc:
            fail("RAW_DRAIN_FAILURE", label + ":" + repr(exc))
            if proc is not None:
                try: proc.kill()
                except BaseException as kill_exc:
                    fail("KILL_AFTER_DRAIN_FAILURE", repr(kill_exc))
        finally:
            drain_done[label] = True
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, shell=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        for label in ("stdout", "stderr"):
            worker = threading.Thread(target=drain,
                                      args=(getattr(proc, label), label,
                                            budgets[label + "_bytes"]), daemon=True)
            workers.append(worker)
            worker.start()
        proc.wait(timeout=max(0.001, min(wall, deadline-time.monotonic()-
                                        budgets["cleanup_reserve_seconds"]-
                                        budgets["finalization_reserve_seconds"])))
    except subprocess.TimeoutExpired as exc:
        receipt["timed_out"] = True
        fail("INVOCATION_WALL_TIMEOUT", repr(exc))
    except BaseException as exc:
        fail("INVOCATION_EXCEPTION", repr(exc))
    finally:
        if proc is not None:
            if proc.poll() is None:
                try: proc.kill()
                except BaseException as exc: fail("KILL_FAILURE", repr(exc))
                try:
                    proc.wait(timeout=max(0.001, min(budgets["kill_wait_seconds"],
                               deadline-time.monotonic()-budgets["finalization_reserve_seconds"])))
                except BaseException as exc: fail("KILL_WAIT_FAILURE", repr(exc))
            receipt["actual_exit"] = proc.poll()
        for worker in workers:
            worker.join(timeout=max(0, min(budgets["drain_join_seconds"],
                        deadline-time.monotonic()-budgets["finalization_reserve_seconds"])))
        receipt["drain_incomplete"] = len(workers) != 2 or any(w.is_alive() for w in workers)
        if receipt["drain_incomplete"]:
            fail("RAW_DRAIN_INCOMPLETE")
        for label in ("stdout", "stderr"):
            if drain_done[label] and not receipt["drain_incomplete"] and raw_paths[label].is_file():
                try: receipt[label] = pin(raw_paths[label])
                except BaseException as exc: fail("RAW_PIN_FAILURE", label + ":" + repr(exc))
        receipt["ended_monotonic"] = time.monotonic()
        if receipt["ended_monotonic"] >= deadline-budgets["finalization_reserve_seconds"]:
            fail("TOTAL_DEADLINE_FINALIZATION_RESERVE")
        try: one_time_json(out_dir / "invocation.json", receipt)
        except BaseException as exc: fail("INVOCATION_RECEIPT_WRITE_FAILURE", repr(exc))
    return receipt


def strict_events(receipt, expected_package):
    if receipt["stdout"] is None:
        raise ValueError("UNPINNED_GO_JSON_RAW")
    events = []
    raw = Path(receipt["stdout"]["path"]).read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("INCOMPLETE_GO_JSON_STREAM")
    for line in raw.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict) or event.get("Package") != expected_package:
            raise ValueError("GO_JSON_PACKAGE_IDENTITY_MISMATCH")
        events.append(event)
    return events


def evaluate_run(receipt, selected, build_only, package):
    result = {"candidate_pass": False, "selected": list(selected), "passed": [],
              "missing": list(selected), "unexpected": [], "skipped": [],
              "package_pass": False, "build_only": build_only,
              "actual_exit": receipt["actual_exit"], "first_cause": None}
    if receipt["first_cause"] or receipt["actual_exit"] != 0 or not receipt["stdout"]:
        result["first_cause"] = "INVOCATION_NOT_CLOSED"
        return result
    try:
        events = strict_events(receipt, "researchos.local/research-os/" + package)
        terminal = {}
        package_terminals = []
        for event in events:
            action = event.get("Action")
            name = event.get("Test")
            if action not in {"start", "run", "pause", "cont", "pass", "fail", "skip", "output"}:
                raise ValueError("UNKNOWN_GO_JSON_ACTION")
            if name and action in {"pass", "fail", "skip"}:
                if name in terminal: raise ValueError("DUPLICATE_TEST_TERMINAL")
                terminal[name] = action
            if not name and action in {"pass", "fail", "skip"}:
                package_terminals.append(action)
        if len(package_terminals) != 1 or package_terminals[0] != "pass":
            raise ValueError("PACKAGE_TERMINAL_NOT_SINGLE_PASS")
        top = {name: status for name, status in terminal.items() if "/" not in name}
        if any(status != "pass" for status in terminal.values()):
            raise ValueError("GO_TEST_FAIL_OR_SKIP")
        result["unexpected"] = sorted(set(top)-set(selected))
        result["missing"] = sorted(set(selected)-set(top))
        result["passed"] = sorted(name for name in selected if top.get(name) == "pass")
        result["skipped"] = sorted(name for name, status in terminal.items() if status == "skip")
        if build_only and terminal:
            raise ValueError("BUILD_ONLY_RAN_TEST")
        result["package_pass"] = True
        result["candidate_pass"] = not result["unexpected"] and not result["missing"]
    except BaseException as exc:
        result["first_cause"] = repr(exc)
    return result


def list_names(receipt):
    if receipt["first_cause"] or receipt["actual_exit"] != 0 or not receipt["stdout"]:
        return None
    raw = Path(receipt["stdout"]["path"]).read_text(encoding="utf-8", errors="strict")
    return sorted({line.strip() for line in raw.splitlines()
                   if re.fullmatch(r"Test\w+", line.strip())})


def main(argv):
    phase_started = time.monotonic()
    if len(argv) != 5:
        raise SystemExit("usage: runner SCOPE_PATH SCOPE_SHA AUTH_PATH AUTH_SHA")
    report = {"schema": "researchos.current58-go-run-facts.v2", "qualified": False,
              "source_acceptance": False, "formal_case_accepted_delta": 0,
              "model_lane_executed": False, "model_cost_usd": None,
              "os_child_tree_lifecycle_qualification": False,
              "nested_process_and_http_cap_qualification": False,
              "external_effect_zero": None, "actual_runtime_control": None,
              "first_cause": None, "secondary_causes": [], "packages": [],
              "planned_primary_go_calls": None, "actual_primary_go_calls": 0,
              "source_closure_before": None, "source_closure_after": None,
              "phase_started_monotonic": phase_started, "phase_ended_monotonic": None}
    output = None
    deadline = None
    authority = None
    try:
        gate = load_gate()
        scope_ref = {"path": argv[1], "sha256": argv[2],
                     "bytes": Path(argv[1]).stat().st_size}
        auth_ref = {"path": argv[3], "sha256": argv[4],
                    "bytes": Path(argv[3]).stat().st_size}
        authority = gate.validate(ROOT, Path(__file__).resolve(), GATE, FINITE,
                                  EXECUTION, scope_ref, auth_ref, phase_started)
        output = authority["output"]
        budgets = authority["budgets"]
        deadline = phase_started + budgets["total_wall_seconds"]
        finite = authority["finite"]
        catalog_path = gate.check_pin(authority["source_catalog_ref"])
        catalog = gate.strict_json(catalog_path.read_bytes())
        report["source_closure_before"] = source_closure(finite, catalog)
        report["scope_ref"] = scope_ref
        report["authority_ref"] = auth_ref
        report["planned_primary_go_calls"] = len(authority["planned_invocations"])
        env = authority["env"]
        go_path = authority["go_path"]
        calls = authority["planned_invocations"]
        for package in finite["packages"]:
            path = package["directory"]
            package_out = output / path.replace("/", "__")
            package_out.mkdir(parents=True, exist_ok=False)
            expected = sorted({name for lane in package["lanes"].values()
                               for name in lane["windows_candidate_names"]})
            call = calls[report["actual_primary_go_calls"]]
            if call["kind"] != "list" or call["package"] != path:
                raise ValueError("FINITE_CALL_ORDER_DRIFT")
            receipt = run_one(call, [str(go_path), "test", "-list", ".", package["import_arg"]],
                              ROOT, env, package_out / "list", deadline, budgets, gate, authority)
            report["actual_primary_go_calls"] += 1
            actual_names = list_names(receipt)
            roster_ok = actual_names == expected
            unit = {"package": path, "list_invocation": receipt,
                    "expected_windows_source_names": expected,
                    "actual_listed_names": actual_names, "roster_reconciled": roster_ok,
                    "lanes": []}
            report["packages"].append(unit)
            if not roster_ok: raise ValueError("TARGET_ROSTER_NOT_EXACT")
            for lane in authority["lanes"]:
                entry = package["lanes"].get(lane)
                if entry is None or (not entry["windows_candidate_names"]
                                     and lane != "BUILD_ONLY_NO_TOP_TEST"):
                    unit["lanes"].append({"lane": lane, "state": "NOT_APPLICABLE"})
                    continue
                call = calls[report["actual_primary_go_calls"]]
                if call["kind"] != "lane" or call["package"] != path or call["lane"] != lane:
                    raise ValueError("FINITE_LANE_CALL_ORDER_DRIFT")
                wall = guarded_wall(budgets, deadline)
                timeout = str(max(1, int(wall))) + "s"
                command = [str(go_path), "test", "-json", "-count=1", "-run",
                           entry["exact_top_regex"], "-timeout", timeout, package["import_arg"]]
                receipt = run_one(call, command, ROOT, env, package_out / lane,
                                  deadline, budgets, gate, authority)
                report["actual_primary_go_calls"] += 1
                outcome = evaluate_run(receipt, entry["windows_candidate_names"],
                                       lane == "BUILD_ONLY_NO_TOP_TEST", path)
                unit["lanes"].append({"lane": lane, "state": "EXECUTED",
                                      "invocation": receipt, "outcome": outcome})
                if not outcome["candidate_pass"]: raise ValueError("GO_LANE_DID_NOT_PASS")
        report["source_closure_after"] = source_closure(finite, catalog)
        if report["actual_primary_go_calls"] != report["planned_primary_go_calls"]:
            raise ValueError("INCOMPLETE_FINITE_PLAN")
        if time.monotonic() >= deadline - budgets["finalization_reserve_seconds"]:
            raise TimeoutError("FINALIZATION_RESERVE_EXHAUSTED")
        report["provisional_workload_pass"] = True
        report["candidate_suite_pass"] = False
    except BaseException as exc:
        report["first_cause"] = repr(exc)
        report["provisional_workload_pass"] = False
        report["candidate_suite_pass"] = False
    finally:
        report["phase_ended_monotonic"] = time.monotonic()
        if deadline is not None and report["phase_ended_monotonic"] >= deadline:
            report["secondary_causes"].append("ABSOLUTE_TOTAL_DEADLINE_EXCEEDED")
            report["candidate_suite_pass"] = False
        report_written = False
        if output is not None:
            try:
                one_time_json(output / "report.json", report)
                report_written = True
            except BaseException as exc:
                report["secondary_causes"].append("REPORT_WRITE_FAILURE:" + repr(exc))
        else:
            # Root caller retains stdout/stderr and actual exit on preflight failure.
            sys.stderr.write(encode_json(report).decode("utf-8"))
        # A file written before this check is deliberately provisional, never a PASS.
        final_tick = time.monotonic()
        within_deadline = deadline is not None and final_tick < deadline
        if output is not None:
            completion = {"schema": "researchos.current58-whole-go-provisional-terminal.v1",
                          "workload_pass": report.get("provisional_workload_pass") is True,
                          "report_written": report_written,
                          "after_report_monotonic": final_tick,
                          "within_absolute_deadline": within_deadline,
                          "source_acceptance": False, "formal_case_accepted_delta": 0}
            try:
                one_time_json(output / "terminal.json", completion)
            except BaseException as exc:
                report["secondary_causes"].append("TERMINAL_WRITE_FAILURE:" + repr(exc))
                report_written = False
        report["candidate_suite_pass"] = (report.get("provisional_workload_pass") is True
                                          and report_written and within_deadline
                                          and deadline is not None and time.monotonic() < deadline)
    return 0 if report["candidate_suite_pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
