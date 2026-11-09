"""Read-only exact-member and VCS-stamp audit of the unlaunched package."""
import hashlib
import json
from pathlib import Path
import subprocess

SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
RAW = SOURCE / ".local/receipts/approved-readlane-combined-20261012"
HERE = Path(__file__).resolve().parent
GO = Path(r"D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe")
UI = "070e6cda24ec2fadca104873534febcedfb7ddc0"
CORE = "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def need(value, reason):
    if not value:
        raise RuntimeError(reason)

def main():
    composition = json.loads((HERE / "composition.json").read_bytes())
    preflight = json.loads((HERE / "preflight.json").read_bytes())
    root = Path(composition["package_root"])
    expected = {row["path"]: row for row in composition["package_files"]}
    actual = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
    need(len(expected) == len(actual) == 58 and set(expected) == set(actual), "package census mismatch")
    for relative, path in actual.items():
        row = expected[relative]
        need(not path.is_symlink() and sha(path) == row["sha256"] and path.stat().st_size == row["bytes"], "member mismatch: " + relative)
    desc = json.loads((root / "apps/desktop/resources/client-wire/descriptor.json").read_bytes())
    need(desc["build_input_digest"] == preflight["bound_input_digest"] == composition["bound_full_input_digest"], "descriptor binding mismatch")
    need(len(desc["exact_module_source_inventory"]) == 14 and len(desc["compiled_React_asset_inventory"]) == 3, "descriptor census mismatch")
    for row in desc["exact_module_source_inventory"]:
        need(sha(root / "apps/desktop" / row["path"]) == row["sha256"], "module descriptor mismatch")
    for row in desc["compiled_React_asset_inventory"]:
        need(sha(root / "apps/web/dist" / row["path"]) == row["sha256"], "React descriptor mismatch")
    control_dir = root / "apps/desktop/resources/control"
    installer = control_dir / "runtime-verifier-installation.json"
    config = json.loads(installer.read_bytes())
    verifier = control_dir / "runtime-verifier.exe"
    need(config["source_commit"] == CORE and config["executable"] == str(verifier) and
         config["executable_hash"] == "sha256:" + sha(verifier), "absolute verifier installation mismatch")
    acl = json.loads((HERE / "manifest-acl.json").read_bytes())
    need(acl["protected"] is True and acl["rule_count"] == 1 and acl["file_sha256"] == sha(installer), "manifest ACL evidence mismatch")
    binaries = {
        "desktop_validator": (root / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe", UI),
        "core_control": (control_dir / "researchos-control.exe", CORE),
        "core_verifier": (verifier, CORE),
    }
    stamps = {}
    for name, (path, commit) in binaries.items():
        raw = subprocess.check_output([str(GO), "version", "-m", str(path)])
        need(b"vcs.revision=" + commit.encode() in raw and b"vcs.modified=false" in raw, "VCS stamp mismatch: " + name)
        output = RAW / (name + ".go-version-m.raw")
        with output.open("xb") as stream:
            stream.write(raw)
        stamps[name] = {"path": str(path), "sha256": sha(path), "source_commit": commit,
                        "vcs_modified": False, "metadata_raw": str(output), "metadata_sha256": sha(output)}
    need(stamps["desktop_validator"]["sha256"] == desc["binary_sha256"], "new validator hash mismatch")
    need(stamps["core_control"]["sha256"] == preflight["reused_control_sha256"] and
         stamps["core_verifier"]["sha256"] == preflight["reused_verifier_sha256"], "reused Core hash mismatch")
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == UI, "Source HEAD changed")
    need(subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b"", "Source worktree dirty")
    save(HERE / "verification.json", {
        "schema": "researchos.cp444-readlane-package-verification.v1",
        "status": "COMPONENTS_HASHED_NOT_LAUNCHED", "package_root": str(root),
        "package_members": len(actual), "package_bytes": sum(p.stat().st_size for p in actual.values()),
        "desktop_module_count": 14, "React_asset_count": 3,
        "public_host_count": len(composition["public_host_assets"]),
        "full_build_input_count": preflight["bound_input_count"],
        "full_build_input_digest": preflight["bound_input_digest"], "build_drift": [],
        "VCS_stamps": stamps, "installation_manifest_sha256": sha(installer),
        "acl_protected_current_sid_single_ace": True, "source_clean": True,
        "activation": "NOT_STARTED", "model_calls": 0, "real_tool_calls": 0,
        "actual_first_use": False, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "COMPONENTS_HASHED_NOT_LAUNCHED", "members": len(actual),
                      "bytes": sum(p.stat().st_size for p in actual.values()),
                      "validator_sha256": stamps["desktop_validator"]["sha256"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
