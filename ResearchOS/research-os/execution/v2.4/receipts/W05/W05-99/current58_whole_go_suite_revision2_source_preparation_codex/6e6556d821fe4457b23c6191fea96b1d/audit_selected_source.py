"""Pure static selected-source audit and full reversible unified diff."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
prior = here.parent.parent / "current58_whole_go_suite_revision_source_preparation_codex" / "6a9f35409cc34e4784ad92b374d73986"
pairs = {
    "gate": (prior / "whole58_gate.v3.proposed.py", here / "whole58_gate.rev4.proposed.py"),
    "runner": (prior / "whole58_finite_runner.v4.proposed.py", here / "whole58_finite_runner.rev9.proposed.py"),
    "execution_contract": (prior / "whole58-execution.contract.proposed.json", here / "whole58-execution.contract.rev4.proposed.json"),
    "authority_interface": (prior / "authority-interface.proposed.json", here / "authority-interface.rev9.proposed.json"),
}

def ref(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def funcs(raw):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)}

report = {"schema": "researchos.current58-whole-go-selected-source-static-audit.v1",
          "stage": "SOURCE_PREPARATION_ONLY", "candidate_imported_or_executed": False,
          "go_executed": False, "source_acceptance": False, "formal_case_accepted_delta": 0,
          "pairs": {}, "checks": {}}
diff = []
for name, (old, new) in pairs.items():
    oldraw, newraw = old.read_bytes(), new.read_bytes()
    if new.suffix == ".py":
        before, after = funcs(oldraw), funcs(newraw)
        fn = {"changed": sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
              "identical": sorted(k for k in before.keys() & after.keys() if before[k] == after[k]),
              "added": sorted(after.keys()-before.keys()), "removed": sorted(before.keys()-after.keys())}
    else:
        json.loads(oldraw); json.loads(newraw)
        fn = None
    report["pairs"][name] = {"before": ref(old), "after": ref(new), "function_ast_delta": fn}
    diff.extend(difflib.unified_diff(oldraw.decode("utf-8").splitlines(keepends=True),
                                     newraw.decode("utf-8").splitlines(keepends=True),
                                     fromfile=str(old), tofile=str(new)))

gate = pairs["gate"][1].read_text(encoding="utf-8")
runner = pairs["runner"][1].read_text(encoding="utf-8")
contract = json.loads(pairs["execution_contract"][1].read_bytes())
interface = json.loads(pairs["authority_interface"][1].read_bytes())
gref = ref(pairs["gate"][1])
checks = {
    "gate_raw_sha_before_compile": f'GATE_SHA256 = "{gref["sha256"]}"' in runner and
        runner.index("if len(raw) != GATE_BYTES") < runner.index("code = compile(raw"),
    "gate_raw_bytes_bound": f'GATE_BYTES = {gref["bytes"]}' in runner,
    "gate_bootstrap_parent_guard": "list(GATE.parents)[:8]" in runner,
    "gate_bootstrap_no_import_loader": not any(
        isinstance(node, ast.Name) and node.id == "SourceFileLoader" for node in ast.walk(ast.parse(runner))),
    "runner_pyc_disabled": "sys.dont_write_bytecode = True" in runner,
    "runner_selected_contract_pointer": 'with_name("whole58-execution.contract.rev4.proposed.json")' in runner,
    "overflow_firstcause_lock": '"OUTPUT_OVERFLOW"' in runner and "with cause_lock:" in runner,
    "overflow_fail_even_native_zero": all(token in runner for token in (
        'receipt.get("stdout_overflow")', 'receipt.get("stderr_overflow")',
        'receipt.get("drain_incomplete")', 'receipt.get("stdout_raw_complete")')),
    "separate_partial_raw_pins": 'receipt[label + "_partial_raw"] = raw_pin' in runner and
        'receipt[label + "_raw_complete"] = bool(saw_eof[label]' in runner,
    "popen_deadline_recheck": runner.index('wall = guarded_wall(budgets, deadline)\n        receipt["timeout_seconds"]') <
        runner.index("proc = subprocess.Popen"),
    "bounded_join_and_snapshot": all(token in runner for token in (
        '"RAW_DRAIN_JOIN_FAILURE"', '"RAW_DRAIN_INCOMPLETE"',
        'frozen_receipt = json.loads(json.dumps(receipt))')),
    "one_way_attestation_review": all(token in gate for token in (
        '"independent_review_ref" not in attestation',
        'review.get("attestation_ref") == attestation_ref',
        'review.get("native_result_ref") == native_ref')),
    "actual_cwd_worktree_bound": all(token in gate for token in (
        'Path.cwd().resolve(strict=True) == root', 'scope.get("worktree") == str(root)',
        'registration.get("cwd") == str(root)', 'grant.get("cwd") == str(root)',
        'lease.get("worktree") == scope.get("worktree") == str(root)',
        'paths.get("cwd") == str(root)')),
    "model_zero_integer_exact": 'type(budgets.get("max_model_requests")) is int' in gate,
    "selected_source_manifest_names": interface["registered_source_manifest"]["must_contain_exact_pins_for"][:3] ==
        [pairs["runner"][1].name, pairs["gate"][1].name, pairs["execution_contract"][1].name],
    "selected_launch_argv": interface["execution_argv_template"][5] == "<" + pairs["runner"][1].name + ">",
    "source_and_formal_zero": contract["qualification"]["source_acceptance"] is False and
        contract["qualification"]["formal_case_accepted_delta"] == 0,
}
report["checks"] = checks
report["all_static_checks_pass"] = all(checks.values())
for name, raw in [
    ("source-inverse.selected.patch", "".join(diff).encode("utf-8")),
    ("static-audit.selected.json", (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")),
]:
    with (here / name).open("xb") as stream: stream.write(raw)
print("SELECTED_STATIC_AUDIT", sum(checks.values()), len(checks), report["all_static_checks_pass"])
