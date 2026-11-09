"""Assemble a fresh 070e Desktop build with reviewed CB Core and fixed Mu assets."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

MAIN = Path(r"D:/作品集/ResearchOS/research-os")
SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
BUILD = SOURCE / ".local/builds/approved-readlane-combined-20261012"
RAW = SOURCE / ".local/receipts/approved-readlane-combined-20261012"
OLD = Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-combined-c381-20261012")
MU = MAIN / ".local/builds/current-chat-runtime-assets-20261012"
DEST = Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012")
HERE = Path(__file__).resolve().parent
OLD_HERE = MAIN / "execution/v2.4/receipts/W05/W05-99/approved_combined_desktop_build_codex/20261012-current-chat"
SCOPE = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp444/combined-readlane-package-scope.json"
UI = "070e6cda24ec2fadca104873534febcedfb7ddc0"
MAIN_COMMIT = "91218bdd3901bae94a2c1c90521a4d133c59026d"
CORE = "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
CORE_HASHES = {"researchos-control.exe": "326f70d5d9097d6f648bc4479a1e9a609c8969f1052a74ff13ddb93f550487a3",
               "runtime-verifier.exe": "28ea9cc1af6d7b7bbe96765b19b17e6ac08f77ac9e89dc781407b023910aa9eb"}
MU_HASHES = {"node.exe": "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6",
             "mu-worker.mjs": "2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441",
             "mu-worker.mjs.build.json": "ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd)

def regular(path):
    need(path.is_file() and not path.is_symlink(), "not a regular file: " + str(path))
    return path

def tree(root):
    return sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix())

def blob(relative):
    return git(MAIN, "show", MAIN_COMMIT + ":" + relative)

def main():
    need(not DEST.exists(), "output package already exists")
    need(sha(regular(SCOPE)) == "b3dc7d04bda53ab9637de5da67e540a0354dc9370a594fc5fb8f9d8b1fb59c2c", "CP444 scope drift")
    need(git(SOURCE, "rev-parse", "HEAD").decode().strip() == UI, "UI source HEAD changed")
    need(git(SOURCE, "status", "--porcelain=v1") == b"", "UI source worktree dirty")
    ui_tree = git(SOURCE, "rev-parse", UI + "^{tree}").decode().strip()
    main_tree = git(MAIN, "rev-parse", MAIN_COMMIT + "^{tree}").decode().strip()
    need(ui_tree == main_tree == "eee694bdad48a45282cf9884f9b5ef21ee0a76e3", "UI/Main tree mismatch")
    need(git(MAIN, "rev-parse", "HEAD").decode().strip() == MAIN_COMMIT, "Main HEAD changed")
    need(sha(regular(OLD_HERE / "manifest.json")) == "bddb0955512fc236807cc71222df038478a33b05fc166bcd8691c328ca8fb774", "old manifest bytes drift")
    need(sha(regular(OLD_HERE / "correction-01.json")) == "12ebc13e1ac4ad15edc8cb813797ddb2ee8e67c58d9c60028e36d5d584e6e49a", "old correction drift")
    need(sha(regular(OLD_HERE / "manifest-supplement-01.json")) == "f6720ce457149ec95903d9c38cdc8bd7104601f170b96ea9e93815fb572fdbf5", "old supplement drift")
    supplement = json.loads((OLD_HERE / "manifest-supplement-01.json").read_bytes())
    need(supplement["field_precedence"]["effective_value_for_review"] == "2936ca3097bc2c2d6cd6fd2e9af40756d25d32f8", "old Core tree correction mismatch")
    old_comp = json.loads(regular(OLD_HERE / "composition.json").read_bytes())
    need(sha(OLD_HERE / "composition.json") == "6a914b4e08d3ab3c16f50942accff12bdc29be8e1cec455a13c4ca22322c1b98", "old Core package composition drift")
    need(old_comp["committed_source_tree"] == supplement["field_precedence"]["effective_value_for_review"], "old composition tree mismatch")
    old_dir = OLD / "apps/desktop/resources/control"
    for name, expected in CORE_HASHES.items():
        need(sha(regular(old_dir / name)) == expected, "reviewed Core binary mismatch: " + name)
    old_install = json.loads(regular(old_dir / "runtime-verifier-installation.json").read_bytes())
    need(old_install["source_commit"] == CORE and old_install["executable_hash"] == "sha256:" + CORE_HASHES["runtime-verifier.exe"], "old installation manifest mismatch")
    for name, expected in MU_HASHES.items():
        need(sha(regular(MU / name)) == expected, "fixed Mu mismatch: " + name)
    mu_meta = json.loads((MU / "mu-worker.mjs.build.json").read_bytes())
    need(mu_meta["mu_commit"] == MU_COMMIT and mu_meta["bundle_sha256"] == MU_HASHES["mu-worker.mjs"] and
         mu_meta["sdk_version"] == "0.87.1" and mu_meta["esbuild_version"] == "0.28.2", "Mu provenance mismatch")
    result = json.loads(regular(RAW / "result.json").read_bytes())
    tests = json.loads(regular(HERE / "bound-tests.json").read_bytes())
    descriptor = json.loads(regular(BUILD / "apps/desktop/resources/client-wire/descriptor.json").read_bytes())
    inputs = json.loads(regular(RAW / "inputs.before.json").read_bytes())
    need(result["status"] == "BUILT_NOT_TESTED" and result["drift"] == [] and len(inputs) == 6444, "fresh bound build drift")
    need(result["build_input_digest"] == tests["build_input_digest"] == descriptor["build_input_digest"] and
         tests["unique_desktop_tests"] == 253, "fresh build/test binding mismatch")
    need(sha(regular(BUILD / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe")) == descriptor["binary_sha256"], "new validator mismatch")
    desktop = tree(BUILD / "apps/desktop")
    web = tree(BUILD / "apps/web/dist")
    public_names = [row["path"] for row in old_comp["public_host_assets"]]
    need(len(desktop) == 17 and len(web) == 3 and len(public_names) == 32, "component census mismatch")
    need(len(descriptor["exact_module_source_inventory"]) == 14 and len(descriptor["compiled_React_asset_inventory"]) == 3, "descriptor census mismatch")
    for row in descriptor["exact_module_source_inventory"]:
        rel = "apps/desktop/" + row["path"]
        need(sha(regular(BUILD / rel)) == row["sha256"] == hashlib.sha256(blob(rel)).hexdigest(), "new UI module/Main mismatch: " + rel)
    for row in descriptor["compiled_React_asset_inventory"]:
        need(sha(regular(BUILD / "apps/web/dist" / row["path"])) == row["sha256"], "React asset mismatch: " + row["path"])
    public = []
    for rel in public_names:
        file = regular(SOURCE / rel)
        need(sha(file) == hashlib.sha256(blob(rel)).hexdigest(), "published Source/Main mismatch: " + rel)
        public.append(file)
    preflight = {"schema": "researchos.cp444-readlane-combined-preflight.v1",
                 "source_vector": {"desktop_ui_and_new_validator": UI, "core_control_and_verifier_reused": CORE, "mu_sdk": MU_COMMIT},
                 "ui_source_tree": ui_tree, "integrated_main_tree": main_tree,
                 "reviewed_core_tree": supplement["field_precedence"]["effective_value_for_review"],
                 "scope_sha256": sha(SCOPE), "old_correction_sha256": sha(OLD_HERE / "correction-01.json"),
                 "old_supplement_sha256": sha(OLD_HERE / "manifest-supplement-01.json"),
                 "bound_input_count": len(inputs), "bound_input_digest": result["build_input_digest"], "drift": [],
                 "new_validator_sha256": descriptor["binary_sha256"], "desktop_module_count": 14,
                 "React_asset_count": 3, "public_host_count": 32,
                 "reused_control_sha256": CORE_HASHES["researchos-control.exe"],
                 "reused_verifier_sha256": CORE_HASHES["runtime-verifier.exe"],
                 "package_preexisted": False, "activation": "NOT_STARTED", "model_calls": 0,
                 "formal_increment": 0, "parent_acceptance": False}
    put(HERE / "preflight.json", preflight)
    DEST.mkdir(parents=True)
    rows = []
    def copy(file, relative, component):
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        need(sha(file) == sha(target) and file.stat().st_size == target.stat().st_size, "copy mismatch: " + relative.as_posix())
        rows.append({"path": relative.as_posix(), "sha256": sha(target), "bytes": target.stat().st_size,
                     "component": component, "source": str(file)})
    for file in desktop:
        copy(file, file.relative_to(BUILD), "UI_070E_FRESH_BOUND")
    for file in web:
        copy(file, file.relative_to(BUILD), "REACT_070E_FRESH_BOUND")
    for file in public:
        copy(file, file.relative_to(SOURCE), "PUBLIC32_070E_EQUALS_MAIN912")
    control_dir = Path("apps/desktop/resources/control")
    for name in CORE_HASHES:
        copy(old_dir / name, control_dir / name, "CORE_CB_REVIEWED_REUSED")
    for name in MU_HASHES:
        copy(MU / name, control_dir / "runtime" / name, "MU_8DF_FIXED")
    manifest_path = DEST / control_dir / "runtime-verifier-installation.json"
    put(manifest_path, {"schema": "researchos.runtime-verifier-installation.v1",
                        "service_id": "researchos.runtime-qualification-verifier.v1",
                        "protocol": "researchos.runtime-verifier/1",
                        "executable": str(DEST / control_dir / "runtime-verifier.exe"),
                        "executable_hash": "sha256:" + CORE_HASHES["runtime-verifier.exe"],
                        "source_commit": CORE, "arguments": []})
    rows.append({"path": (control_dir / manifest_path.name).as_posix(), "sha256": sha(manifest_path),
                 "bytes": manifest_path.stat().st_size, "component": "NEW_INSTALLATION_MANIFEST", "source": str(HERE / "assemble-readlane.py")})
    need(len(rows) == 58, "assembled package count mismatch")
    composition = {"schema": "researchos.cp444-readlane-combined-composition.v1",
                   "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "package_root": str(DEST),
                   "ui_source_commit": UI, "integrated_main_commit": MAIN_COMMIT,
                   "ui_source_tree": ui_tree, "main_committed_tree": main_tree,
                   "reviewed_core_source_commit": CORE,
                   "reviewed_core_tree": supplement["field_precedence"]["effective_value_for_review"],
                   "source_vector": preflight["source_vector"],
                   "bound_full_input_count": len(inputs), "bound_full_input_digest": result["build_input_digest"],
                   "new_validator_sha256": descriptor["binary_sha256"],
                   "new_descriptor_sha256": sha(DEST / "apps/desktop/resources/client-wire/descriptor.json"),
                   "module_inventory": descriptor["exact_module_source_inventory"],
                   "React_asset_inventory": descriptor["compiled_React_asset_inventory"],
                   "public_host_assets": [{"path": p.relative_to(SOURCE).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in public],
                   "package_files": rows, "installation_manifest_path": str(manifest_path),
                   "installation_manifest_sha256": sha(manifest_path),
                   "default_control_exe": str(DEST / control_dir / "researchos-control.exe"),
                   "control_override_used": False, "source_modified": False,
                   "activation": "NOT_STARTED", "model_calls": 0, "real_tool_calls": 0,
                   "actual_first_use": False, "installer_acceptance": False,
                   "formal_increment": 0, "parent_acceptance": False}
    put(HERE / "composition.json", composition)
    print(json.dumps({"status": "ASSEMBLED_NOT_LAUNCHED", "package": str(DEST),
                      "package_files": len(rows), "composition_sha256": sha(HERE / "composition.json"),
                      "manifest_sha256": sha(manifest_path)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
