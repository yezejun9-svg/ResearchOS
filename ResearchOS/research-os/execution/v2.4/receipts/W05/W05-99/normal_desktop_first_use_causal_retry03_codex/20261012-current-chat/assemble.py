"""Assemble the CP430 reviewed, unlaunched Desktop component distribution."""
import datetime
import hashlib
import json
import pathlib
import shutil
import subprocess

MAIN = pathlib.Path(r"D:/作品集/ResearchOS/research-os")
BOUND = MAIN / ".local/worktrees/w05-normal-first-use-contract-repair-20261012/.local/builds/normal-first-use-contract-repair-final-20261012"
CORE = pathlib.Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/native-folder-visibility-20261012/.local/builds/native-folder-visibility-20261012")
MU = MAIN / ".local/builds/current-chat-runtime-assets-20261012"
PUBLIC = MAIN / ".local/builds/current-chat-installed-runtime-components-20261012/public-host-root"
DEST = pathlib.Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-causal-retry03-20261012")
RECEIPT = pathlib.Path(__file__).resolve().parent
MAIN_HEAD = "84d6fc0f2018404170ec3fa4295c56cf4453a15a"
UI_COMMIT = "90b72d19c760974af46dc4243c56107e886d7cf6"
CORE_COMMIT = "b45008a754414cd795a4be396475aab8e74b2a8c"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
EXPECTED = {
    "control": "41eca2a248a64fdbe31359de3433e04addca3dd5f08230b6144bfe54ff1fdf5a",
    "verifier": "9ae7dc3d281951de7ff3af3aaf359c769d4305fa4b5907d1273517f51f5c0624",
    "validator": "cfdcbd5dd3c46cb5b44ad6c7e57b00b21a51126191ce2f3294de566d9399680e",
    "input": "e99cfe80d39fef7d797c505e4a6a3cf4906877f3b7cfcce3e05888164f35191b",
    "node.exe": "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6",
    "mu-worker.mjs": "2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441",
    "mu-worker.mjs.build.json": "ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular(path):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"not an approved regular file: {path}")
    return path


def exact_tree(root):
    return sorted(p for p in root.rglob("*") if p.is_file())


def git_blob(path):
    return subprocess.run(
        ["git", "show", f"{MAIN_HEAD}:{path}"], cwd=MAIN,
        capture_output=True, check=True,
    ).stdout


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def put(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    require(not DEST.exists(), "new package destination already exists")
    require(subprocess.run(["git", "rev-parse", "HEAD"], cwd=MAIN, capture_output=True,
                           check=True, text=True).stdout.strip() == MAIN_HEAD, "Main HEAD drift")
    scope = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp432/normal-firstuse-retry03-package-scope.json"
    require(sha(scope) == "529f39f15ed07551afbe2db36eef8b32a6ae44a77108d978bb280b257d670b2e", "scope drift")
    refs = [
        ("execution/v2.4/receipts/W05/W05-99/native_folder_visibility_review_codex/20261012-current-chat/review-01.json", "cb4d3b3c25fc22cb6520bee2b03539af0dcbeff0e8216c165d6dfbf812f45039"),
        ("execution/v2.4/receipts/W05/W05-99/native_folder_visibility_integration_codex/20261012-current-chat/integration.json", "0b783315cf0ee9e834680c14f9af5ed2f8298435e89698e3c74be5d56bf87f3d"),
        ("execution/v2.4/receipts/W05/W05-99/native_folder_visibility_codex/20261012-current-chat/source-bundle-final.json", "2a2c2796ff3bfed1feeb1c3a46c80b00c98b4f5df3210840b2f5b5cce80d62fd"),
        ("execution/v2.4/receipts/W05/W05-99/normal_desktop_first_use_causal_retry02_codex/20261012-current-chat/composition.json", "2894d86ad4e45af3832c7e8a5d399356b692158b739699914d5a5491dd2218cf"),
    ]
    for relative, expected in refs:
        require(sha(regular(MAIN / relative)) == expected, f"review/integration reference drift: {relative}")
    result = json.loads(regular(BOUND.parent / "normal-first-use-contract-repair-final-20261012-logs/result.json").read_text(encoding="utf-8"))
    descriptor = json.loads(regular(BOUND / "apps/desktop/resources/client-wire/descriptor.json").read_text(encoding="utf-8"))
    require(result["build_input_digest"] == EXPECTED["input"] and result["drift"] == [], "bound build drift")
    require(descriptor["build_input_digest"] == EXPECTED["input"] and descriptor["binary_sha256"] == EXPECTED["validator"], "descriptor drift")
    require(sha(regular(BOUND / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe")) == EXPECTED["validator"], "validator drift")
    module_rows = descriptor["exact_module_source_inventory"]
    require(len(module_rows) == 14, "unexpected module inventory")
    for row in module_rows:
        rel = "apps/desktop/" + row["path"]
        file = regular(BOUND / rel)
        require(sha(file) == row["sha256"] == hashlib.sha256(git_blob(rel)).hexdigest(), f"module/Main mismatch: {rel}")
    require(sha(regular(BOUND / "apps/desktop/package.json")) == hashlib.sha256(git_blob("apps/desktop/package.json")).hexdigest(), "package.json mismatch")
    react_rows = descriptor["compiled_React_asset_inventory"]
    require(len(react_rows) == 3, "unexpected React inventory")
    for row in react_rows:
        file = regular(BOUND / "apps/web/dist" / row["path"])
        require(sha(file) == row["sha256"] and file.stat().st_size == row["bytes"], f"React asset drift: {row['path']}")
    desktop = exact_tree(BOUND / "apps/desktop")
    web = exact_tree(BOUND / "apps/web/dist")
    public = exact_tree(PUBLIC)
    require(len(desktop) == 17 and len(web) == 3 and len(public) == 32, "shipped file count changed")
    for file in desktop + web + public:
        regular(file)
    public_rows = []
    for file in public:
        rel = file.relative_to(PUBLIC).as_posix()
        digest = sha(file)
        require(digest == hashlib.sha256(git_blob(rel)).hexdigest(), f"public/Main mismatch: {rel}")
        public_rows.append({"path": rel, "sha256": digest, "bytes": file.stat().st_size})
    require([sha(regular(CORE / name)) for name in ("control.exe", "runtime-verifier.exe")] ==
            [EXPECTED["control"], EXPECTED["verifier"]], "reviewed Core binary drift")
    for name in ("node.exe", "mu-worker.mjs", "mu-worker.mjs.build.json"):
        require(sha(regular(MU / name)) == EXPECTED[name], f"Mu asset drift: {name}")
    meta = json.loads((MU / "mu-worker.mjs.build.json").read_text(encoding="utf-8"))
    require(meta["mu_commit"] == MU_COMMIT and meta["bundle_sha256"] == EXPECTED["mu-worker.mjs"], "Mu metadata drift")
    preflight = {
        "schema": "researchos.cp432-component-preflight.v1", "main_head": MAIN_HEAD,
        "ui_source_commit": UI_COMMIT, "core_source_commit": CORE_COMMIT, "mu_source_commit": MU_COMMIT,
        "bound_full_input_count": 6441, "bound_full_input_digest": EXPECTED["input"], "bound_build_drift": [],
        "desktop_module_count": len(module_rows), "react_asset_count": len(react_rows),
        "public_count": len(public_rows), "package_preexisted": False,
        "control_sha256": EXPECTED["control"], "verifier_sha256": EXPECTED["verifier"],
        "validator_sha256": EXPECTED["validator"], "model_calls": 0, "activation": "NOT_STARTED",
    }
    put(RECEIPT / "preflight.json", preflight)
    DEST.mkdir(parents=True)
    rows = []
    def copy(source, rel, component):
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(source) == sha(target) and source.stat().st_size == target.stat().st_size, f"copy drift: {rel}")
        rows.append({"path": rel.as_posix(), "sha256": sha(target), "bytes": target.stat().st_size,
                     "component": component, "source": str(source)})
    for source in desktop:
        copy(source, source.relative_to(BOUND), "UI90B_FULL_BOUND")
    for source in web:
        copy(source, source.relative_to(BOUND), "UI90B_REACT_BOUND")
    for source in public:
        copy(source, source.relative_to(PUBLIC), "PUBLIC32_MAIN_AND_CORE_EQUIVALENT")
    control_dir = pathlib.Path("apps/desktop/resources/control")
    copy(CORE / "control.exe", control_dir / "researchos-control.exe", "CORE040D")
    copy(CORE / "runtime-verifier.exe", control_dir / "runtime-verifier.exe", "CORE040D")
    for name in ("node.exe", "mu-worker.mjs", "mu-worker.mjs.build.json"):
        copy(MU / name, control_dir / "runtime" / name, "MU8DF_LOCKED_ASSET")
    verifier_path = DEST / control_dir / "runtime-verifier.exe"
    manifest = {
        "schema": "researchos.runtime-verifier-installation.v1",
        "service_id": "researchos.runtime-qualification-verifier.v1",
        "protocol": "researchos.runtime-verifier/1",
        "executable": str(verifier_path),
        "executable_hash": "sha256:" + EXPECTED["verifier"],
        "source_commit": CORE_COMMIT,
        "arguments": [],
    }
    manifest_path = DEST / control_dir / "runtime-verifier-installation.json"
    put(manifest_path, manifest)
    rows.append({"path": (control_dir / manifest_path.name).as_posix(), "sha256": sha(manifest_path),
                 "bytes": manifest_path.stat().st_size, "component": "NEW_INSTALLATION_MANIFEST",
                 "source": "CP430_ASSEMBLY"})
    composition = {
        "schema": "researchos.native-first-use-causal-composition.v2",
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "package_root": str(DEST), "source_main_head": MAIN_HEAD,
        "component_vector": {"desktop_ui": UI_COMMIT, "core_control_verifier": CORE_COMMIT, "mu_sdk": MU_COMMIT},
        "desktop_full_input_count": 6441, "desktop_full_input_digest": EXPECTED["input"],
        "desktop_validator_sha256": EXPECTED["validator"], "desktop_descriptor_sha256": sha(DEST / "apps/desktop/resources/client-wire/descriptor.json"),
        "main_module_inventory": module_rows, "react_asset_inventory": react_rows,
        "public_host_assets": public_rows, "package_files": rows,
        "installation_manifest_path": str(manifest_path), "installation_manifest_sha256": sha(manifest_path),
        "default_control_exe": str(DEST / control_dir / "researchos-control.exe"),
        "control_override_used": False, "source_modified": False,
        "activation": "NOT_STARTED", "model_calls": 0, "installer_acceptance": False,
        "formal_increment": 0, "parent_acceptance": False,
    }
    put(RECEIPT / "composition.json", composition)
    print(json.dumps({"status": "ASSEMBLED_NOT_LAUNCHED", "package": str(DEST),
                      "package_files": len(rows), "composition_sha256": sha(RECEIPT / "composition.json"),
                      "installation_manifest_sha256": sha(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
