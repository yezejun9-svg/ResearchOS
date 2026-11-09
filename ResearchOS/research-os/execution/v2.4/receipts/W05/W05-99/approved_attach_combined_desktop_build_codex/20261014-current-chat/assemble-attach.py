"""Build new Core and assemble one source-bound Desktop package."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MAIN = Path("D:/作品集/ResearchOS/research-os")
SOURCE = Path("C:/Users/yqyyds/.codex/researchos-build-worktrees/attach-synchronous-completion-20261012")
BUILD = SOURCE / ".local/builds/approved-attach-combined-20261014"
RAW = SOURCE / ".local/receipts/approved-attach-combined-20261014"
OLD = Path("C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012")
DEST = Path("C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014")
HERE = Path(__file__).resolve().parent
OLD_COMP = MAIN / "execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat/composition.json"
SCOPE = MAIN / "execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp451/combined-attach-package-scope.json"
GO = Path("D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe")
PY = Path("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")
SOURCE_COMMIT = "b955c8665281193d5cbf90a146f936c9212c7940"
SOURCE_TREE = "00d44e133662227b115eb3b16bef3d4edcc35630"
MAIN_COMMIT = "c465d1356480d6e6a90da84656724f9fc02b31c7"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
SCOPE_SHA = "3c40cdbff8ec015ebd7ba5a9793df0d7866a2e39668575e808b6451b45b1bc1e"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd).decode().strip()


def snapshot():
    require(sha(SCOPE) == SCOPE_SHA, "scope changed")
    require(git(SOURCE, "rev-parse", "HEAD") == SOURCE_COMMIT, "source HEAD changed")
    require(git(SOURCE, "rev-parse", "HEAD^{tree}") == SOURCE_TREE, "source tree changed")
    require(git(SOURCE, "status", "--porcelain=v1") == "", "source dirty")
    require(git(MAIN, "rev-parse", "HEAD") == MAIN_COMMIT, "Main HEAD changed")
    require(git(MAIN, "rev-parse", "HEAD^{tree}") == SOURCE_TREE, "Main tree changed")


def invoke(name, argv, cwd, env, timeout=240):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, capture_output=True, timeout=timeout)
    out = RAW / (name + ".stdout")
    err = RAW / (name + ".stderr")
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    row = {"argv": [str(a) for a in argv], "cwd": str(cwd), "started_at": started,
           "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "native_exit": proc.returncode,
           "stdout": {"path": str(out), "sha256": sha(out), "bytes": out.stat().st_size},
           "stderr": {"path": str(err), "sha256": sha(err), "bytes": err.stat().st_size},
           "environment": {k: env.get(k) for k in ("GOTOOLCHAIN", "GOENV", "GOROOT", "GOPATH", "GOMODCACHE", "GOCACHE", "GOTMPDIR", "GOPROXY", "GOSUMDB")}}
    put(RAW / (name + ".invocation.json"), row)
    require(proc.returncode == 0, name + " exited " + str(proc.returncode))
    return proc.stdout.decode("utf-8", errors="replace")


def go_env():
    env = dict(os.environ)
    env.update(GOTOOLCHAIN="local", GOENV="off", GOROOT=str(GO.parent.parent),
               GOPATH="D:/作品集/ResearchOS/research-os/.local/tools/gopath",
               GOMODCACHE="D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod",
               GOCACHE=str(BUILD / "go-cache"), GOTMPDIR=str(BUILD / "go-tmp"),
               GOPROXY="off", GOSUMDB="off")
    return env


def stamp(name, binary, env):
    raw = invoke(name + "-go-version-m", [GO, "version", "-m", binary], SOURCE, env)
    require("vcs.revision=" + SOURCE_COMMIT in raw and "vcs.modified=false" in raw,
            name + " missing clean source VCS stamp")
    return raw


def core():
    snapshot()
    require((RAW / "result.json").is_file(), "validator build incomplete")
    result = json.loads((RAW / "result.json").read_bytes())
    require(result["status"] == "BUILT_NOT_TESTED" and not result["drift"], "validator build drift")
    env = go_env()
    for name, package in (("core-control", "./apps/control"), ("core-runtime-verifier", "./apps/runtime-verifier")):
        target = BUILD / (name + ".exe")
        require(not target.exists(), name + " already exists")
        invoke(name + "-build", [GO, "build", "-mod=readonly", "-buildvcs=true", "-o", target, package], SOURCE, env)
        stamp(name, target, env)
    validator = BUILD / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe"
    stamp("validator", validator, env)
    invoke("validator-suite", [BUILD / "validator.test.exe", "-test.v"], SOURCE / "apps/desktop/validator", env, timeout=240)
    print(json.dumps({"status": "CORE_AND_VALIDATOR_SUITE_PASSED", "input_digest": result["build_input_digest"]}))


def assemble():
    snapshot()
    require(not DEST.exists(), "new package already exists")
    result = json.loads((RAW / "result.json").read_bytes())
    descriptor = json.loads((BUILD / "apps/desktop/resources/client-wire/descriptor.json").read_bytes())
    inputs = json.loads((RAW / "inputs.before.json").read_bytes())
    require(result["status"] == "BUILT_NOT_TESTED" and not result["drift"], "validator input drift")
    require(result["build_input_digest"] == descriptor["build_input_digest"] and len(inputs) > 6000, "input binding mismatch")
    require(sha(BUILD / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe") == descriptor["binary_sha256"], "validator binary mismatch")
    for name in ("core-control", "core-runtime-verifier", "validator"):
        row = json.loads((RAW / (name + "-go-version-m.invocation.json")).read_bytes())
        require(row["native_exit"] == 0, name + " stamp failed")
        raw = (RAW / (name + "-go-version-m.stdout")).read_text(encoding="utf-8")
        require("vcs.revision=" + SOURCE_COMMIT in raw and "vcs.modified=false" in raw, name + " source stamp mismatch")
    suite = json.loads((RAW / "validator-suite.invocation.json").read_bytes())
    require(suite["native_exit"] == 0 and b"--- PASS:" in (RAW / "validator-suite.stdout").read_bytes(), "validator suite missing")
    old = json.loads(OLD_COMP.read_bytes())
    old_rows = {row["path"]: row for row in old["package_files"]}
    require(len(old_rows) == 58, "old package census changed")
    require(len(descriptor["exact_module_source_inventory"]) == 14 and len(descriptor["compiled_React_asset_inventory"]) == 3, "UI census changed")
    require(len(old["public_host_assets"]) == 32, "public census changed")
    for row in descriptor["exact_module_source_inventory"]:
        relative = "apps/desktop/" + row["path"]
        require(sha(BUILD / relative) == row["sha256"] == sha(SOURCE / relative) == old_rows[relative]["sha256"], "UI changed: " + relative)
    for row in descriptor["compiled_React_asset_inventory"]:
        relative = "apps/web/dist/" + row["path"]
        require(sha(BUILD / relative) == row["sha256"] == old_rows[relative]["sha256"], "React changed: " + relative)
    for row in old["public_host_assets"]:
        relative = row["path"]
        require(sha(SOURCE / relative) == row["sha256"] == old_rows[relative]["sha256"], "public changed: " + relative)
    for name in ("node.exe", "mu-worker.mjs", "mu-worker.mjs.build.json"):
        relative = "apps/desktop/resources/control/runtime/" + name
        require(sha(OLD / relative) == old_rows[relative]["sha256"], "Mu changed: " + name)
    mu = json.loads((OLD / "apps/desktop/resources/control/runtime/mu-worker.mjs.build.json").read_bytes())
    require(mu["mu_commit"] == MU_COMMIT, "Mu source pin changed")
    DEST.mkdir(parents=True)
    rows = []

    def copy(source, relative, component):
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(sha(source) == sha(target), "copy changed: " + relative)
        rows.append({"path": relative, "sha256": sha(target), "bytes": target.stat().st_size,
                     "component": component, "source": str(source)})

    for row in old["package_files"]:
        relative = row["path"]
        if relative == "apps/desktop/resources/control/runtime-verifier-installation.json":
            continue
        if relative == "apps/desktop/resources/control/researchos-control.exe":
            source, component = BUILD / "core-control.exe", "NEW_CORE_CONTROL"
        elif relative == "apps/desktop/resources/control/runtime-verifier.exe":
            source, component = BUILD / "core-runtime-verifier.exe", "NEW_CORE_VERIFIER"
        elif relative.startswith("apps/desktop/resources/control/runtime/"):
            source, component = OLD / relative, "REUSED_MU_FIXED"
        elif relative.startswith("apps/desktop/resources/client-wire/"):
            source, component = BUILD / relative, "NEW_SOURCE_BOUND_VALIDATOR"
        elif relative.startswith("apps/web/dist/"):
            source, component = BUILD / relative, "REBUILT_REACT_EQUAL_OLD"
        elif relative.startswith("apps/desktop/"):
            source, component = BUILD / relative, "REBUILT_UI_EQUAL_OLD"
        else:
            source, component = SOURCE / relative, "PUBLIC_SOURCE_EQUAL_OLD"
        require(source.is_file() and not source.is_symlink(), "missing regular member: " + relative)
        copy(source, relative, component)
    control_dir = Path("apps/desktop/resources/control")
    verifier = DEST / control_dir / "runtime-verifier.exe"
    installation = DEST / control_dir / "runtime-verifier-installation.json"
    put(installation, {"schema": "researchos.runtime-verifier-installation.v1",
                       "service_id": "researchos.runtime-qualification-verifier.v1",
                       "protocol": "researchos.runtime-verifier/1", "executable": str(verifier),
                       "executable_hash": "sha256:" + sha(verifier), "source_commit": SOURCE_COMMIT,
                       "arguments": []})
    rows.append({"path": str(control_dir / installation.name).replace("\\", "/"), "sha256": sha(installation),
                 "bytes": installation.stat().st_size, "component": "NEW_INSTALLATION_MANIFEST", "source": str(HERE / "assemble-attach.py")})
    require(len(rows) == 58 and {r["path"] for r in rows} == set(old_rows), "58-member composition changed")
    composition = {"schema": "researchos.cp451-attach-combined-composition.v1",
                   "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "package_root": str(DEST),
                   "source_commit": SOURCE_COMMIT, "source_tree": SOURCE_TREE, "integrated_main_commit": MAIN_COMMIT,
                   "mu_commit": MU_COMMIT, "scope_sha256": SCOPE_SHA,
                   "bound_full_input_count": len(inputs), "bound_full_input_digest": result["build_input_digest"],
                   "descriptor_sha256": sha(DEST / "apps/desktop/resources/client-wire/descriptor.json"),
                   "validator_sha256": descriptor["binary_sha256"], "package_files": rows,
                   "installation_manifest_path": str(installation), "installation_manifest_sha256": sha(installation),
                   "activation": "NOT_STARTED", "formal_increment": 0, "parent_acceptance": False}
    put(HERE / "composition.json", composition)
    print(json.dumps({"status": "ASSEMBLED_NOT_LAUNCHED", "members": len(rows),
                      "composition_sha256": sha(HERE / "composition.json")}, ensure_ascii=False))


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("core", "assemble"), "phase must be core or assemble")
    globals()[sys.argv[1]]()
