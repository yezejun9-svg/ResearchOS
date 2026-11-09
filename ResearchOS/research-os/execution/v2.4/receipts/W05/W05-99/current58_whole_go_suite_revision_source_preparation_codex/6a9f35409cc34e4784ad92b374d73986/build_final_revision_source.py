"""One-shot superseding static source transform, with exclusive outputs."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent

def revised(name, output, substitutions):
    source = (HERE / name).read_text(encoding="utf-8")
    for old, new in substitutions:
        if source.count(old) != 1:
            raise SystemExit("non-unique revision anchor: " + old[:70])
        source = source.replace(old, new)
    with (HERE / output).open("xb") as stream:
        stream.write(source.encode("utf-8"))

revised("whole58_gate.v2.proposed.py", "whole58_gate.v3.proposed.py", [
    ('''    require(scope.get("finite_contract_ref") == pin_file(finite_path)
            and scope.get("runner_ref") == pin_file(runner_path)
            and scope.get("gate_ref") == pin_file(gate_path), "RUNNER_GATE_CONTRACT_NOT_PINNED")
''', '''    require(scope.get("finite_contract_ref") == pin_file(finite_path)
            and scope.get("runner_ref") == pin_file(runner_path)
            and scope.get("gate_ref") == pin_file(gate_path), "RUNNER_GATE_CONTRACT_NOT_PINNED")
    _, source_manifest = read_pin(scope.get("source_manifest_ref"))
    require(source_manifest.get("schema") == "researchos.current58-whole-go-source-preparation-manifest.v1"
            and all(pin_file(path) in source_manifest.get("members", [])
                    for path in (runner_path, gate_path, execution_path, finite_path)),
            "CURRENT_SOURCE_MANIFEST_NOT_CLOSED")
'''),
    ('''            and registration.get("owner") == scope.get("owner"), "ACTUAL_ROOT_REGISTRATION_MISMATCH")
''', '''            and registration.get("owner") == scope.get("owner")
            and registration.get("source_manifest_ref") == scope["source_manifest_ref"],
            "ACTUAL_ROOT_REGISTRATION_MISMATCH")
'''),
    ('''            and review.get("finite_contract_ref") == scope["finite_contract_ref"],
''', '''            and review.get("finite_contract_ref") == scope["finite_contract_ref"]
            and review.get("source_manifest_ref") == scope["source_manifest_ref"],
'''),
    ('''            and grant.get("runtime_catalog_ref") == scope["runtime_catalog_ref"]
''', '''            and grant.get("runtime_catalog_ref") == scope["runtime_catalog_ref"]
            and grant.get("source_manifest_ref") == scope["source_manifest_ref"]
'''),
    ('''            "grant_ref": auth["grant_ref"], "tree": tree,
''', '''            "grant_ref": auth["grant_ref"], "tree": tree,
            "source_manifest_ref": scope["source_manifest_ref"],
'''),
    ('''    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref", "grant_ref"):
''', '''    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref", "grant_ref", "source_manifest_ref"):
'''),
])

revised("whole58_finite_runner.v2.proposed.py", "whole58_finite_runner.v3.proposed.py", [
    ('GATE = Path(__file__).with_name("whole58_gate.v2.proposed.py")',
     'GATE = Path(__file__).with_name("whole58_gate.v3.proposed.py")'),
    ('''        report["candidate_suite_pass"] = True
''', '''        report["provisional_workload_pass"] = True
        report["candidate_suite_pass"] = False
'''),
    ('''    except BaseException as exc:
        report["first_cause"] = repr(exc)
        report["candidate_suite_pass"] = False
    finally:
''', '''    except BaseException as exc:
        report["first_cause"] = repr(exc)
        report["provisional_workload_pass"] = False
        report["candidate_suite_pass"] = False
    finally:
'''),
    ('''        if output is not None:
            try:
                one_time_json(output / "report.json", report)
            except BaseException as exc:
                report["secondary_causes"].append("REPORT_WRITE_FAILURE:" + repr(exc))
                report["candidate_suite_pass"] = False
        else:
            # Root caller retains stdout/stderr and actual exit on preflight failure.
            sys.stderr.write(encode_json(report).decode("utf-8"))
    return 0 if report["candidate_suite_pass"] else 1
''', '''        report_written = False
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
'''),
    ('''            "actual_primary_go_calls": 0,
''', '''            "actual_primary_go_calls": 0,
'''),
])
print("exclusive superseding gate and runner sources created")
