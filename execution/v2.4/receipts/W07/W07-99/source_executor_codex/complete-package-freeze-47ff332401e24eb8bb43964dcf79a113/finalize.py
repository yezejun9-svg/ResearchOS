import json
import os
import sys
from qualify import OUT, ROOT, MAIN, run, save, ref

save(OUT / "qualification-initial-failure.json", {
    "actualargv": [sys.executable, "-B", "-X", "utf8", str((OUT / "qualify.py").relative_to(ROOT))],
    "cwd": str(ROOT), "exit_code": 1,
    "origin": "exec session 60524, chunk c51d49; original terminal output retained in session",
    "exception": "AssertionError at qualify.py line 86: len(old_gaps) == 27 and set(old_gaps).issubset(snapshot)",
    "cause": "The isolated 2da28a73 baseline lacks the S6-only adapters/runtime/bridge_control_windows_test.go; actual fixture and environment commands had already exited 0",
    "correction": "Validate actual isolated package closure and 26 existing gaps; separately bind all 27 MAIN paths to actual MAIN package directories. MAIN capture remains pending.",
    "source_script_ref": ref(OUT / "qualify.py")})
run([sys.executable, "-B", "-X", "utf8", str((OUT / "verify_saved.py").relative_to(ROOT))], "final-readonly-verification", dict(os.environ))
failed = MAIN / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-2881cfa84dd64156b59d12795e6375a2"
save(OUT / "handoff.json", {
    "status": "CANDIDATE_READY_FOR_INDEPENDENT_REVIEW", "formal_acceptance": "NOT_ISSUED",
    "executor": "codex:/root/sources_parent_impl", "scope": ["ops/ci/sources.py", "tests/sources/check/parent_gate_test.py"],
    "qualification_ref": ref(OUT / "qualification.json"),
    "retained_main_rejected_context_ref": ref(failed / "context.json"),
    "retained_main_preflight_ref": ref(failed / "preflight.json"),
    "retained_main_capture_27_gaps_ref": ref(failed / "capture-coverage-gaps.json"),
    "retained_main_G01_642_difference_ref": ref(failed / "dispatch-source-gap.json"),
    "verification_caveat": "MAIN default Go environment/dependencies were inspected read-only using candidate helper. Full collector fixture ran only in original W07 worktree. No new LIVE collection or native MAIN dispatch occurred.",
    "remaining": "Independent code review, Root serial integration, one current MAIN three-source/H07 freeze and native four commands, then formal pre-registration qualification"})
print(json.dumps({"handoff": ref(OUT / "handoff.json"), "qualification": ref(OUT / "qualification.json")}))
