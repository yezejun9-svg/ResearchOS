"""Seal independent Main23 source review. No execution of Go or product code."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parent.parent / "fresh_main23_programme_builder_source_codex" / "main23b-20261009-01"


def read(name):
    return json.loads((HERE / name).read_bytes())


def exact(path):
    raw = Path(path).read_bytes()
    return {"path": Path(path).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def save(name, obj):
    path = HERE / name
    assert not path.exists(), f"seal output already exists: {path}"
    raw = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with path.open("xb") as f:
        f.write(raw)
        f.flush()
    return exact(path)


def main():
    author_hdf = json.loads((AUTHOR / "HDF.json").read_bytes())
    author_mf = json.loads((AUTHOR / "MF.json").read_bytes())
    author_controls = json.loads((AUTHOR / "source-controls.json").read_bytes())
    contract = json.loads((AUTHOR / "contract.json").read_bytes())
    manifest = json.loads((AUTHOR / "input-manifest.json").read_bytes())
    own_controls = read("independent-controls.json")
    guard = read("source-guard-audit.json")
    author_member_checks = [{"name": Path(x["path"]).name, "matched": exact(x["path"]) == x} for x in author_mf["members"]]
    assert all(x["matched"] for x in author_member_checks)
    assert author_hdf["manifest_ref"] == exact(AUTHOR / "MF.json")
    assert author_hdf["builder_ref"] == exact(AUTHOR / "main23_builder.py")
    assert author_hdf["contract_ref"] == exact(AUTHOR / "contract.json")
    assert author_hdf["input_manifest_ref"] == exact(AUTHOR / "input-manifest.json")
    assert (author_controls["pass"], author_controls["fail"], author_controls["count"]) == (105, 0, 105)
    assert own_controls["failed"] == 0 and own_controls["passed"] == 35
    assert guard["error"] is None and guard["audit"]["verification"] == "PASSED"
    assert guard["audit"]["closed"] and guard["audit"]["retained_handles_count"] == 0
    assert len(guard["audit"]["entries"]) == 14676

    root = Path(contract["main_root"])
    actual = {str(x.resolve()).casefold() for s in contract["main_scopes"] for x in (root / s).rglob("*")
              if x.is_file() and not any(v in ("__pycache__", ".git", "node_modules") for v in x.relative_to(root / s).parts)}
    actual |= {str((root / n).resolve()).casefold() for n in ("go.mod", "go.sum")}
    declared = {str(Path(i["ref"]["path"]).resolve()).casefold() for i in manifest["items"] if i["kind"] == "main"}
    assert actual == declared and len(actual) == 572
    inventory_ref = save("current-main-inventory.json", {"schema": "researchos.main23-current-main-inventory-review.v1", "actual_count": len(actual), "manifest_count": len(declared), "missing": [], "unexpected": [], "migration_24_present": (root / "migrations/sqlite/0024_prepared_run_abandonment.sql").exists()})

    findings = {"schema": "researchos.main23-independent-source-findings.v1", "author": "codex:/root/w09_formal_profile_source_impl", "verdict": "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", "blocking_findings": [],
        "reviewed_boundaries": {
            "input_pins": "14670 current exact input refs plus six builder/helper refs verified with held Windows read handles; final target paths and bytes matched; all handles closed",
            "main_inventory": "572 current Main files match manifest; numbered SQLite migrations 0001 through 0023 and no 0024",
            "dependency_closure": "historical hint only: 334 packages reachable from ops/backup; no historical package file missing from current manifest; actual fresh go-list closure remains a runtime gate",
            "toolchain": "pinned go.exe and toolchain source files; unique initially empty GOCACHE; no shared cache copying",
            "process": "one pinned existing OwnedProcess callsite, closed_job aggregate cleanup check, uint64 FILETIME and uint32 PID validation; individual descendants remain unknown null",
            "failure": "per-phase raw stdout/stderr and result on returned observation; failstop, no automatic retry, Root assigns original failure ordinal; Root persists returned state if closed receipt cannot publish",
            "authority": "live Root scope required, Root registration precedes output creation, builder emits candidate with qualification_ref null"},
        "runtime_limits": ["Source review did not invoke Go, product, SQLite, Win32 OwnedProcess or create a registered build request", "Go export closure, cache behavior, actual executable and programme qualification require Root-controlled actual run and independent provenance review", "Root must enforce contract Root_require_registered_must_enforce obligations, including host runtime and loaded native resource qualification and held ownership through cleanup"],
        "author_member_checks": author_member_checks}
    findings_ref = save("findings.json", findings)

    hostpair = {"schema": "researchos.main23-independent-source-tool-pair.v1", "kind": "review_command_observation", "request": {"tool": "exec_command", "cmd": "python D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/fresh_main23_programme_builder_independent_source_review_codex/src-review-20261009-01/review_source.py", "workdir": "D:/作品集/ResearchOS"},
        "response": {"exit_code": 0, "output_json": {"passed": 35, "failed": 0, "failures": [], "guard": {"ref_count": 14676, "byte_sum": 363197213, "error": None}}},
        "scope_note": "This records the visible command/result pair; it is not a byte-for-byte host wrapper capture. Full Root hostpair remains Root's obligation.",
        "independent_controls_ref": exact(HERE / "independent-controls.json"), "source_guard_audit_ref": exact(HERE / "source-guard-audit.json")}
    hostpair_ref = save("review-tool-pair.json", hostpair)

    decision = {"schema": "researchos.main23-independent-source-decision.v1", "review_author": "codex:/root/w09_formal_profile_source_impl", "source_author": author_hdf["source_author"], "independent_non_author": True,
        "verdict": "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", "formal_programme_qualification": False, "candidate_program_ref": None,
        "author_hdf_ref": exact(AUTHOR / "HDF.json"), "author_mf_ref": exact(AUTHOR / "MF.json"), "author_contract_ref": exact(AUTHOR / "contract.json"), "author_builder_ref": exact(AUTHOR / "main23_builder.py"), "author_input_manifest_ref": exact(AUTHOR / "input-manifest.json"),
        "independent_controls_ref": exact(HERE / "independent-controls.json"), "source_guard_audit_ref": exact(HERE / "source-guard-audit.json"), "inventory_ref": inventory_ref, "findings_ref": findings_ref, "review_tool_pair_ref": hostpair_ref,
        "source_controls": {"author_pass": 105, "author_fail": 0, "independent_pass": 35, "independent_fail": 0},
        "Go_product_SQLite_OwnedProcess_calls": 0, "actual_build": "NOT_RUN", "qualification_ref": None, "Main23_to24": "BLOCKED_MAIN_NOT_ADOPTED", "schema21": "OPEN", "full20to24": "OPEN", "original_failures": [], "Root_counter_last_reported": 1013, "formal_acceptance": False}
    decision_ref = save("source-decision.json", decision)

    members = [exact(HERE / n) for n in ["review_source.py", "seal_review.py", "independent-controls.json", "source-guard-audit.json", "current-main-inventory.json", "findings.json", "review-tool-pair.json", "source-decision.json"]]
    mf_ref = save("MF.json", {"schema": "researchos.source-manifest.v1", "scope": "INDEPENDENT_CURRENT_MAIN23_BUILDER_SOURCE_REVIEW", "members": members, "excludes": ["MF.json", "HDF.json"]})
    hdf_ref = save("HDF.json", {"schema": "researchos.main23-independent-source-review-handoff.v1", "status": "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", "source_author": author_hdf["source_author"], "review_author": "codex:/root/w09_formal_profile_source_impl", "author_hdf_ref": exact(AUTHOR / "HDF.json"), "author_mf_ref": exact(AUTHOR / "MF.json"), "manifest_ref": mf_ref, "decision_ref": decision_ref, "findings_ref": findings_ref, "independent_controls_ref": exact(HERE / "independent-controls.json"), "source_guard_audit_ref": exact(HERE / "source-guard-audit.json"), "review_tool_pair_ref": hostpair_ref, "current_input_pins_checked": 14670, "held_guard_refs_checked_and_closed": 14676, "source_controls_pass": 35, "source_controls_fail": 0, "Go_product_SQLite_OwnedProcess_calls": 0, "first_actual_request_created": False, "Root_registration": "NOT_CREATED", "actual_build": "NOT_RUN", "formal_programme_qualification": False, "qualification_ref": None, "Main23_to24": "BLOCKED_MAIN_NOT_ADOPTED", "schema21": "OPEN", "full20to24": "OPEN", "new_original_failures": [], "Root_counter_last_reported": 1013, "formal_acceptance": False, "STOP": True, "FINAL": True})
    print(json.dumps({"HDF": hdf_ref, "MF": mf_ref, "decision": decision_ref}, ensure_ascii=False))


if __name__ == "__main__":
    main()
