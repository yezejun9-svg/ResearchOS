"""Pure byte/AST audit and reverse patches for the selected review proposal."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
prior = here.parent.parent / "current58_whole_go_suite_revision_source_preparation_codex" / "6a9f35409cc34e4784ad92b374d73986"
assert prior.is_dir()
files = [
    ("gate", prior / "whole58_gate.v3.proposed.py", here / "whole58_gate.rev3.proposed.py"),
    ("runner", prior / "whole58_finite_runner.v4.proposed.py", here / "whole58_finite_runner.rev7.proposed.py"),
    ("execution_contract", prior / "whole58-execution.contract.proposed.json", here / "whole58-execution.contract.rev3.proposed.json"),
    ("authority_interface", prior / "authority-interface.proposed.json", here / "authority-interface.rev7.proposed.json"),
]

def ref(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}

def named_functions(raw):
    tree = ast.parse(raw)
    return {item.name: ast.dump(item, include_attributes=False)
            for item in tree.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}

report = {"schema": "researchos.current58-whole-go-source-revision-static-audit.v1",
          "stage": "SOURCE_PREPARATION_ONLY", "candidate_imported_or_executed": False,
          "go_executed": False, "source_acceptance": False,
          "formal_case_accepted_delta": 0, "checks": [], "pairs": []}
patches = []
for label, old, new in files:
    old_data, new_data = old.read_bytes(), new.read_bytes()
    if new.suffix == ".py":
        old_functions, new_functions = named_functions(old_data), named_functions(new_data)
        functions = {"changed": sorted(name for name in old_functions.keys() & new_functions.keys()
                                       if old_functions[name] != new_functions[name]),
                     "identical": sorted(name for name in old_functions.keys() & new_functions.keys()
                                         if old_functions[name] == new_functions[name]),
                     "added": sorted(new_functions.keys() - old_functions.keys()),
                     "removed": sorted(old_functions.keys() - new_functions.keys())}
    else:
        json.loads(old_data); json.loads(new_data)
        functions = None
    report["pairs"].append({"label": label, "before": ref(old), "after": ref(new),
                            "top_level_function_ast_delta": functions})
    patches.extend(difflib.unified_diff(old_data.decode("utf-8").splitlines(keepends=True),
                                        new_data.decode("utf-8").splitlines(keepends=True),
                                        fromfile=str(old), tofile=str(new)))

gate = files[0][2].read_text(encoding="utf-8")
runner = files[1][2].read_text(encoding="utf-8")
contract = json.loads(files[2][2].read_bytes())
interface = json.loads(files[3][2].read_bytes())
gref = ref(files[0][2])
checks = {
    "runner_gate_raw_sha_bound": f'GATE_SHA256 = "{gref["sha256"]}"' in runner,
    "runner_gate_raw_size_bound": f'GATE_BYTES = {gref["bytes"]}' in runner,
    "runner_does_not_use_sourcefileloader": "SourceFileLoader" not in runner,
    "runner_raw_gate_compiled_after_hash": runner.index("if len(raw) != GATE_BYTES") < runner.index("code = compile(raw"),
    "runner_pyc_disabled": "sys.dont_write_bytecode = True" in runner,
    "runner_gate_parent_guard": "list(GATE.parents)[:8]" in runner,
    "runner_execution_contract_selected": 'with_name("whole58-execution.contract.rev3.proposed.json")' in runner,
    "runner_overflow_fails_even_with_native_zero": all(x in runner for x in (
        '"OUTPUT_OVERFLOW"', 'receipt.get("stdout_overflow")', 'receipt.get("stderr_overflow")',
        'note_overflow(label, count - kept + len(chunk))')),
    "runner_raw_incomplete_fails": '"RAW_DRAIN_INCOMPLETE"' in runner and '"RAW_DRAIN_JOIN_FAILURE"' in runner,
    "runner_receipt_snapshot_under_lock": 'frozen_receipt = json.loads(json.dumps(receipt))' in runner,
    "gate_attestation_review_one_way": all(x in gate for x in (
        '"independent_review_ref" not in attestation', 'review.get("attestation_ref") == attestation_ref',
        'review.get("native_result_ref") == native_ref')),
    "gate_actual_root_cwd_worktree_bound": all(x in gate for x in (
        'Path.cwd().resolve(strict=True) == root', 'scope.get("worktree") == str(root)',
        'registration.get("worktree") == str(root)', 'grant.get("cwd") == str(root)',
        'lease.get("worktree") == scope.get("worktree") == str(root)',
        'paths.get("cwd") == str(root)')),
    "gate_source_false": contract["qualification"]["source_acceptance"] is False,
    "interface_runner_ref_selected": interface["registered_source_manifest"]["must_contain_exact_pins_for"][0] == files[1][2].name,
    "interface_gate_ref_selected": interface["registered_source_manifest"]["must_contain_exact_pins_for"][1] == files[0][2].name,
    "interface_execution_ref_selected": interface["registered_source_manifest"]["must_contain_exact_pins_for"][2] == files[2][2].name,
    "interface_no_future_grant": interface["future_root_literals_assigned"] is False,
}
report["checks"] = [{"id": k, "pass": v} for k, v in checks.items()]
assert all(checks.values())
for name, data in [
    ("source-inverse.patch", "".join(patches).encode("utf-8")),
    ("static-audit.json", (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")),
]:
    with (here / name).open("xb") as stream:
        stream.write(data)
print("STATIC_SOURCE_AUDIT_PASS", len(checks), len(files), len(patches))
