"""Read-only exact package and bound Core metadata verification."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012")
RAW = SOURCE / ".local/receipts/approved-combined-first-use-20261012"
GO = Path(r"D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe")
CB = "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def need(value, why):
    if not value:
        raise RuntimeError(why)

def main():
    composition = json.loads((HERE / "composition.json").read_bytes())
    preflight = json.loads((HERE / "preflight.json").read_bytes())
    root = Path(composition["package_root"])
    expected = {row["path"]: row for row in composition["package_files"]}
    actual = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
    need(len(expected) == len(actual) == 58 and set(expected) == set(actual), "package census mismatch")
    for rel, file in actual.items():
        row = expected[rel]
        need(not file.is_symlink() and sha(file) == row["sha256"] and file.stat().st_size == row["bytes"], "package member mismatch: " + rel)
    desc = json.loads((root / "apps/desktop/resources/client-wire/descriptor.json").read_bytes())
    need(desc["build_input_digest"] == composition["desktop_full_input_digest"] == preflight["bound_input_digest"], "build descriptor binding mismatch")
    need(sha(root / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe") == desc["binary_sha256"], "validator binary mismatch")
    for row in desc["exact_module_source_inventory"]:
        need(sha(root / "apps/desktop" / row["path"]) == row["sha256"], "module mismatch: " + row["path"])
    for row in desc["compiled_React_asset_inventory"]:
        need(sha(root / "apps/web/dist" / row["path"]) == row["sha256"], "React asset mismatch: " + row["path"])
    manifest = root / "apps/desktop/resources/control/runtime-verifier-installation.json"
    verifier = root / "apps/desktop/resources/control/runtime-verifier.exe"
    config = json.loads(manifest.read_bytes())
    need(config["executable"] == str(verifier) and config["executable_hash"] == "sha256:" + sha(verifier), "absolute verifier manifest mismatch")
    need(config["source_commit"] == CB, "manifest Source stamp mismatch")
    acl = json.loads((HERE / "manifest-acl.json").read_bytes())
    need(acl["protected"] is True and acl["rule_count"] == 1 and acl["file_sha256"] == sha(manifest), "protected ACL evidence mismatch")
    stamps = {}
    for name in ("researchos-control.exe", "runtime-verifier.exe"):
        binary = root / "apps/desktop/resources/control" / name
        output = subprocess.check_output([str(GO), "version", "-m", str(binary)], text=True)
        need("vcs.revision=" + CB in output and "vcs.modified=false" in output, "Core VCS stamp mismatch: " + name)
        stamps[name] = {"sha256": sha(binary), "vcs_revision": CB, "vcs_modified": False,
                        "go_version_m_output_sha256": hashlib.sha256(output.encode()).hexdigest()}
        (RAW / (name + ".go-version-m.txt")).write_text(output, encoding="utf-8", newline="\n")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == CB, "frozen source HEAD changed")
    need(subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b"", "frozen source dirty")
    result = {"schema": "researchos.cp436-combined-package-readonly-verification.v1",
              "status": "COMPONENTS_HASHED_NOT_LAUNCHED", "package_root": str(root),
              "package_file_count": len(actual), "desktop_module_count": len(desc["exact_module_source_inventory"]),
              "React_asset_count": len(desc["compiled_React_asset_inventory"]),
              "public_host_asset_count": len(composition["public_host_assets"]),
              "bound_input_count": preflight["bound_input_count"], "bound_input_digest": desc["build_input_digest"],
              "bound_input_drift": preflight["bound_input_drift"],
              "Core_VCS": stamps, "installation_manifest_sha256": sha(manifest),
              "acl_protected_current_sid_single_ace": True,
              "model_calls": 0, "tool_calls": 0, "activation": "NOT_STARTED",
              "formal_increment": 0, "parent_acceptance": False}
    put(HERE / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
