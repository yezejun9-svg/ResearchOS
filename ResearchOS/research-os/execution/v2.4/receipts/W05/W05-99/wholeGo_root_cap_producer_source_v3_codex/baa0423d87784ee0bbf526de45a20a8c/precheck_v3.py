"""Pure IO and extracted-helper checks. Never imports the candidate module."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "wholego_cap_metadata.v3.proposed.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
compile(tree, str(SOURCE), "exec", dont_inherit=True)
functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
names = ("require", "unique_json", "canonical", "verified_raw", "verified_json",
         "allocated_paths", "close")
assert all(name in functions for name in names)
extracted = ast.fix_missing_locations(ast.Module(body=[functions[name] for name in names],
                                                 type_ignores=[]))
ns = {"Path": Path, "stat": stat, "hashlib": hashlib, "json": json,
      "ROOT": None, "HEAD": "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"}
exec(compile(extracted, str(SOURCE), "exec", dont_inherit=True), ns)

def reject(call, code):
    try:
        call()
    except ValueError as exc:
        assert code in str(exc), (code, str(exc))
    else:
        raise AssertionError("unexpected accept: " + code)

with tempfile.TemporaryDirectory(prefix="cap-v3-check-", dir=HERE) as tmp:
    root = Path(tmp).resolve(strict=True)
    assert HERE in root.parents
    ns["ROOT"] = root
    uuid = "a" * 32
    target = root / "raw.go"
    target.write_bytes(b"package main\n")
    raw = target.read_bytes()
    ref = {"path": str(target), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    assert ns["verified_raw"](ref) == raw
    try:
        ns["verified_json"](ref)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("Go source was accepted as JSON")
    drift = {**ref, "sha256": "0" * 64}
    reject(lambda: ns["verified_raw"](drift), "PIN_DRIFT")
    assert sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
               node.func.attr == "read_bytes" for node in ast.walk(functions["verified_raw"])) == 1
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                   node.func.attr == "read_bytes" for node in ast.walk(functions["verified_json"]))

    base = root / "execution/v2.4/receipts/W05/W05-99/integration_codex"
    reg = base / ("whole58-go-" + uuid)
    run_out = reg / "run-output"
    stage_out = reg / "cap-producer/arm"
    stage_out.mkdir(parents=True)
    run_out.mkdir()
    allocation = {"schema": "researchos.current58-whole-go-root-allocation.v1",
                  "actor_id": "codex:/root", "run_uuid": uuid,
                  "source_commit": ns["HEAD"], "registration_dir": str(reg),
                  "run_output_root": str(run_out),
                  "stage_output_roots": {"arm": str(stage_out)}}
    review = {"schema": "researchos.current58-whole-go-root-allocation-review.v1",
              "decision": "ALLOCATED_PATHS_REVIEWED", "actor_id": "codex:/root/f08",
              "run_uuid": uuid, "allocation_ref": "alloc"}
    ns["verified_json"] = lambda ref: {"alloc": allocation, "review": review}[ref]
    source = {"run_uuid": uuid, "owner": "codex:/root",
              "root_allocation_ref": "alloc", "root_allocation_review_ref": "review"}
    assert ns["allocated_paths"](source, "arm", stage_out) == allocation
    foreign = root / "foreign"
    foreign.mkdir()
    reject(lambda: ns["allocated_paths"](source, "arm", foreign),
           "ROOT_STAGE_OUTPUT_NOT_FRESH")

    # The close consumer must bind the exact original output leaf before reading
    # user-controlled JSON. Stubs count reads and reject a swapped terminal path.
    ns["scope"] = lambda source, require_fresh=False: {"output_root": str(run_out)}
    docs = {"scope": {"output_root": str(run_out)}}
    ns["verified_json"] = lambda ref: docs[ref]
    close_source = {"scope_ref": "scope", "runner_report_ref": None,
                    "runner_terminal_ref": {"path": str(foreign / "terminal.json"),
                                            "sha256": "0" * 64, "bytes": 0}}
    (foreign / "terminal.json").write_bytes(b"{}")
    reject(lambda: ns["close"](close_source), "RUNNER_TERMINAL_NOT_FROM_THIS_OUTPUT")

assert "read_pin(" not in SOURCE.read_text(encoding="utf-8")
assert "source[\"checkpoint_ref\"][\"path\"]" in SOURCE.read_text(encoding="utf-8")
assert "observed_windows_process(outer[\"runner_pid\"])" in SOURCE.read_text(encoding="utf-8")
results = {"schema": "researchos.whole-go-cap-v3-pure-precheck.v1",
           "python_ast_compile": True, "candidate_imported": False,
           "go_or_product_executed": False, "actual_cap_authorized": False,
           "positive": ["Go raw pin validates without JSON parse",
                        "exact Root allocation arm output path accepted"],
           "negative": ["wrong raw SHA refused", "Go raw rejected as JSON",
                        "foreign stage output refused before writing",
                        "swapped terminal outside run output refused before consuming JSON"],
           "one_read_parse": "AST verified: verified_raw has one read_bytes; verified_json has zero",
           "controller_and_native_live_tests": "NOT_RUN_SOURCE_ONLY"}
with (HERE / "precheck.v3.final.json").open("xb") as out:
    out.write((json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
print(json.dumps(results, ensure_ascii=False))
