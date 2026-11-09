"""Add pinned F2 lifecycle counterexamples and legal parallel-package control."""
from __future__ import annotations

import ast
from pathlib import Path

P = Path(__file__).resolve().parent
profile_path = P / "formal_profile_w09.after.py"
controls_path = P / "source_controls_v4.py"
profile = profile_path.read_bytes()
controls = controls_path.read_bytes()

old = b'        for test, test_rows in tests.items():\n'
new = (b'        api.require(any(test in selected for test in tests),\n'
       b'                    "GO_EVENT_TERMINAL", label + " " + package + " unmatched package")\n'
       + old)
assert profile.count(old) == 1
profile_candidate = profile.replace(old, new, 1)

needle = b'future_dispatch = {key: dict(value) for key, value in routes.items()}\n'
assert controls.count(needle) == 1
extra = '''# F2-terminal: replay the exact sealed v3r2 impossible package completion.
terminal_example = (R / "execution/v2.4/receipts/W09/W09-99/"
                    "w09_formal_profile_v3_independent_review_codex/profv3r2-01a12c09/"
                    "native-terminal-counterexample.json")
terminal_raw = terminal_example.read_bytes()
assert len(terminal_raw) == 2283 and hashlib.sha256(terminal_raw).hexdigest() == (
    "42f0b4fca7852be62f87454e4a62cf69a34b32541958d1645e583f7ead9a867c")
terminal_case = json.loads(terminal_raw)
terminal_stream = b"".join((json.dumps(event) + "\\n").encode("utf-8")
                           for event in terminal_case["raw_jsonl_events"])
reject("F2_EXACT_V3R2_PACKAGE_PASS_BEFORE_TEST_REJECTED",
       lambda: profile["_native_event_interval"](
           api, terminal_stream, terminal_case["report"], terminal_case["selected_tests"],
           "synthetic"), "GO_EVENT_TERMINAL")

def stream(events):
    return b"".join((json.dumps(event) + "\\n").encode("utf-8") for event in events)

valid = [
    {"Time": "2026-10-01T00:00:00Z", "Action": "start", "Package": "example/p"},
    {"Time": "2026-10-01T00:00:01Z", "Action": "run", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-01T00:00:02Z", "Action": "pass", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-01T00:00:03Z", "Action": "pass", "Package": "example/p"},
]
assert profile["_native_event_interval"](api, stream(valid), go_report,
                                          ["TestW09Synthetic"], "synthetic")
checks.append("F2_SINGLE_PACKAGE_LIFECYCLE_ACCEPTED_SYNTHETIC")
duplicate_terminal = valid + [{"Time": "2026-10-01T00:00:04Z", "Action": "pass", "Package": "example/p"}]
reject("F2_DUPLICATE_PACKAGE_TERMINAL_REJECTED", lambda: profile["_native_event_interval"](
    api, stream(duplicate_terminal), go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")
conflicting_terminal = valid + [{"Time": "2026-10-01T00:00:04Z", "Action": "fail", "Package": "example/p"}]
reject("F2_CONFLICTING_PACKAGE_TERMINAL_REJECTED", lambda: profile["_native_event_interval"](
    api, stream(conflicting_terminal), go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")
late_unselected = valid + [{"Time": "2026-10-01T00:00:04Z", "Action": "output",
                            "Package": "example/p", "Test": "TestW09Foreign", "Output": "synthetic"}]
reject("F2_UNSELECTED_EVENT_AFTER_PACKAGE_TERMINAL_REJECTED",
       lambda: profile["_native_event_interval"](
           api, stream(late_unselected), go_report, ["TestW09Synthetic"], "synthetic"),
       "GO_EVENT_TERMINAL")
pass_before_run = [dict(item) for item in valid]
pass_before_run[1]["Action"], pass_before_run[2]["Action"] = "pass", "run"
reject("F2_TEST_PASS_BEFORE_RUN_REJECTED", lambda: profile["_native_event_interval"](
    api, stream(pass_before_run), go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")
late_test_output = valid[:3] + [{"Time": "2026-10-01T00:00:02.500000Z", "Action": "output",
                                 "Package": "example/p", "Test": "TestW09Synthetic", "Output": "late"}] + valid[3:]
reject("F2_TEST_OUTPUT_AFTER_TEST_TERMINAL_REJECTED", lambda: profile["_native_event_interval"](
    api, stream(late_test_output), go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")
unmatched = valid + [
    {"Time": "2026-10-01T00:00:00Z", "Action": "start", "Package": "example/unused"},
    {"Time": "2026-10-01T00:00:01Z", "Action": "pass", "Package": "example/unused"},
]
reject("F2_UNMATCHED_PACKAGE_REJECTED", lambda: profile["_native_event_interval"](
    api, stream(unmatched), go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")

# Interleaved packages retain independent clocks and lifecycles. The emitted
# global sequence even moves backward in Time across packages; that is legal.
parallel = [
    {"Time": "2026-10-01T00:00:00Z", "Action": "start", "Package": "example/p"},
    {"Time": "2026-10-01T00:00:00.500000Z", "Action": "start", "Package": "example/q"},
    {"Time": "2026-10-01T00:00:02Z", "Action": "run", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-01T00:00:01Z", "Action": "run", "Package": "example/q", "Test": "TestW09Other"},
    {"Time": "2026-10-01T00:00:04Z", "Action": "pass", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-01T00:00:03Z", "Action": "pass", "Package": "example/q", "Test": "TestW09Other"},
    {"Time": "2026-10-01T00:00:05Z", "Action": "pass", "Package": "example/q"},
    {"Time": "2026-10-01T00:00:06Z", "Action": "pass", "Package": "example/p"},
]
assert profile["_native_event_interval"](
    api, stream(parallel), go_report, ["TestW09Synthetic", "TestW09Other"], "synthetic") == (
        "2026-10-01T00:00:00+00:00", "2026-10-01T00:00:06+00:00")
checks.append("F2_CROSS_PACKAGE_INTERLEAVING_ACCEPTED_SYNTHETIC")

'''.encode("utf-8")
controls_candidate = controls.replace(needle, extra + needle, 1)
controls_candidate = controls_candidate.replace(
    b'researchos.w09-formal-profile-v3-controls.v1',
    b'researchos.w09-formal-profile-v4-controls.v1', 1)
assert controls_candidate.count(b'researchos.w09-formal-profile-v3-controls.v1') == 0
ast.parse(profile_candidate, filename=str(profile_path))
ast.parse(controls_candidate, filename=str(controls_path))
assert profile_path.read_bytes() == profile and controls_path.read_bytes() == controls
profile_path.write_bytes(profile_candidate)
controls_path.write_bytes(controls_candidate)
assert profile_path.read_bytes() == profile_candidate
assert controls_path.read_bytes() == controls_candidate
print("W09_V4_CONTROLS_AND_PACKAGE_OWNERSHIP_AST_PASS")
