#!/usr/bin/env python3
"""Build a source-bound, repo-shaped Windows Desktop development tree.

The output is a development fixture. It is not an installer or a portable
release. All generated files stay in a new ignored worktree directory.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = {
    "apps/desktop/build-development.py",
    "apps/desktop/launch-development.mjs",
    "apps/desktop/main/main.js",
    "tests/ui/desktop/development-launcher.test.mjs",
    "tests/ui/desktop/development-bundle.test.py",
    "tests/ui/desktop/development-smoke.test.mjs",
    "docs/installation/desktop-development.md",
}
SOURCE_PREFIXES = ("adapters/", "internal/", "apps/control/", "apps/runtime-verifier/",
                   "apps/desktop/main/", "apps/desktop/preload/", "apps/desktop/validator/",
                   "apps/web/src/", "migrations/sqlite/", "spec/v2.0/contracts/")
SOURCE_EXACT = {"go.mod", "go.sum", "go.work", "go.work.sum", "execution/toolchains/locked.json",
                "apps/desktop/package.json", "apps/desktop/package-lock.json", "apps/web/package.json",
                "apps/web/package-lock.json", "apps/web/index.html", "apps/desktop/build-validator.py"}
SCHEMA = "researchos.desktop-development-tree/1"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def sha256(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
    return hasher.hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value))


def regular(path):
    path = Path(path)
    info = path.lstat()
    return path.is_file() and not path.is_symlink() and not (info.st_file_attributes & REPARSE)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def source_snapshot():
    """Freeze tracked source plus the six explicitly admitted new source files."""
    tracked = {item.decode("utf-8") for item in git("ls-files", "-z").split(b"\0") if item}
    changed = {item.decode("utf-8") for item in git("diff", "--name-only", "-z").split(b"\0") if item}
    changed |= {item.decode("utf-8") for item in git("diff", "--cached", "--name-only", "-z").split(b"\0") if item}
    untracked = {item.decode("utf-8") for item in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if item}
    if not (changed | untracked) <= ALLOWLIST:
        raise RuntimeError(f"source outside frozen scope: {sorted((changed | untracked) - ALLOWLIST)}")
    # The 36k-file Git tree includes historic receipts and unrelated products.
    # Go's exact package closure and the current Mu producer closure are sealed
    # separately below; only source and contract candidates belong here.
    paths = {name for name in tracked if name.startswith(SOURCE_PREFIXES) or name in SOURCE_EXACT} | ALLOWLIST
    rows = []
    for relative in sorted(paths):
        path = ROOT / relative
        if not regular(path):
            raise RuntimeError(f"source missing or redirected: {relative}")
        rows.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size,
                     "candidate_delta": relative in ALLOWLIST})
    head = git("rev-parse", "HEAD").decode("ascii").strip()
    tree = git("show", "-s", "--format=%T", "HEAD").decode("ascii").strip()
    return {"head": head, "tree": tree, "tracked_count": len(tracked),
            "candidate_delta": sorted(changed | untracked), "files": rows,
            "digest": hashlib.sha256(canonical(rows)).hexdigest()}


def validate_migrations(root):
    migration_dir = Path(root) / "migrations/sqlite"
    files = sorted(p for p in migration_dir.glob("*.sql") if p.is_file())
    numbered = sorted(int(m.group(1)) for p in files if (m := re.fullmatch(r"(\d{4})_[A-Za-z0-9_]+\.sql", p.name)))
    if not numbered or numbered != list(range(1, max(numbered) + 1)) or not (migration_dir / "next_v24_sessions.sql").is_file():
        raise RuntimeError("continuous numbered SQLite migrations and next_v24_sessions.sql required")
    if len(files) != len(numbered) + 1:
        raise RuntimeError("unexpected SQLite migration name")
    return files


def exact_copy(source, target):
    source, target = Path(source), Path(target)
    if not regular(source):
        raise RuntimeError(f"nonregular or redirected source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise RuntimeError(f"output collision: {target}")
    shutil.copy2(source, target)
    if sha256(source) != sha256(target):
        raise RuntimeError(f"copy drift: {target}")


def copy_tree(source, target):
    source, target = Path(source), Path(target)
    if not source.is_dir() or source.is_symlink():
        raise RuntimeError(f"source directory unavailable: {source}")
    count = 0
    for current, directories, files in os.walk(source, followlinks=False):
        for name in directories:
            directory = Path(current) / name
            if directory.is_symlink() or directory.lstat().st_file_attributes & REPARSE:
                raise RuntimeError(f"redirected directory: {directory}")
        for name in files:
            path = Path(current) / name
            exact_copy(path, target / path.relative_to(source))
            count += 1
    return count


def inventory(root):
    root = Path(root)
    rows = []
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            path = Path(current) / name
            if path.is_symlink() or path.lstat().st_file_attributes & REPARSE:
                raise RuntimeError(f"redirected output directory: {path}")
        for name in files:
            path = Path(current) / name
            if not regular(path):
                raise RuntimeError(f"nonregular output: {path}")
            relative = path.relative_to(root).as_posix()
            if relative == "development-manifest.json":
                continue
            rows.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})
    return sorted(rows, key=lambda row: row["path"])


def json_stream(raw):
    source = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    offset = 0
    while offset < len(source):
        while offset < len(source) and source[offset].isspace():
            offset += 1
        if offset == len(source):
            break
        item, offset = decoder.raw_decode(source, offset)
        yield item


def file_rows(paths):
    rows = []
    for path in sorted({Path(path).resolve() for path in paths}, key=lambda item: str(item).lower()):
        if not regular(path):
            raise RuntimeError(f"build input missing or redirected: {path}")
        rows.append({"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size})
    return rows


def go_compiled_closure(go_lists, toolchain_root):
    paths = set()
    package_count = 0
    fields = ("GoFiles", "CompiledGoFiles", "CgoFiles", "CFiles", "CXXFiles", "MFiles",
              "HFiles", "FFiles", "SFiles", "SwigFiles", "SwigCXXFiles", "SysoFiles", "EmbedFiles")
    for raw in go_lists:
        for package in json_stream(raw):
            package_count += 1
            directory = Path(package["Dir"])
            for field in fields:
                for name in package.get(field, []):
                    source = Path(name)
                    paths.add(source if source.is_absolute() else directory / source)
            module = package.get("Module") or {}
            if module.get("GoMod"):
                paths.add(Path(module["GoMod"]))
    tool_dir = Path(toolchain_root) / "pkg/tool/windows_amd64"
    tools = sorted(tool_dir.glob("*.exe"))
    if package_count < 20 or not tools:
        raise RuntimeError("Go package/toolchain closure incomplete")
    paths.update(tools)
    for name in ["go.env", "VERSION"]:
        path = Path(toolchain_root) / name
        if path.is_file():
            paths.add(path)
    return {"package_count": package_count, "tool_count": len(tools), "files": file_rows(paths)}


def mu_vendor_closure(common):
    manifest = json.loads((common / "third_party/mu.MANIFEST.json").read_bytes())
    entries = manifest.get("entries") or {}
    if manifest.get("files") != 5083 or len(entries) != 5083:
        raise RuntimeError("public Mu 5083-file manifest unavailable")
    paths = []
    for relative, expected in entries.items():
        if not relative.startswith("third_party/mu/") or ".." in Path(relative).parts:
            raise RuntimeError("Mu vendor manifest path invalid")
        path = common / relative
        if not regular(path) or path.stat().st_size != expected["size"] or sha256(path) != expected["sha256"]:
            raise RuntimeError(f"public Mu vendor source changed: {relative}")
        paths.append({"path": str(path.resolve()), "sha256": expected["sha256"], "bytes": expected["size"]})
    return sorted(paths, key=lambda row: row["path"].lower())


MU_META_SCRIPT = r'''
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { join, resolve } from 'node:path';
const [worktree, common, output] = process.argv.slice(2);
const require = createRequire(import.meta.url);
const dependencies = join(common, 'third_party', 'mu', 'node_modules');
const esbuild = require(join(dependencies, 'esbuild'));
const result = await esbuild.build({
  entryPoints: [join(worktree, 'adapters/runtime/mu/worker.mjs')], bundle: true,
  platform: 'node', format: 'esm', target: 'node24', nodePaths: [dependencies],
  banner: { js: "import { createRequire as createRequireForMuWorker } from 'node:module'; const require = createRequireForMuWorker(import.meta.url);" },
  outfile: output, write: false, metafile: true, logLevel: 'warning',
});
const compiled = result.outputFiles.find(item => resolve(item.path) === resolve(output));
if (!compiled) throw Error('Mu compiled output absent');
process.stdout.write(JSON.stringify({ output_sha256: createHash('sha256').update(compiled.contents).digest('hex'),
  inputs: Object.keys(result.metafile.inputs).map(name => resolve(worktree, name)),
  esbuild_version: esbuild.version }) + '\n');
'''


def mu_compiled_closure(common, worktree, metadata, node, stage, receipts, env, run):
    script = stage / "mu-metafile.mjs"
    script.write_text(MU_META_SCRIPT, encoding="utf-8", newline="\n")
    raw = run(receipts, "mu-compiled-inputs", [node, script, worktree, common, stage / "mu-worker.mjs"], worktree, env)
    compiled = json.loads(raw)
    if compiled.get("output_sha256") != metadata["bundle_sha256"] or compiled.get("esbuild_version") != "0.28.2":
        raise RuntimeError("Mu independent compiled-input closure differs from producer output")
    paths = [Path(name) for name in compiled["inputs"]]
    for dependency in [common / "third_party/mu/node_modules/esbuild", common / "third_party/mu/node_modules/@esbuild/win32-x64"]:
        if not dependency.is_dir() or dependency.is_symlink():
            raise RuntimeError("Mu esbuild package/tool unavailable")
        paths.extend(path for path in dependency.rglob("*") if path.is_file())
    return {"compiled_input_count": len(compiled["inputs"]), "files": file_rows(paths)}


def run_command(receipts, name, argv, cwd, env):
    location = receipts / "commands" / name
    location.mkdir(parents=True, exist_ok=False)
    invocation = {"argv": [str(item) for item in argv], "cwd": str(cwd),
                  "environment": {key: env.get(key) for key in ["GOENV", "GOTOOLCHAIN", "GOPATH", "GOMODCACHE", "GOCACHE", "GOTMPDIR", "GOPROXY", "GOSUMDB", "TEMP", "TMP"]}}
    put(location / "recipe.json", invocation)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (location / "stdout.raw").open("xb") as stdout, (location / "stderr.raw").open("xb") as stderr:
        process = subprocess.Popen([str(item) for item in argv], cwd=cwd, env=env,
                                   stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL)
        code = process.wait()
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    put(location / "result.json", {"started_at": started, "ended_at": ended, "pid": process.pid,
                                   "native_exit": code, "stdout_sha256": sha256(location / "stdout.raw"),
                                   "stderr_sha256": sha256(location / "stderr.raw")})
    if code:
        raise RuntimeError(f"{name} exited {code}; retained {location}")
    return (location / "stdout.raw").read_bytes()


def build(args):
    output, receipts = Path(args.output).resolve(), Path(args.receipts).resolve()
    allowed_output = ROOT / ".local"
    if not output.is_relative_to(allowed_output) or output.exists() or receipts.exists():
        raise RuntimeError("output and receipts must be new approved locations")
    if not (ROOT / "apps/desktop/build-validator.py").is_file():
        raise RuntimeError("baseline client-wire builder missing")
    lock = json.loads((ROOT / "execution/toolchains/locked.json").read_bytes())
    tools = {"go": Path(args.go).resolve(), "node": Path(args.node).resolve(),
             "python": Path(sys.executable).resolve(), "electron": Path(args.electron_dist).resolve() / "electron.exe"}
    for name, path in tools.items():
        expected = lock["tools"].get(name, {}).get("sha256") if name != "electron" else "8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac"
        if not regular(path) or sha256(path) != expected:
            raise RuntimeError(f"locked {name} unavailable or changed")
    if not Path(args.module_cache).is_dir() or not Path(args.web_modules).is_dir():
        raise RuntimeError("offline module cache unavailable")
    migrations = validate_migrations(ROOT)
    required_contracts = ["spec/v2.0/contracts/domain.schema.json", "spec/v2.0/contracts/openapi.json",
                          "internal/api/contracts/client.protocol.schema.json", "internal/api/contracts/domain.schema.json"]
    for relative in required_contracts:
        if not regular(ROOT / relative):
            raise RuntimeError(f"Core cwd contract missing: {relative}")
    mu_common = Path(args.mu_common).resolve()
    common_raw = git("rev-parse", "--git-common-dir").decode("utf-8").strip()
    common_dir = Path(common_raw)
    if not common_dir.is_absolute():
        common_dir = (ROOT / common_dir).resolve()
    if mu_common != common_dir.parent.resolve():
        raise RuntimeError("Mu common Main differs from build.mjs git-common-dir selection")
    mu_public = {relative: mu_common / relative for relative in ["execution/v2.4/component_lock.json",
                 "third_party/VENDORED_FROM.md", "third_party/mu.MANIFEST.json",
                 "third_party/mu/node_modules/esbuild/package.json"]}
    if any(not regular(path) for path in mu_public.values()):
        raise RuntimeError("public Main Mu vendor or esbuild inputs unavailable")
    if not (ROOT / ".git").exists():
        raise RuntimeError("source must remain a registered worktree")
    source_before = source_snapshot()
    receipts.mkdir(parents=True, exist_ok=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    put(receipts / "source.before.json", source_before)
    vendor_before = mu_vendor_closure(mu_common)
    put(receipts / "mu-vendor-5083.before.json", vendor_before)
    public_before = {name: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
                     for name, path in mu_public.items()}
    put(receipts / "external-public.before.json", public_before)
    go_cache = output.with_name(output.name + "-go-cache")
    go_tmp = output.with_name(output.name + "-go-tmp")
    temp = output.with_name(output.name + "-temp")
    mu_stage = output.with_name(output.name + "-mu-stage")
    client_stage = output.with_name(output.name + "-client-stage")
    client_receipts = output.with_name(output.name + "-client-receipts")
    for location in [go_cache, go_tmp, temp, mu_stage, client_stage, client_receipts]:
        if location.exists():
            raise RuntimeError(f"fresh build scratch already exists: {location}")
    for location in [go_cache, go_tmp, temp]:
        location.mkdir()
    env = os.environ.copy()
    env.update({"GOENV": "off", "GOTOOLCHAIN": "local", "GOROOT": str(tools["go"].parent.parent),
                "GOPATH": str(Path(args.module_cache).resolve().parent.parent),
                "GOMODCACHE": str(Path(args.module_cache).resolve()), "GOCACHE": str(go_cache),
                "GOTMPDIR": str(go_tmp), "GOPROXY": "off", "GOSUMDB": "off",
                "TEMP": str(temp), "TMP": str(temp), "PYTHONDONTWRITEBYTECODE": "1"})
    core_go_list = run_command(receipts, "core-go-list", [tools["go"], "list", "-deps", "-compiled", "-json", "./apps/control"], ROOT, env)
    verifier_go_list = run_command(receipts, "verifier-go-list", [tools["go"], "list", "-deps", "-compiled", "-json", "./apps/runtime-verifier"], ROOT, env)
    go_before = go_compiled_closure([core_go_list, verifier_go_list], tools["go"].parent.parent)
    put(receipts / "core-verifier-go-inputs.before.json", go_before)
    mu_output = mu_stage / "mu-worker.mjs"
    mu_raw = run_command(receipts, "mu-source-build",
                         [tools["node"], ROOT / "adapters/runtime/mu/build.mjs", mu_output], ROOT, env)
    mu_meta = json.loads((Path(str(mu_output) + ".build.json")).read_bytes())
    if mu_meta.get("mu_commit") != MU_COMMIT or mu_meta.get("vendored_files_verified") != 5083 or \
       mu_meta.get("source_sha256") != sha256(ROOT / "adapters/runtime/mu/worker.mjs") or \
       mu_meta.get("bundle_sha256") != sha256(mu_output) or mu_meta.get("bundle_bytes") != mu_output.stat().st_size:
        raise RuntimeError("current source Mu producer outcome mismatch")
    producer_stdout = json.loads(mu_raw.decode("utf-8").strip())
    if producer_stdout != mu_meta:
        raise RuntimeError("Mu producer stdout and metadata differ")
    mu_compiled_before = mu_compiled_closure(mu_common, ROOT, mu_meta, tools["node"], mu_stage, receipts, env, run_command)
    put(receipts / "mu-compiled-inputs.before.json", mu_compiled_before)
    run_command(receipts, "client-wire-source-build",
                [tools["python"], "-B", "-X", "utf8", ROOT / "apps/desktop/build-validator.py",
                 "--go", tools["go"], "--node", tools["node"], "--electron", tools["electron"],
                 "--module-cache", Path(args.module_cache).resolve(), "--web-modules", Path(args.web_modules).resolve(),
                 "--output", client_stage, "--receipts", client_receipts], ROOT, env)
    copy_tree(client_receipts, receipts / "client-wire-builder")
    client_result = json.loads((client_receipts / "result.json").read_bytes())
    if client_result.get("status") != "BUILT_NOT_TESTED" or client_result.get("drift") != []:
        raise RuntimeError("client-wire source build not clean")
    if source_snapshot() != source_before:
        raise RuntimeError("source changed during client-wire module digest build")
    output.mkdir(parents=True, exist_ok=False)
    exact_copy(ROOT / "apps/desktop/launch-development.mjs", output / "launch-development.mjs")
    exact_copy(ROOT / "apps/desktop/build-development.py", output / "tools/build-development.py")
    for relative in ["apps/desktop/main", "apps/desktop/preload", "apps/web/dist"]:
        copy_tree(client_stage / relative, output / relative)
    exact_copy(client_stage / "apps/desktop/package.json", output / "apps/desktop/package.json")
    copy_tree(client_stage / "apps/desktop/resources/client-wire", output / "apps/desktop/resources/client-wire")
    for relative in required_contracts:
        exact_copy(ROOT / relative, output / relative)
    for source in migrations:
        exact_copy(source, output / "migrations/sqlite" / source.name)
    control = output / "apps/desktop/resources/control"
    control.mkdir(parents=True)
    run_command(receipts, "core-go-build", [tools["go"], "build", "-mod=readonly", "-trimpath", "-o", control / "researchos-control.exe", "./apps/control"], ROOT, env)
    run_command(receipts, "verifier-go-build", [tools["go"], "build", "-mod=readonly", "-trimpath", "-o", control / "runtime-verifier.exe", "./apps/runtime-verifier"], ROOT, env)
    verifier_hash = sha256(control / "runtime-verifier.exe")
    put(control / "runtime-verifier-installation.json", {
        "schema": "researchos.runtime-verifier-installation.v1",
        "service_id": "researchos.runtime-qualification-verifier.v1",
        "protocol": "researchos.runtime-verifier/1",
        "executable": str(control / "runtime-verifier.exe"),
        "executable_hash": "sha256:" + verifier_hash,
        "source_commit": source_before["head"],
        "arguments": [],
    })
    runtime = control / "runtime"
    exact_copy(mu_output, runtime / "mu-worker.mjs")
    exact_copy(Path(str(mu_output) + ".build.json"), runtime / "mu-worker.mjs.build.json")
    exact_copy(tools["node"], runtime / "node.exe")
    electron_count = copy_tree(Path(args.electron_dist).resolve(), output / "runtime/electron")
    if electron_count < 50 or sha256(output / "runtime/electron/electron.exe") != sha256(tools["electron"]):
        raise RuntimeError("full pinned Electron runtime closure incomplete")
    source_after = source_snapshot()
    put(receipts / "source.after.json", source_after)
    if source_after != source_before:
        raise RuntimeError("source changed during complete development build")
    go_after = {**go_before, "files": file_rows(row["path"] for row in go_before["files"])}
    put(receipts / "core-verifier-go-inputs.after.json", go_after)
    if go_after != go_before:
        raise RuntimeError("Core or verifier compiled input/toolchain drift")
    vendor_after = mu_vendor_closure(mu_common)
    put(receipts / "mu-vendor-5083.after.json", vendor_after)
    if vendor_after != vendor_before:
        raise RuntimeError("Mu public vendored source drift")
    mu_compiled_after = {**mu_compiled_before, "files": file_rows(row["path"] for row in mu_compiled_before["files"])}
    put(receipts / "mu-compiled-inputs.after.json", mu_compiled_after)
    if mu_compiled_after != mu_compiled_before:
        raise RuntimeError("Mu compiled dist/module/tool drift")
    public_after = {name: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
                    for name, path in mu_public.items()}
    put(receipts / "external-public.after.json", public_after)
    if public_after != public_before:
        raise RuntimeError("external public Mu producer inputs changed")
    files = inventory(output)
    manifest = {
        "schema": SCHEMA,
        "mode": "DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED",
        "bundle_root": str(output),
        "source": {"head": source_before["head"], "tree": source_before["tree"],
                   "digest": source_before["digest"], "candidate_delta": source_before["candidate_delta"],
                   "seven_scoped_source_sha256": {row["path"]: row["sha256"] for row in source_before["files"] if row["candidate_delta"]}},
        "tools": {name: {"path": str(path), "sha256": sha256(path)} for name, path in tools.items()},
        "client_wire": {"build_input_digest": client_result["build_input_digest"],
                        "binary_sha256": client_result["binary_sha256"],
                        "descriptor_sha256": sha256(output / "apps/desktop/resources/client-wire/descriptor.json")},
        "mu": {"producer": "adapters/runtime/mu/build.mjs", "producer_sha256": sha256(ROOT / "adapters/runtime/mu/build.mjs"),
               "worker_sha256": sha256(ROOT / "adapters/runtime/mu/worker.mjs"),
               "metadata_sha256": sha256(runtime / "mu-worker.mjs.build.json"),
               "bundle_sha256": sha256(runtime / "mu-worker.mjs"),
               "vendored_files_verified": 5083, "public_main_vendor_inputs": public_before,
               "vendor_5083_manifest_sha256": sha256(receipts / "mu-vendor-5083.before.json"),
               "compiled_input_manifest_sha256": sha256(receipts / "mu-compiled-inputs.before.json"),
               "compiled_input_count": mu_compiled_before["compiled_input_count"]},
        "core": {"sha256": sha256(control / "researchos-control.exe"),
                 "verifier_sha256": verifier_hash,
                 "migration_count": len(migrations), "cwd_contracts": required_contracts,
                 "compiled_input_manifest_sha256": sha256(receipts / "core-verifier-go-inputs.before.json"),
                 "go_package_count": go_before["package_count"]},
        "electron": {"file_count": electron_count, "source_dist": str(Path(args.electron_dist).resolve())},
        "files": files,
    }
    put(output / "development-manifest.json", manifest)
    exact_copy(output / "development-manifest.json", receipts / "development-manifest.json")
    put(receipts / "result.json", {"status": "BUILT_NOT_NATIVE_TESTED", "source_acceptance": False,
                                   "source_drift": False, "public_vendor_drift": False,
                                   "output": str(output), "manifest_sha256": sha256(output / "development-manifest.json"),
                                   "files": len(files), "electron_files": electron_count,
                                   "client_wire_build_input_digest": client_result["build_input_digest"],
                                   "mu_bundle_sha256": manifest["mu"]["bundle_sha256"]})
    print(json.dumps({"status": "BUILT_NOT_NATIVE_TESTED", "output": str(output),
                      "manifest_sha256": sha256(output / "development-manifest.json"),
                      "files": len(files)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    for flag in ["go", "node", "electron-dist", "module-cache", "web-modules", "mu-common", "output", "receipts"]:
        parser.add_argument("--" + flag, required=True)
    args = parser.parse_args()
    try:
        build(args)
    except Exception as error:
        receipts = Path(args.receipts)
        if receipts.is_dir() and not (receipts / "failed.json").exists():
            put(receipts / "failed.json", {"error_type": type(error).__name__, "error": str(error),
                                           "status": "FIRST_FAILURE_RETAINED_NO_RETRY"})
        print(f"development build failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
