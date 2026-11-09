import hashlib
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

here = pathlib.Path(__file__).resolve().parent
repo = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
old = repo / "execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261015-current-chat"
scope_path = repo / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp529/source43-resume-scope.json"
scope = json.loads(scope_path.read_text(encoding="utf-8"))


def sha(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(name, data):
    (here / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def receipt(name):
    folder = here / name
    return {"id": name, "exit": json.loads((folder / "exit.json").read_text(encoding="utf-8"))["exit"],
            "invocation": str((folder / "invocation.json").relative_to(here)),
            "stdout": {"path": str((folder / "stdout.raw").relative_to(here)), **sha(folder / "stdout.raw")},
            "stderr": {"path": str((folder / "stderr.raw").relative_to(here)), **sha(folder / "stderr.raw")}}


def go_events(name):
    events = [json.loads(line) for line in (here / name / "stdout.raw").read_text(encoding="utf-8").splitlines() if line.startswith("{")]
    return {"receipt": name, "native_exit": receipt(name)["exit"],
            "pass_events": [e["Test"] for e in events if e.get("Action") == "pass" and e.get("Test")],
            "fail_events": [e["Test"] for e in events if e.get("Action") == "fail" and e.get("Test")],
            "skip_events": [e["Test"] for e in events if e.get("Action") == "skip" and e.get("Test")]}


def main():
    assert sha(scope_path)["sha256"] == "ba67fadc116d087735c122602118322c349cf35e288a44a570569eae7aec731a"
    head, tree = (here / "039-final-head-tree/stdout.raw").read_text(encoding="utf-8").splitlines()
    assert head == "085b4711afe0c1288448b174eef24ecd5af0551b"
    assert tree == "227d36324fd1053c285d0b2846a2b707ac2df6bd"
    assert (here / "040-final-clean-status/stdout.raw").read_bytes() == b""
    assert json.loads((here / "041-final-pin41/stdout.raw").read_text(encoding="utf-8"))["mismatches"] == []
    names = [line.split("\t", 1)[1] for line in (here / "034-main43-name-status/stdout.raw").read_text(encoding="utf-8").splitlines()]
    assert len(names) == 43 and set(names) == set(scope["source_allowlist"])
    for name in ("045-control-buildinfo", "046-stop-buildinfo"):
        data = (here / name / "stdout.raw").read_text(encoding="utf-8")
        assert f"vcs.revision={head}" in data and "vcs.modified=false" in data
    copies = {"037-fix2-patch-from-baseb/stdout.raw": "fix2-from-baseB.patch",
              "047-full43-binarypatch/stdout.raw": "full43-from-Main4f.patch",
              "042-final43-manifest/stdout.raw": "source43-files.json"}
    for source, destination in copies.items():
        shutil.copyfile(here / source, here / destination)
    manifest = json.loads((here / "source43-files.json").read_text(encoding="utf-8"))
    assert set(manifest) == set(scope["source_allowlist"])
    for name, pin in scope["mechanical_source41_pins"].items():
        assert manifest[name] == {"sha256": pin["sha256"], "bytes": pin["bytes"]}

    old_commands = []
    for folder in sorted(old.iterdir()):
        if folder.is_dir() and folder.name[:3].isdigit():
            item = {"id": folder.name, "exit_present": (folder / "exit.json").exists()}
            if (folder / "exit.json").exists():
                item["native_exit"] = json.loads((folder / "exit.json").read_text(encoding="utf-8"))["exit"]
            for filename in ("invocation.json", "stdout.raw", "stderr.raw"):
                if (folder / filename).exists():
                    item[filename] = sha(folder / filename)
            old_commands.append(item)
    new_commands = [receipt(p.name) for p in sorted(here.iterdir()) if p.is_dir() and p.name[:3].isdigit() and (p / "exit.json").exists()]
    write("command-index.json", {"source": "20261025-current-chat", "recorded_commands": new_commands,
                                 "capture_boundary": "Finalizer command 049 is excluded from this pre-finalization index; its receipt is adjacent."})
    old_failures = [x for x in old_commands if not x["exit_present"] or x.get("native_exit") != 0]
    new_failures = [x for x in new_commands if x["exit"] != 0]
    write("diagnostic-ledger.json", {"old_command_count": len(old_commands), "old_failures_or_missing_exit": old_failures,
                                     "new_recorded_failures": new_failures,
                                     "launcher_binding_failures_without_subprocess_receipt": [
                                         {"id": "005-check-test-invocation", "cause": "PowerShell parameter binder rejected python -c argument"},
                                         {"id": "012-fixture-requirements", "cause": "PowerShell parameter binder rejected rg -C"},
                                         {"id": "014-build-owned-fixture", "cause": "PowerShell parameter binder treated -o as common parameter"}],
                                     "historical_boundary": "20261015 receipts are read only; ordinal 011 absent in old sequence and not rewritten."})
    matrix = [go_events(x) for x in ("008-host-backup-integration", "010-stop-store-ops", "016-rerun-fixture-tests", "018-rerun-fixture-tests-c", "026-b-domain-focused", "048-roots-clean-commit")]
    matrix += [{"receipt": "024-ownedcorestop-native-c", "native_exit": receipt("024-ownedcorestop-native-c")["exit"], "pass_events": ["TestOwnedCoreStopPostflightRealLeaseBlocksLogicalDrift"], "fail_events": [], "skip_events": []},
               {"receipt": "025-ownedops-native-c", "native_exit": receipt("025-ownedops-native-c")["exit"], "pass_events": ["TestOwnedCoreControlledCrashWALAndLease"], "fail_events": [], "skip_events": []}]
    write("claim-test-matrix.json", {"results": matrix,
                                     "qualification_failure_closure": "026 TestQualificationFailure* all pass, zero skips within that prefix",
                                     "domain_skip_boundary": "026 has 56 skip events requiring an explicitly built immutable Mu bundle; skips are not counted as passes",
                                     "previous_failures": "010/016/018 retain fixture/environment failure evidence; 024/025 pass after C secure parent test image"})
    final = {"schema": "researchos.source43-combined-source-freeze.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
             "status": "AUTHOR_FROZEN_PENDING_INDEPENDENT_REVIEW", "source_commit": head, "source_tree": tree,
             "base_b_commit": scope["base_commit"], "main_base": scope["Main_base"], "stop_commit": scope["STOP_commit"],
             "worktree": scope["worktree"], "source_paths": 43, "mechanical_paths": 41, "semantic_fix_paths": ["internal/host/roots_windows.go", "internal/host/roots_windows_test.go"],
             "clean_worktree": True, "mechanical41_pins_match": True, "full43_names_match": True,
             "builds": {"apps/control": "043-build-control/exit.json", "ops/owned_core_stop": "044-build-owned-stop/exit.json"},
             "buildinfo": ["045-control-buildinfo/stdout.raw", "046-stop-buildinfo/stdout.raw"],
             "evidence": {name: sha(here / name) for name in ("source43-files.json", "fix2-from-baseB.patch", "full43-from-Main4f.patch", "command-index.json", "diagnostic-ledger.json", "claim-test-matrix.json")},
             "authority": {"actual": False, "formal_increment": 0, "self_acceptance": False, "main_imported": False},
             "limitations": ["B fixture-dependent Mu tests skipped without immutable bundle", "No live provider, original data, or formal acceptance exercised"]}
    write("FINAL-manifest.json", final)
    print(json.dumps({"commit": head, "tree": tree, "old_failures": [x["id"] for x in old_failures], "new_failures": [x["id"] for x in new_failures], "final": str(here / "FINAL-manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
