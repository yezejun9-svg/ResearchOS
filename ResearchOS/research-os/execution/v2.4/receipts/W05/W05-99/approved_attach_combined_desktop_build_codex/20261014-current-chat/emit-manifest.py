"""Verify the assembled package and emit a reviewable build receipt."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

MAIN = Path("D:/作品集/ResearchOS/research-os")
SOURCE = Path("C:/Users/yqyyds/.codex/researchos-build-worktrees/attach-synchronous-completion-20261012")
BUILD = SOURCE / ".local/builds/approved-attach-combined-20261014"
RAW = SOURCE / ".local/receipts/approved-attach-combined-20261014"
DEST = Path("C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014")
HERE = Path(__file__).resolve().parent
SCOPE = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp451/combined-attach-package-scope.json"
REVIEW = MAIN / "execution/v2.4/receipts/W05/W05-99/attach_synchronous_integration_codex/20261014-current-chat/FINAL-report.json"
INTEGRATION = MAIN / "execution/v2.4/receipts/W05/W05-99/attach_synchronous_integration_codex/20261014-current-chat/integration.json"
OLD_MANIFEST = MAIN / "execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat/manifest.json"
SOURCE_COMMIT = "b955c8665281193d5cbf90a146f936c9212c7940"
SOURCE_TREE = "00d44e133662227b115eb3b16bef3d4edcc35630"
MAIN_COMMIT = "c465d1356480d6e6a90da84656724f9fc02b31c7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def load(path):
    return json.loads(path.read_bytes())


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd).decode().strip()


def main():
    require(not (HERE / "FINAL-manifest.json").exists(), "final manifest already exists")
    scope = load(SCOPE)
    require(scope["source_commit"] == SOURCE_COMMIT and scope["main_head"] == MAIN_COMMIT, "scope identity mismatch")
    require(git(SOURCE, "rev-parse", "HEAD") == SOURCE_COMMIT and git(SOURCE, "status", "--porcelain=v1") == "", "source changed")
    require(git(SOURCE, "rev-parse", "HEAD^{tree}") == SOURCE_TREE, "source tree changed")
    require(git(MAIN, "rev-parse", "HEAD") == MAIN_COMMIT and git(MAIN, "rev-parse", "HEAD^{tree}") == SOURCE_TREE, "Main changed")
    require(load(REVIEW)["verdict"] == "APPROVE_LIMITED_SCOPE", "source review changed")
    composition = load(HERE / "composition.json")
    descriptor = load(DEST / "apps/desktop/resources/client-wire/descriptor.json")
    result = load(RAW / "result.json")
    acl = load(HERE / "acl-readback.json")
    installation = load(DEST / "apps/desktop/resources/control/runtime-verifier-installation.json")
    require(result["status"] == "BUILT_NOT_TESTED" and not result["drift"], "build drift")
    require(descriptor["build_input_digest"] == result["build_input_digest"] == composition["bound_full_input_digest"], "descriptor binding mismatch")
    require(sha(DEST / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe") == descriptor["binary_sha256"], "validator changed")
    rows = composition["package_files"]
    require(len(rows) == 58 and len({r["path"] for r in rows}) == 58, "member census mismatch")
    actual = {p.relative_to(DEST).as_posix() for p in DEST.rglob("*") if p.is_file()}
    require(actual == {r["path"] for r in rows}, "package filesystem census mismatch")
    for row in rows:
        p = DEST / row["path"]
        require(p.is_file() and not p.is_symlink() and p.stat().st_size == row["bytes"] and sha(p) == row["sha256"], "package member mismatch: " + row["path"])
    installer_path = DEST / "apps/desktop/resources/control/runtime-verifier-installation.json"
    verifier_path = DEST / "apps/desktop/resources/control/runtime-verifier.exe"
    require(installation["executable"] == str(verifier_path) and installation["executable_hash"] == "sha256:" + sha(verifier_path), "installer verifier mismatch")
    require(installation["source_commit"] == SOURCE_COMMIT, "installer source mismatch")
    require(acl["status"] == "LIVE_READBACK_PASS" and acl["protected"] and acl["rule_count"] == 1 and acl["current_user_sid"] == acl["single_ace_identity"] and acl["manifest_sha256"] == sha(installer_path), "installer ACL mismatch")
    stamps = {}
    binaries = {"control": DEST / "apps/desktop/resources/control/researchos-control.exe",
                "runtime_verifier": verifier_path,
                "client_wire_validator": DEST / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe"}
    for label, receipt_label in (("control", "core-control"), ("runtime_verifier", "core-runtime-verifier"), ("client_wire_validator", "validator")):
        raw = RAW / (receipt_label + "-go-version-m.stdout")
        text = raw.read_text(encoding="utf-8")
        require("vcs.revision=" + SOURCE_COMMIT in text and "vcs.modified=false" in text, "VCS stamp mismatch: " + label)
        stamps[label] = {"binary": ref(binaries[label]), "version_m_raw": ref(raw), "source_commit": SOURCE_COMMIT, "vcs_modified": False}
    invocations = {}
    for name in ("go-build", "negative-child-build", "go-test-build", "react-build", "core-control-build", "core-runtime-verifier-build", "core-control-go-version-m", "core-runtime-verifier-go-version-m", "validator-go-version-m", "validator-suite"):
        path = RAW / (name + ".invocation.json")
        row = load(path)
        native = row["native_exit"] if "native_exit" in row else row["exit"]
        require(native == 0, "nonzero native exit: " + name)
        invocations[name] = {"receipt": ref(path), "argv": row.get("argv", row.get("actualargv")),
                             "cwd": row["cwd"], "native_exit": native,
                             "stdout": row["stdout"] if isinstance(row["stdout"], dict) else ref(RAW / row["stdout"]),
                             "stderr": row["stderr"] if isinstance(row["stderr"], dict) else ref(RAW / row["stderr"])}
    suite = (RAW / "validator-suite.stdout").read_text(encoding="utf-8")
    top_pass = re.findall(r"^--- PASS: ([^\s]+)", suite, flags=re.MULTILINE)
    require(suite.rstrip().endswith("PASS") and top_pass, "validator test summary missing")
    payload = {"schema": "researchos.cp451-attach-combined-desktop-build-manifest.v1",
               "status": "ASSEMBLED_HASHED_NOT_LAUNCHED_PENDING_INDEPENDENT_PACKAGE_REVIEW",
               "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "owner": "codex:/root/attach_desktop_builder", "model": "gpt-6-sol", "reasoning_effort": "high",
               "scope": ref(SCOPE), "source_review": ref(REVIEW), "integration": ref(INTEGRATION),
               "source": {"worktree": str(SOURCE), "candidate_commit": SOURCE_COMMIT, "main_commit": MAIN_COMMIT,
                          "committed_tree": SOURCE_TREE, "candidate_clean": True, "main_tree_equal": True},
               "build": {"output": str(BUILD), "raw_receipts": str(RAW),
                         "input_count": composition["bound_full_input_count"],
                         "input_digest": result["build_input_digest"], "input_drift": result["drift"],
                         "input_before": ref(RAW / "inputs.before.json"), "input_after": ref(RAW / "inputs.after.json"),
                         "compiler_work_archive": ref(RAW / "compiler-work-archive.json"),
                         "result": ref(RAW / "result.json"), "descriptor": ref(DEST / "apps/desktop/resources/client-wire/descriptor.json"),
                         "invocations": invocations,
                         "compiler_input_boundary": "go-list inventory is broad; go -work/-x compiler commands are raw in receipts. Do not describe the broad inventory or archive as exact selected compile inputs."},
               "local_tests": {"validator_suite_native_exit": 0, "validator_top_level_pass_count": len(top_pass),
                               "validator_top_level_tests": top_pass,
                               "unchanged_UI_253_fixture_provenance": ref(OLD_MANIFEST),
                               "new_Core_15_plus_3_independent_source_test_provenance": ref(REVIEW),
                               "broad_UI_or_api_domain_retest": False},
               "package": {"root": str(DEST), "member_count": len(rows),
                           "bytes": sum(r["bytes"] for r in rows), "members": rows,
                           "module_count": len(descriptor["exact_module_source_inventory"]),
                           "React_asset_count": len(descriptor["compiled_React_asset_inventory"]),
                           "public_host_count": 32, "mu_pin": composition["mu_commit"],
                           "composition": ref(HERE / "composition.json"), "binaries": stamps,
                           "installation_manifest": ref(installer_path), "installation_acl_readback": ref(HERE / "acl-readback.json"),
                           "installer_current_user_single_ace": True},
               "source_modified": False, "activation": "NOT_STARTED", "GUI_first_use": False,
               "model_calls": 0, "real_API_calls": 0, "database_operations": 0,
               "package_independent_review": "PENDING", "formal_increment": 0, "parent_acceptance": False,
               "limitations": ["Package hash/source verification is local build evidence.",
                               "Ordinary GUI original-session launch and downstream live qualification remain Root follow-up after independent package review."]}
    with (HERE / "FINAL-manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": payload["status"], "members": len(rows), "validator_top_level_pass": len(top_pass),
                      "manifest_sha256": sha(HERE / "FINAL-manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
