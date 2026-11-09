"""One-shot byte-preserving replacement of only the W09 Go event validator."""
from __future__ import annotations

import ast
from pathlib import Path

P = Path(__file__).resolve().parent
target = P / "formal_profile_w09.after.py"
original = target.read_bytes()
start_marker = b"def _native_event_interval(api, raw, report, selected, label):\n"
end_marker = b"def _native(api, reader, row, closure, router, pinned, producer_sources):\n"
assert original.count(start_marker) == original.count(end_marker) == 1
start, end = original.index(start_marker), original.index(end_marker)
replacement = '''def _native_event_interval(api, raw, report, selected, label):
    """Bind each Go package and test lifecycle to pinned original JSONL order."""
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise api.InvalidEvidence("GO_EVENT_CLOCK", label + " UTF-8") from exc
    api.require(bool(lines), "GO_EVENT_CLOCK", label + " empty stream")
    events = [api.strict_json(line.encode("utf-8")) for line in lines]
    api.require(all(type(event) is dict for event in events), "GO_EVENT_CLOCK", label + " event shape")
    clocks = [api.stamp(event.get("Time"), label + " Go Time") for event in events]
    started, ended = api.interval(report, "native " + label)
    first, last = min(clocks), max(clocks)
    api.require(started <= first <= last <= ended, "GO_EVENT_CLOCK", label + " report/raw contradiction")

    packages = {}
    for position, (event, clock) in enumerate(zip(events, clocks)):
        package = event.get("Package")
        api.require(type(package) is str and package
                    and event.get("Action") in {"start", "run", "pause", "cont", "pass",
                                                "fail", "skip", "output", "bench"},
                    "GO_EVENT_TERMINAL", label + " event identity")
        test = event.get("Test")
        api.require(test is None or (type(test) is str and test),
                    "GO_EVENT_TERMINAL", label + " test identity")
        packages.setdefault(package, []).append((position, event, clock))
    api.require(bool(packages), "GO_EVENT_TERMINAL", label + " no package")

    selected_seen = set()
    for package, rows in packages.items():
        package_events = [(i, event, clock) for i, event, clock in rows if not event.get("Test")]
        starts = [row for row in package_events if row[1]["Action"] == "start"]
        terminals = [row for row in package_events
                     if row[1]["Action"] in {"pass", "fail", "skip"}]
        api.require(len(starts) == len(terminals) == 1
                    and terminals[0][1]["Action"] == "pass",
                    "GO_EVENT_TERMINAL", label + " " + package + " package endpoints")
        start_row, terminal_row = starts[0], terminals[0]
        api.require(start_row[0] < terminal_row[0]
                    and start_row[2] <= terminal_row[2]
                    and rows[0][0] == start_row[0] and rows[-1][0] == terminal_row[0]
                    and all(start_row[0] <= i <= terminal_row[0]
                            and start_row[2] <= clock <= terminal_row[2]
                            for i, _event, clock in rows)
                    and all(left[2] <= right[2] for left, right in zip(rows, rows[1:])),
                    "GO_EVENT_TERMINAL", label + " " + package + " lifecycle")

        tests = {}
        for row in rows:
            test = row[1].get("Test")
            if test:
                tests.setdefault(test, []).append(row)
        for test, test_rows in tests.items():
            runs = [row for row in test_rows if row[1]["Action"] == "run"]
            terminal_tests = [row for row in test_rows
                              if row[1]["Action"] in {"pass", "fail", "skip"}]
            api.require(len(runs) == len(terminal_tests) == 1
                        and terminal_tests[0][1]["Action"] == "pass",
                        "GO_EVENT_TERMINAL", label + " " + package + " " + test + " endpoints")
            run_row, pass_row = runs[0], terminal_tests[0]
            api.require(start_row[0] < run_row[0] < pass_row[0] < terminal_row[0]
                        and start_row[2] <= run_row[2] <= pass_row[2] <= terminal_row[2]
                        and test_rows[0][0] == run_row[0]
                        and test_rows[-1][0] == pass_row[0]
                        and all(run_row[0] <= i <= pass_row[0]
                                and run_row[2] <= clock <= pass_row[2]
                                for i, _event, clock in test_rows),
                        "GO_EVENT_TERMINAL", label + " " + package + " " + test + " lifecycle")
            if test in selected:
                api.require(test not in selected_seen, "GO_EVENT_TERMINAL",
                            label + " duplicate selected test " + test)
                selected_seen.add(test)
    api.require(selected_seen == set(selected)
                and len(selected) == len(set(selected)),
                "GO_EVENT_TERMINAL", label + " selected test ownership")
    return first.isoformat(), last.isoformat()


'''.encode("utf-8")
candidate = original[:start] + replacement + original[end:]
ast.parse(candidate, filename=str(target))
assert candidate[:start] == original[:start]
assert candidate[start + len(replacement):] == original[end:]
assert target.read_bytes() == original
target.write_bytes(candidate)
assert target.read_bytes() == candidate
print("W09_V4_NATIVE_EVENT_LIFECYCLE_AST_PASS")
