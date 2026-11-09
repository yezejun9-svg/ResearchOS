"""Emit a small, dynamically derived final index; keep full raw on C."""
import hashlib
import json
from pathlib import Path
import subprocess

MAIN = Path(r"D:/作品集/ResearchOS/research-os")
SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
BUILD = SOURCE / ".local/builds/approved-readlane-combined-20261012"
RAW = SOURCE / ".local/receipts/approved-readlane-combined-20261012"
HERE = Path(__file__).resolve().parent
OLD_HERE = MAIN / "execution/v2.4/receipts/W05/W05-99/approved_combined_desktop_build_codex/20261012-current-chat"
SCOPE = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp444/combined-readlane-package-scope.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}

def load(path):
    return json.loads(path.read_bytes())

def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd).decode().strip()

def main():
    output = HERE / "manifest.json"
    assert not output.exists()
    scope = load(SCOPE)
    result = load(RAW / "result.json")
    descriptor_path = BUILD / "apps/desktop/resources/client-wire/descriptor.json"
    descriptor = load(descriptor_path)
    tools = load(RAW / "tools.before.json")
    inputs = load(RAW / "inputs.before.json")
    after = load(RAW / "inputs.after.json")
    tests = load(HERE / "bound-tests.json")
    preflight = load(HERE / "preflight.json")
    composition = load(HERE / "composition.json")
    verification = load(HERE / "verification.json")
    acl = load(HERE / "acl-readback.json")
    package = Path(composition["package_root"])
    installer_path = Path(composition["installation_manifest_path"])
    installer = load(installer_path)
    ui = git(SOURCE, "rev-parse", "HEAD")
    ui_tree = git(SOURCE, "rev-parse", "HEAD^{tree}")
    main = git(MAIN, "rev-parse", "HEAD")
    main_tree = git(MAIN, "rev-parse", main + "^{tree}")
    assert ui == scope["ui_source_commit"] and main == scope["main_head"]
    assert ui_tree == main_tree == scope["ui_source_tree"]
    assert subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b""
    assert result["drift"] == [] and len(inputs) == len(after) == 6444
    assert all(row["sha256"] == row["current_sha256"] for row in after)
    assert hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == result["build_input_digest"]
    assert result["build_input_digest"] == descriptor["build_input_digest"] == tests["build_input_digest"]
    assert tests["unique_desktop_tests"] == 253
    assert sum(row["counts"]["pass"] for row in tests["desktop_entrypoints"]) == 253
    assert preflight["ui_source_tree"] == composition["ui_source_tree"] == ui_tree
    assert verification["package_members"] == len(composition["package_files"]) == 58
    assert installer["executable"] == str(package / "apps/desktop/resources/control/runtime-verifier.exe")
    assert installer["executable_hash"] == "sha256:" + verification["VCS_stamps"]["core_verifier"]["sha256"]
    assert acl["status"] == "LIVE_READBACK_PASS" and acl["manifest_sha256"] == sha(installer_path)
    assert len(descriptor["exact_module_source_inventory"]) == 14
    assert len(descriptor["compiled_React_asset_inventory"]) == 3
    assert len(composition["public_host_assets"]) == 32
    old_supplement = load(OLD_HERE / "manifest-supplement-01.json")
    assert old_supplement["field_precedence"]["effective_value_for_review"] == preflight["reviewed_core_tree"]
    manifest = {
        "schema": "researchos.cp444-approved-readlane-combined-desktop-manifest.v1",
        "status": "ASSEMBLED_HASHED_NOT_LAUNCHED",
        "scope": ref(SCOPE),
        "source_root": str(SOURCE),
        "ui_source_commit": ui,
        "ui_source_tree": ui_tree,
        "integrated_main_commit": main,
        "integrated_main_tree": main_tree,
        "component_vector": composition["source_vector"],
        "reviewed_core_source_tree": preflight["reviewed_core_tree"],
        "old_core_provenance": {
            "frozen_manifest": ref(OLD_HERE / "manifest.json"),
            "correction": ref(OLD_HERE / "correction-01.json"),
            "supplement": ref(OLD_HERE / "manifest-supplement-01.json"),
            "effective_core_tree": old_supplement["field_precedence"]["effective_value_for_review"]},
        "build": {
            "root": str(BUILD), "receipts": str(RAW),
            "full_input_count": len(inputs), "full_input_digest": result["build_input_digest"],
            "input_drift_count": 0, "new_validator_sha256": descriptor["binary_sha256"],
            "new_descriptor": ref(descriptor_path), "tools": tools,
            "full_input_manifest": ref(RAW / "inputs.before.json"),
            "input_after_manifest": ref(RAW / "inputs.after.json"),
            "compiler_archive_manifest": ref(RAW / "compiler-work-archive.json"),
            "build_result": ref(RAW / "result.json"),
            "go_build_invocation": ref(RAW / "go-build.invocation.json"),
            "react_build_invocation": ref(RAW / "react-build.invocation.json")},
        "local_tests": {"validator_pass": True,
                        "desktop_unique": 253,
                        "entrypoints": [{"name": row["name"], "counts": row["counts"],
                                          "prefix_counts": row["prefix_counts"],
                                          "invocation": ref(RAW / ("attempt01-" + row["name"] + ".invocation.json"))}
                                         for row in tests["desktop_entrypoints"]],
                        "validator_invocation": ref(RAW / "attempt01-validator-test.invocation.json"),
                        "bound_test_receipt": ref(HERE / "bound-tests.json")},
        "package": {"root": str(package), "member_count": 58,
                    "bytes": verification["package_bytes"],
                    "module_count": 14, "React_asset_count": 3, "public_host_count": 32,
                    "composition": ref(HERE / "composition.json"),
                    "installation_manifest": ref(installer_path),
                    "acl_protected_single_current_sid_ace": True,
                    "acl_readback": ref(HERE / "acl-readback.json")},
        "formal_receipts": {name: ref(HERE / name) for name in
                            ("preflight.json", "bound-tests.json", "composition.json",
                             "manifest-acl.json", "acl-readback.json", "verification.json")},
        "new_failures": [],
        "prior_failure_histories_rewritten": False,
        "protect_manifest_stdout_projection_note": "The protection command exited 0 and saved correct ACL JSON; its summary Select-Object on an ordered hashtable printed null fields. Independent live readback passed and is pinned above.",
        "activation": "NOT_STARTED", "actual_first_use": False,
        "model_calls": 0, "real_tool_calls": 0,
        "installer_acceptance": False, "formal_increment": 0, "parent_acceptance": False,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": manifest["status"], "manifest": ref(output),
                      "package_members": 58, "input_digest": result["build_input_digest"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
