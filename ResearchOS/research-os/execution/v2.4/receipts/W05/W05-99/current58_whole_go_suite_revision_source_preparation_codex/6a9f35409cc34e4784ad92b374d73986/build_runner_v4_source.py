"""Exclusive final runner revision; static transform only."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
source = (here / "whole58_finite_runner.v3.proposed.py").read_text(encoding="utf-8")

def sub(old, new):
    global source
    if source.count(old) != 1:
        raise SystemExit("runner v4 source anchor mismatch")
    source = source.replace(old, new)

sub('''def one_time_json(path, value):
    with path.open("xb") as stream:
        stream.write(encode_json(value))
''', '''def one_time_json(path, value):
    with path.open("xb") as stream:
        stream.write(encode_json(value))


def bounded_json(path, value, deadline):
    """Return only after final IO, or leave a partial receipt and fail closed."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("FINAL_IO_DEADLINE_EXHAUSTED")
    errors = []
    def writer():
        try: one_time_json(path, value)
        except BaseException as exc: errors.append(repr(exc))
    worker = threading.Thread(target=writer, daemon=True)
    worker.start()
    worker.join(timeout=remaining)
    if worker.is_alive():
        raise TimeoutError("FINAL_IO_INCOMPLETE_RAW_MAY_BE_PARTIAL")
    if errors:
        raise OSError("FINAL_IO_FAILURE:" + errors[0])
''')
sub('''        try: one_time_json(out_dir / "invocation.json", receipt)
''', '''        try: bounded_json(out_dir / "invocation.json", receipt,
                          deadline - budgets["finalization_reserve_seconds"])
''')
sub('''        if len(package_terminals) != 1 or package_terminals[0] != "pass":
            raise ValueError("PACKAGE_TERMINAL_NOT_SINGLE_PASS")
''', '''        if len(package_terminals) != 1 or (package_terminals[0] != "pass" and
                not (build_only and package_terminals[0] == "skip" and not terminal)):
            raise ValueError("PACKAGE_TERMINAL_NOT_SINGLE_PASS_OR_BUILD_ONLY")
''')
sub('''        report["planned_primary_go_calls"] = len(authority["planned_invocations"])
''', '''        report["planned_primary_go_calls"] = len(authority["planned_invocations"])
        selected_ids = sorted(test_id for package in finite["packages"]
                              for lane in authority["lanes"]
                              for test_id in package["lanes"].get(lane, {}).get("test_ids", []))
        report["planned_selected_test_count"] = len(selected_ids)
        report["planned_selected_test_ids"] = selected_ids
        report["observed_passed_test_count"] = 0
        report["all_platform_top_test_count_source_only"] = finite["all_platform_top_tests"]
''')
sub('''                unit["lanes"].append({"lane": lane, "state": "EXECUTED",
                                      "invocation": receipt, "outcome": outcome})
''', '''                unit["lanes"].append({"lane": lane, "state": "EXECUTED",
                                      "invocation": receipt, "outcome": outcome})
                if outcome["candidate_pass"]:
                    report["observed_passed_test_count"] += len(outcome["passed"])
''')
sub('''        if report["actual_primary_go_calls"] != report["planned_primary_go_calls"]:
            raise ValueError("INCOMPLETE_FINITE_PLAN")
''', '''        if report["actual_primary_go_calls"] != report["planned_primary_go_calls"]:
            raise ValueError("INCOMPLETE_FINITE_PLAN")
        if report["observed_passed_test_count"] != report["planned_selected_test_count"]:
            raise ValueError("INCOMPLETE_SELECTED_TEST_COVERAGE")
''')
sub('''                one_time_json(output / "report.json", report)
''', '''                bounded_json(output / "report.json", report, deadline)
''')
sub('''                one_time_json(output / "terminal.json", completion)
''', '''                bounded_json(output / "terminal.json", completion, deadline)
''')
with (here / "whole58_finite_runner.v4.proposed.py").open("xb") as stream:
    stream.write(source.encode("utf-8"))
print("exclusive runner v4 source created")
