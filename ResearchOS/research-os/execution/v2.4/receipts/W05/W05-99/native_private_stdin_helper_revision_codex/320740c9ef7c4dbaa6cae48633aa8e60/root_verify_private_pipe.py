"""Root-invoked tests. Importing creates no process and performs no native call.

All stdin bytes below are fixed PUBLIC dummy values, never real credentials.
Root must pin this file, probe, helper, Python/DLL inventory and owned output root
before explicitly running the test. This is no production acceptance gate.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("one fresh absolute output-directory argument required")
    output = Path(sys.argv[1])
    if not output.is_absolute() or output.exists():
        raise SystemExit("output must be a fresh absolute directory")
    output.mkdir(parents=False, exist_ok=False)
    helper_path = Path(__file__).with_name("windows_owned_private_stdin.py")
    spec = importlib.util.spec_from_file_location("owned_private_stdin_source", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    probe = Path(__file__).with_name("private_pipe_public_probe.py")
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    env["PYTHONUTF8"] = "1"
    results = []
    for mode in ("normal", "maximum", "reject", "timeout"):
        data = bytearray(b"A" * 4096 if mode == "maximum" else b"PUBLIC_DUMMY_PRIVATE_PIPE_TEST")
        with (output / (mode + ".stdout.raw")).open("xb") as stdout, (output / (mode + ".stderr.raw")).open("xb") as stderr:
            receipt = helper.run_owned_private_stdin(
                [sys.executable, "-I", "-S", "-B", "-X", "utf8", str(probe), mode], str(probe.parent), env,
                stdout, stderr, 1.5 if mode == "timeout" else 15.0,
                data, creation_flags=0x08000000)
        closed = receipt["job_cleanup"]
        pipe = receipt["private_stdin"]
        ok = (not any(data) and pipe["input_buffer_cleared"]
              and pipe["anonymous_pipe"] and pipe["file_type_pipe_verified"]
              and pipe["complete_input_written"] and pipe["writer_closed_before_launch"]
              and pipe["capacity_verified"] and pipe["empty_before_write"]
              and pipe["effective_capacity"] >= len(data)
              and pipe["write_deadline_checked_before_and_after"]
              and closed["assigned_before_resume"] and closed["kill_on_job_close_configured"]
              and closed["primary_exit_confirmed"] and closed["job_idle_confirmed"]
              and closed["active_processes_last_observed"] == 0
              and closed["handles_closed"] and not closed["errors"] and receipt["error"] is None)
        if mode == "timeout":
            ok = ok and receipt["timed_out"] and closed["termination_requested"] and closed["termination_succeeded"]
        else:
            ok = ok and not receipt["timed_out"] and receipt["actual_exit"] == (7 if mode == "reject" else 0)
            raw = (output / (mode + ".stdout.raw")).read_bytes()
            observed = json.loads(raw)
            ok = ok and observed["file_type_pipe"] and observed["read_all_reached_eof"] and observed["expected_public_input_matched"]
        entry = {"case": mode, "passed": bool(ok), "result": receipt}
        (output / (mode + ".invocation.json")).write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        results.append(entry)
        if not ok:
            break
    if all(item["passed"] for item in results):
        for name, data in (("empty", bytearray()), ("oversize", bytearray(b"A" * 4097))):
            with (output / (name + ".stdout.raw")).open("xb") as stdout, (output / (name + ".stderr.raw")).open("xb") as stderr:
                receipt = helper.run_owned_private_stdin(
                    [sys.executable, "-I", "-S", "-B", "-X", "utf8", str(probe), "normal"], str(probe.parent), env,
                    stdout, stderr, 15.0, data, creation_flags=0x08000000)
            ok = (receipt["actual_exit"] is None and receipt["owned_child_pid"] is None
                  and not receipt["resumed"] and receipt["error"] is not None
                  and not any(data) and receipt["private_stdin"]["input_buffer_cleared"]
                  and receipt["job_cleanup"]["handles_closed"])
            entry = {"case": name, "passed": bool(ok), "result": receipt}
            (output / (name + ".invocation.json")).write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
            results.append(entry)
            if not ok:
                break
    complete = len(results) == 6 and all(item["passed"] for item in results)
    (output / "validation.closed.json").write_text(json.dumps(
        {"status": "PUBLIC_PIPE_TESTS_PASSED" if complete else "FAILED_CLOSED_REVIEW_REQUIRED",
         "scope": "PUBLIC_DUMMY_INPUT_ONLY", "native_authority_positive": False,
         "provider_requests": 0, "production_db_writes": 0, "results": results},
        indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_directory": str(output), "all_cases_passed": complete,
                      "native_authority_positive": False}))
    return 0 if complete else 1

if __name__ == "__main__":
    raise SystemExit(main())

