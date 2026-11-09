"""Read-only, pure Source-review controls for the proposed Main23 Root caller."""
import hashlib
import importlib.util
import json
from pathlib import Path
import types

ROOT = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99")
SOURCE = ROOT / "fresh_main23_root_caller_registration_source_codex" / "main23root-20261009-01"
OUT = Path(__file__).resolve().parent


def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def load_source():
    spec = importlib.util.spec_from_file_location("reviewed_main23_root_source", SOURCE / "main23_root.source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_source_chain(module):
    hdf = json.loads((SOURCE / "HDF.json").read_bytes())
    mf = json.loads((SOURCE / "MF.json").read_bytes())
    assert hdf["status"] == "SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING"
    assert hdf["source_author"] == module.AUTHOR
    assert hdf["manifest_ref"] == pin(SOURCE / "MF.json")
    assert hdf["caller_ref"] == hdf["registrar_ref"] == pin(SOURCE / "main23_root.source.py")
    assert len(mf["members"]) == 12
    assert all(member == pin(member["path"]) for member in mf["members"])
    for key in ("contract_ref", "source_inputs_ref", "controls_ref", "facts_ref", "recorded_tool_pairs_ref"):
        assert hdf[key] == pin(hdf[key]["path"])
    assert hdf["actual_registration"] is False and hdf["actual_builder_execution"] is False
    return {"name": "sealed_source_chain", "result": "PASS", "members": len(mf["members"])}


def hash_only_external_capture(module):
    # The output contains three matching digests, but no ref path or size.
    refs = [{"path": f"C:\\relevant\\{i}.json", "sha256": f"{i:064x}", "bytes": 123+i} for i in (1, 2, 3)]
    rows = [
        {"type": "session_meta", "payload": {"id": module.ROOT_THREAD}},
        {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "call-review-test", "name": "exec", "input": {"cmd": "irrelevant"}}},
        {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "call-review-test", "output": {"message": " ".join(ref["sha256"] for ref in refs)}}},
    ]
    raw = b"".join((json.dumps(row) + "\n").encode() for row in rows)
    lines = raw.splitlines(keepends=True)
    binding = {
        "schema": "researchos.root-actual-tool-capture-binding.v1", "issued_by": module.ROOT,
        "root_thread_id": module.ROOT_THREAD, "original_call_id": "call-review-test",
        "original_line_sha256": [hashlib.sha256(line).hexdigest() for line in lines],
        "source_line_bytes": [len(line) for line in lines],
        "tool_call_timestamp": "2026-10-09T00:00:00Z", "tool_result_timestamp": "2026-10-09T00:00:01Z",
    }
    assert module.validate_root_capture(binding, raw, refs) is True
    return {"name": "hash_only_external_capture_false_positive", "result": "REPRODUCED", "expected_refs": refs,
            "actual_tool_output_has_paths": False, "actual_tool_output_has_sizes": False}


def string_only_runtime_reviewer(module):
    python = {"path": "C:\\python.exe", "sha256": "1" * 64, "bytes": 1}
    go = {"path": "C:\\go.exe", "sha256": "2" * 64, "bytes": 2}
    guard = module.GUARD_REF
    tp = module.TP_REF
    caller = {"path": "C:\\caller.py", "sha256": "3" * 64, "bytes": 3}
    resources = [python, go, guard, tp, caller]
    qualification_ref = {"path": "C:\\qualification.json", "sha256": "4" * 64, "bytes": 4}
    decision_ref = {"path": "C:\\decision.json", "sha256": "5" * 64, "bytes": 5}
    lock_ref = {"path": "C:\\lock.json", "sha256": "6" * 64, "bytes": 6}
    forged_reviewer = "codex:/invented-independent-reviewer"
    qualification = {"schema": "researchos.root-main23-qualified-runtime.v1", "issued_by": module.ROOT,
                     "independent_non_author": True, "review_author": forged_reviewer,
                     "status": "QUALIFIED_FOR_MAIN23_BUILD", "formal_programme_qualification": False,
                     "python_ref": python, "go_ref": go, "review_decision_ref": decision_ref,
                     "resource_refs": resources}
    decision = {"review_author": forged_reviewer, "independent_non_author": True,
                "verdict": "RUNTIME_CLOSURE_ACCEPTED", "resource_refs": resources}
    locked = {"tools": {"python": python, "go": go}}
    table = {qualification_ref["path"]: qualification, decision_ref["path"]: decision, lock_ref["path"]: locked}
    original = {key: getattr(module, key) for key in ("doc", "pin", "load", "sys")}
    try:
        module.doc = lambda ref: table[ref["path"]]
        module.pin = lambda path: caller if str(path) == str(module.__file__) else python
        module.load = lambda ref, name: types.SimpleNamespace(runtime_resource_paths=lambda: [])
        module.sys = types.SimpleNamespace(executable=python["path"], modules={})
        result = module.runtime_closure(qualification_ref, {"toolchain_lock_ref": lock_ref, "go_ref": go, "owned_job_ref": caller})
        assert result == [qualification_ref, decision_ref, lock_ref] + resources
    finally:
        for key, value in original.items():
            setattr(module, key, value)
    return {"name": "string_only_runtime_reviewer_false_positive", "result": "REPRODUCED",
            "authenticated_review_capture": False, "review_author": forged_reviewer}


def main():
    module = load_source()
    results = [check_source_chain(module), hash_only_external_capture(module), string_only_runtime_reviewer(module)]
    path = OUT / "source-review-controls.json"
    path.write_text(json.dumps({"source_ref": pin(SOURCE / "main23_root.source.py"), "controls": results,
                                "scope": "Pure Source fixtures; no Canon/Native/Go/SQLite/Main access"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"controls_ref": pin(path), "results": [r["result"] for r in results]}))


if __name__ == "__main__":
    main()
