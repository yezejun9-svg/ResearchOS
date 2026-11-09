"""Assemble the approved, unlaunched CB desktop package from locked components."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

MAIN = Path(r"D:/作品集/ResearchOS/research-os")
SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012")
BUILD = SOURCE / ".local/builds/approved-combined-first-use-20261012"
RAW = SOURCE / ".local/receipts/approved-combined-first-use-20261012"
MU = MAIN / ".local/builds/current-chat-runtime-assets-20261012"
PUBLIC_REFERENCE = MAIN / ".local/builds/current-chat-installed-runtime-components-20261012/public-host-root"
DEST = Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-combined-c381-20261012")
HERE = Path(__file__).resolve().parent
SCOPE = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp436/combined-desktop-package-scope.json"
CB = "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
MAIN_COMMIT = "c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
MU_HASHES = {"node.exe": "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6",
             "mu-worker.mjs": "2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441",
             "mu-worker.mjs.build.json": "ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok, why):
    if not ok:
        raise RuntimeError(why)

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd)

def regular(path):
    require(path.is_file() and not path.is_symlink(), "source is not a regular file: " + str(path))
    return path

def tree(root):
    return sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix())

def blob(rel):
    return git(MAIN, "show", MAIN_COMMIT + ":" + rel)

def main():
    require(not DEST.exists(), "package destination already exists")
    require(sha(regular(SCOPE)) == "087554522317b0ccbbb99677dcc98e5d53105b2b6aac4cb25e2d49c06d4858de", "CP436 scope drift")
    require(git(SOURCE, "rev-parse", "HEAD").decode().strip() == CB, "source HEAD drift")
    require(git(SOURCE, "status", "--porcelain=v1") == b"", "source worktree dirty")
    source_tree = git(SOURCE, "rev-parse", CB + "^{tree}").decode().strip()
    main_tree = git(MAIN, "rev-parse", MAIN_COMMIT + "^{tree}").decode().strip()
    require(source_tree == main_tree, "whole committed tree mismatch")
    result = json.loads(regular(RAW / "result.json").read_bytes())
    descriptor_path = BUILD / "apps/desktop/resources/client-wire/descriptor.json"
    descriptor = json.loads(regular(descriptor_path).read_bytes())
    validation = json.loads(regular(HERE / "bound-verification.json").read_bytes())
    inputs = json.loads(regular(RAW / "inputs.before.json").read_bytes())
    require(result["status"] == "BUILT_NOT_TESTED" and result["drift"] == [], "bound build drift")
    require(len(inputs) == 6444 and result["build_input_digest"] == descriptor["build_input_digest"] == validation["build_input_digest"], "input binding mismatch")
    require(validation["status"] == "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "bound local tests not passed")
    require(sha(regular(BUILD / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe")) == descriptor["binary_sha256"], "validator mismatch")
    desktop = tree(BUILD / "apps/desktop")
    web = tree(BUILD / "apps/web/dist")
    public_names = [p.relative_to(PUBLIC_REFERENCE).as_posix() for p in tree(PUBLIC_REFERENCE)]
    require(len(desktop) == 17 and len(web) == 3 and len(public_names) == 32, "package base member count mismatch")
    require(len(descriptor["exact_module_source_inventory"]) == 14 and len(descriptor["compiled_React_asset_inventory"]) == 3, "descriptor member count mismatch")
    for row in descriptor["exact_module_source_inventory"]:
        rel = "apps/desktop/" + row["path"]
        require(sha(regular(BUILD / rel)) == row["sha256"] == hashlib.sha256(blob(rel)).hexdigest(), "module/Main mismatch: " + rel)
    for row in descriptor["compiled_React_asset_inventory"]:
        require(sha(regular(BUILD / "apps/web/dist" / row["path"])) == row["sha256"], "React asset mismatch")
    require(sha(regular(BUILD / "apps/desktop/package.json")) == hashlib.sha256(blob("apps/desktop/package.json")).hexdigest(), "desktop package mismatch")
    public = []
    for rel in public_names:
        source = regular(SOURCE / rel)
        require(sha(source) == sha(regular(PUBLIC_REFERENCE / rel)) == hashlib.sha256(blob(rel)).hexdigest(), "published source mismatch: " + rel)
        public.append(source)
    for name, expected in MU_HASHES.items():
        require(sha(regular(MU / name)) == expected, "Mu fixed asset mismatch: " + name)
    mu_meta = json.loads((MU / "mu-worker.mjs.build.json").read_bytes())
    require(mu_meta["mu_commit"] == MU_COMMIT and mu_meta["bundle_sha256"] == MU_HASHES["mu-worker.mjs"], "Mu provenance mismatch")
    control = regular(BUILD / "control.exe")
    verifier = regular(BUILD / "runtime-verifier.exe")
    require(sha(control) == validation["control_sha256"] and sha(verifier) == validation["verifier_sha256"], "CB Core hashes mismatch")
    preflight = {"schema": "researchos.cp436-combined-desktop-preflight.v1",
                 "scope_sha256": sha(SCOPE), "source_commit": CB, "integrated_main_commit": MAIN_COMMIT,
                 "committed_source_tree": source_tree, "main_committed_tree": main_tree,
                 "component_vector": {"desktop_full_build": CB, "core_control_and_verifier": CB, "mu_sdk": MU_COMMIT},
                 "bound_input_count": len(inputs), "bound_input_digest": result["build_input_digest"],
                 "bound_input_drift": [], "control_sha256": sha(control), "verifier_sha256": sha(verifier),
                 "validator_sha256": descriptor["binary_sha256"], "desktop_count": len(desktop),
                 "React_count": len(web), "public32_count": len(public),
                 "package_preexisted": False, "activation": "NOT_STARTED", "model_calls": 0,
                 "formal_increment": 0, "parent_acceptance": False}
    put(HERE / "preflight.json", preflight)
    DEST.mkdir(parents=True)
    rows = []
    def copy(source, relative, component):
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(source) == sha(target) and source.stat().st_size == target.stat().st_size, "copy drift: " + relative.as_posix())
        rows.append({"path": relative.as_posix(), "sha256": sha(target), "bytes": target.stat().st_size,
                     "component": component, "source": str(source)})
    for file in desktop:
        copy(file, file.relative_to(BUILD), "CB_DESKTOP_BOUND")
    for file in web:
        copy(file, file.relative_to(BUILD), "CB_REACT_BOUND")
    for file in public:
        copy(file, file.relative_to(SOURCE), "PUBLIC32_CB_EQUALS_C381")
    control_dir = Path("apps/desktop/resources/control")
    copy(control, control_dir / "researchos-control.exe", "CB_CORE")
    copy(verifier, control_dir / "runtime-verifier.exe", "CB_CORE")
    for name in MU_HASHES:
        copy(MU / name, control_dir / "runtime" / name, "MU8DF_FIXED")
    manifest_path = DEST / control_dir / "runtime-verifier-installation.json"
    put(manifest_path, {"schema": "researchos.runtime-verifier-installation.v1",
                        "service_id": "researchos.runtime-qualification-verifier.v1",
                        "protocol": "researchos.runtime-verifier/1",
                        "executable": str(DEST / control_dir / "runtime-verifier.exe"),
                        "executable_hash": "sha256:" + sha(verifier),
                        "source_commit": CB, "arguments": []})
    rows.append({"path": (control_dir / manifest_path.name).as_posix(),
                 "sha256": sha(manifest_path), "bytes": manifest_path.stat().st_size,
                 "component": "NEW_INSTALLATION_MANIFEST", "source": str(HERE / "assemble-combined.py")})
    require(len(rows) == 58, "assembled count mismatch")
    composition = {"schema": "researchos.cp436-approved-combined-desktop-composition.v1",
                   "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "package_root": str(DEST),
                   "source_commit": CB, "integrated_main_commit": MAIN_COMMIT,
                   "committed_source_tree": source_tree,
                   "component_vector": preflight["component_vector"],
                   "desktop_full_input_count": len(inputs),
                   "desktop_full_input_digest": result["build_input_digest"],
                   "desktop_validator_sha256": descriptor["binary_sha256"],
                   "desktop_descriptor_sha256": sha(DEST / "apps/desktop/resources/client-wire/descriptor.json"),
                   "module_inventory": descriptor["exact_module_source_inventory"],
                   "React_asset_inventory": descriptor["compiled_React_asset_inventory"],
                   "public_host_assets": [{"path": p.relative_to(SOURCE).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in public],
                   "package_files": rows, "installation_manifest_path": str(manifest_path),
                   "installation_manifest_sha256": sha(manifest_path),
                   "default_control_exe": str(DEST / control_dir / "researchos-control.exe"),
                   "control_override_used": False, "source_modified": False,
                   "activation": "NOT_STARTED", "model_calls": 0, "tool_calls": 0,
                   "installer_acceptance": False, "formal_increment": 0, "parent_acceptance": False,
                   "previous_failed_attempt": str(HERE / "stopped.json")}
    put(HERE / "composition.json", composition)
    print(json.dumps({"status": "ASSEMBLED_NOT_LAUNCHED", "package": str(DEST),
                      "package_files": len(rows), "composition_sha256": sha(HERE / "composition.json"),
                      "manifest_sha256": sha(manifest_path)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
