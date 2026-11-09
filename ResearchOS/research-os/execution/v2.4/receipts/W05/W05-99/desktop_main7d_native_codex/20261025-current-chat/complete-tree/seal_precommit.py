"""Seal tested seven-file source and append-only diagnostics before commit."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-main7d-native-20261025")
spec = importlib.util.spec_from_file_location("build_development", ROOT / "apps/desktop/build-development.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(name, value):
    with (HERE / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


freeze = read(HERE / "SOURCE-FREEZE-02.json")
source = builder.source_snapshot()
if source["digest"] != freeze["source_snapshot_digest"] or set(source["candidate_delta"]) != builder.ALLOWLIST:
    raise SystemExit("r2 source freeze no longer current")
for row in source["files"]:
    if row["path"] in builder.ALLOWLIST and row["sha256"] != freeze["seven_file_hashes"][row["path"]]["sha256"]:
        raise SystemExit("seven-file source hash changed")
if digest(HERE / "SOURCE-FREEZE-02.patch") != freeze["patch"]["sha256"]:
    raise SystemExit("r2 patch hash changed")
build = read(HERE / "build-01/result.json")
manifest = read(HERE / "build-01/development-manifest.json")
if build["status"] != "BUILT_NOT_NATIVE_TESTED" or build["source_drift"] or build["public_vendor_drift"] or \
   build["manifest_sha256"] != digest(HERE / "build-01/development-manifest.json") or \
   manifest["source"]["digest"] != freeze["source_snapshot_digest"] or \
   manifest["source"]["seven_scoped_source_sha256"] != {p: item["sha256"] for p, item in freeze["seven_file_hashes"].items()}:
    raise SystemExit("complete builder result differs from r2 source")
if read(HERE / "build-01/source.before.json") != read(HERE / "build-01/source.after.json") or \
   read(HERE / "build-01/mu-vendor-5083.before.json") != read(HERE / "build-01/mu-vendor-5083.after.json") or \
   read(HERE / "build-01/mu-compiled-inputs.before.json") != read(HERE / "build-01/mu-compiled-inputs.after.json") or \
   read(HERE / "build-01/core-verifier-go-inputs.before.json") != read(HERE / "build-01/core-verifier-go-inputs.after.json"):
    raise SystemExit("compiler or public source closure drift")
for folder in (HERE / "build-01/commands").iterdir():
    if folder.is_dir() and read(folder / "result.json")["native_exit"] != 0:
        raise SystemExit(f"build subcommand failed: {folder.name}")
for suffix in ["focused-02.pre-python-bundle-tests", "focused-02.pre-node-launcher-smoke-tests",
               "focused-03.pre-python-bundle-tests", "postbuild-01.pre-python-built-bundle",
               "postbuild-01.pre-node-sealed-dryrun", "postbuild-01.pre-nearest-desktop-tests",
               "postbuild-02.pre-python-bundle-verbose", "resources-01.pre-installed-resources",
               "precommit-01.pre-patch-apply-cached-check"]:
    if (HERE / (suffix + ".native-exit.txt")).read_text(encoding="ascii").strip() != "0":
        raise SystemExit(f"required focused evidence failed: {suffix}")
if (HERE / "build-01.pre-build.native-exit.txt").read_text(encoding="ascii").strip() != "0":
    raise SystemExit("outer complete builder native exit missing")
if Path(build["output"]).joinpath("development-manifest.json").read_bytes() != (HERE / "build-01/development-manifest.json").read_bytes():
    raise SystemExit("builder output/canonical manifest copy differs")
if Path(build["output"]).joinpath("development-manifest.json").is_symlink():
    raise SystemExit("builder manifest redirected")
status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=no"],
                        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8", "replace").splitlines()
if any("apps/desktop/main/main.js" not in line for line in status):
    raise SystemExit("tracked source outside seven-file scope")
dryrun_state = ROOT / ".local/desktop-state-dryrun-20261025-01"
if dryrun_state.exists():
    raise SystemExit("dry-run created runtime state")

diagnostics = {
    "schema": "researchos.desktop-complete-tree-diagnostics.v1",
    "mode": "DEVELOPMENT_ONLY_NO_NATIVE_LAUNCH",
    "formal_increment": 0,
    "attempts": [
        {"id": "focused-01", "status": "FAILED", "failed_invocation": "python-bundle-tests",
         "native_exit": 1, "reason": "Windows read-only Git object in test-only temporary repo caused tearDown shutil.rmtree WinError5",
         "recipe": "focused-01.pre.json", "stderr": "focused-01.pre-python-bundle-tests.stderr.raw",
         "preceding": "py-ast,node-check-launcher,node-check-main all exit0"},
        {"id": "focused-02", "status": "PASSED_WITH_SKIPS", "python": "5 run, 3 pass, 2 skip",
         "node": "6 pass, 0 skip", "reason": "test-only cleanup corrected, source unchanged except scoped test file"},
        {"id": "freeze-01", "status": "INTERRUPTED_NOT_FROZEN", "controller_exit": 1,
         "native_child_exit_capture": "ABSENT", "runner_pid": 94808, "child_pid": 39032,
         "post_interrupt_process_check": "both absent", "reason": "overbroad 36186 tracked files included unrelated history; source closure design superseded before build",
         "record": "freeze-01.interruption.json"},
        {"id": "focused-03", "status": "PASSED_WITH_SKIPS", "python": "5 run, 3 pass, 2 skip",
         "reason": "Go/Mu exact input closure revision, no GUI/Core"},
        {"id": "freeze-02", "status": "FROZEN", "manifest": "SOURCE-FREEZE-02.json",
         "patch": "SOURCE-FREEZE-02.patch"},
        {"id": "build-01", "status": "BUILT_NOT_NATIVE_TESTED", "native_exit": 0,
         "source_revisions_after_freeze": 0, "build_failed_attempts": 0,
         "builder_subcommands": 7, "builder_subcommands_nonzero": 0,
         "client_wire_subcommands": 9, "client_wire_subcommands_nonzero": 0},
        {"id": "postbuild-01", "status": "PASSED_WITH_SKIP", "python": "5 run, 4 pass, 1 skip",
         "sealed_dry_run_exit": 0, "nearest_desktop_tests": "5 pass", "runtime_state_created": False},
        {"id": "resources-01", "status": "PURE_STATIC_PASS", "native_exit": 0},
        {"id": "postbuild-02", "status": "PASSED_WITH_SKIP", "python": "5 run, 4 pass, 1 skip",
         "purpose": "capture exact symlink skip reason"},
    ],
    "skips": [
        {"case": "test_actual_build_manifest_when_explicitly_supplied", "attempts": ["focused-01", "focused-02", "focused-03"],
         "reason": "RESEARCHOS_DEVELOPMENT_BUNDLE not set before build; later postbuild-01/02 case passed"},
        {"case": "test_exact_copy_and_tree_refuse_redirected_source", "attempts": ["focused-01", "focused-02", "focused-03", "postbuild-01", "postbuild-02"],
         "reason": "Windows file-symlink creation denied WinError1314; Node junction alias negative passed in focused-02",
         "evidence": "postbuild-02.pre-python-bundle-verbose.stderr.raw"},
    ],
    "native_GUI_Core_started": False,
    "original_data_or_credentials_accessed": False,
}
put("diagnostics.json", diagnostics)
precommit = {
    "schema": "researchos.desktop-complete-tree-precommit.v1",
    "base_commit": freeze["base_commit"], "base_tree": freeze["base_tree"],
    "scope_sha256": freeze["scope_sha256"],
    "seven_file_source_hashes": freeze["seven_file_hashes"],
    "source_snapshot_digest": freeze["source_snapshot_digest"],
    "patch_sha256": freeze["patch"]["sha256"],
    "build_result_sha256": digest(HERE / "build-01/result.json"),
    "development_manifest_sha256": build["manifest_sha256"],
    "go_compiled_input_manifest_sha256": digest(HERE / "build-01/core-verifier-go-inputs.before.json"),
    "mu_vendor_5083_manifest_sha256": digest(HERE / "build-01/mu-vendor-5083.before.json"),
    "mu_compiled_input_manifest_sha256": digest(HERE / "build-01/mu-compiled-inputs.before.json"),
    "checked_runtime_resources_sha256": digest(HERE / "resources-01.pre-installed-resources.stdout.raw"),
    "dry_run_sha256": digest(HERE / "postbuild-01.pre-node-sealed-dryrun.stdout.raw"),
    "diagnostics_sha256": digest(HERE / "diagnostics.json"),
    "git_apply_cached_check_exit": 0,
    "source_worktree_tracked_dirty": status,
    "status": "CANDIDATE_PRECOMMIT_NO_NATIVE_ACCEPTANCE",
}
put("PRECOMMIT-MANIFEST.json", precommit)
print(json.dumps({"precommit_sha256": digest(HERE / "PRECOMMIT-MANIFEST.json"),
                  "diagnostics_sha256": precommit["diagnostics_sha256"],
                  "source_snapshot_digest": source["digest"], "files": len(freeze["seven_file_hashes"])}, ensure_ascii=False))
