#!/usr/bin/env python3
"""Build a source-bound, repo-shaped Windows Desktop development tree.

The output is a development fixture. It is not an installer or a portable
release. All generated files stay in a new ignored worktree directory.
"""

import argparse
import datetime
import hashlib
import json
import ntpath
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
    "tests/desktop/test_qualification_build.py",
}
SOURCE_PREFIXES = ("adapters/", "internal/", "apps/control/", "apps/runtime-verifier/",
                   "apps/desktop/main/", "apps/desktop/preload/", "apps/desktop/validator/",
                   "apps/web/src/", "migrations/sqlite/", "spec/v2.0/contracts/",
                   "cmd/researchos-qualification-helper/")
SOURCE_EXACT = {"go.mod", "go.sum", "go.work", "go.work.sum", "execution/toolchains/locked.json",
                "apps/desktop/package.json", "apps/desktop/package-lock.json", "apps/web/package.json",
                "apps/web/package-lock.json", "apps/web/index.html", "apps/desktop/build-validator.py"}
SCHEMA = "researchos.desktop-development-tree/1"
MU_COMMIT = "8dfebe36508ac0c2508735bb866756dab9283e74"
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
QUALIFICATION_HELPER_RELATIVE = "apps/desktop/resources/control/native-qualification/qualification-helper.exe"
QUALIFICATION_HELPER_BUILD_RECEIPT = "execution/product-v1/receipts/single-harness-20261104/native-helper-build01"
QUALIFICATION_HELPER_SCOPE_ID = "product-v1-native-helper-build-01"
QUALIFICATION_FIRST_HELPER_SHA256 = "4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef"
QUALIFICATION_FIRST_HELPER_BYTES = 5335552
QUALIFICATION_ROOT_SYMBOL = "researchos.local/research-os/internal/host.codexQualificationApprovedRoot"
QUALIFICATION_HELPER_SYMBOL = "researchos.local/research-os/internal/host.codexQualificationHelperSHA256"


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


def qualification_windows_path(value, *, linker_value=False):
    """Reject Windows aliases before any resolve or filesystem access."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z]:\\.*", value) or not ntpath.isabs(value):
        raise RuntimeError("qualification path must be an absolute local Windows drive path")
    if value.startswith("\\\\") or "/" in value or ntpath.normpath(value) != value or ":" in value[2:]:
        raise RuntimeError("qualification path spelling is not canonical")
    if any(ord(char) < 32 or ord(char) == 127 or char in ';"\'' for char in value):
        raise RuntimeError("qualification path contains forbidden characters")
    if linker_value and any(char.isspace() for char in value):
        raise RuntimeError("qualification linker root whitespace is unsupported")
    for part in value[3:].split("\\"):
        if part in ("", ".", "..") or part.endswith((".", " ")):
            raise RuntimeError("qualification path contains an alias component")
    path = Path(value)
    if str(path) != value:
        raise RuntimeError("qualification path was normalized before validation")
    return path


def qualification_no_reparse(path):
    """Check each existing original-spelling component before resolve."""
    path = Path(path)
    for current in (path, *path.parents):
        info = current.lstat()
        if current.is_symlink() or getattr(info, "st_file_attributes", 0) & REPARSE:
            raise RuntimeError(f"qualification path uses reparse point: {current}")
    resolved = path.resolve(strict=True)
    if str(resolved).casefold() != str(path).casefold():
        raise RuntimeError("qualification path resolves to an alias")
    return path


def qualification_inputs(args):
    values = [getattr(args, name, None) for name in ("qualification_root", "qualification_helper", "qualification_helper_sha256")]
    if all(value is None for value in values):
        return {"enabled": False, "status": "CLOSED_NO_QUALIFICATION_LINK"}
    if any(not isinstance(value, str) or not value for value in values):
        raise RuntimeError("qualification root, helper and helper-sha256 must be supplied together")
    root_raw, helper_raw, expected = values
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or expected != QUALIFICATION_FIRST_HELPER_SHA256:
        raise RuntimeError("qualification helper digest must match the reviewed first synthetic helper")
    root = qualification_no_reparse(qualification_windows_path(root_raw, linker_value=True))
    helper = qualification_no_reparse(qualification_windows_path(helper_raw))
    if not root.is_dir() or not regular(helper) or helper.suffix.lower() != ".exe":
        raise RuntimeError("qualification root or helper is not an ordinary directory/executable")
    source = root / "S"
    try:
        source.lstat()
    except FileNotFoundError:
        source_status = "DERIVED_NOT_PRESENT_NOT_VALIDATED"
    else:
        qualification_no_reparse(source)
        if not source.is_dir():
            raise RuntimeError("qualification S exists but is not an ordinary directory")
        source_status = "EXISTS_ORDINARY_VALIDATED"
    actual = sha256(helper)
    size = helper.stat().st_size
    if actual != expected or size != QUALIFICATION_FIRST_HELPER_BYTES:
        raise RuntimeError("qualification helper differs from reviewed prebuilt input")
    return {"enabled": True, "status": "BUILD_BOUND_NOT_NATIVE_TESTED", "root_original": root_raw,
            "root_canonical": str(root), "source_derived": str(source), "source_validation": source_status,
            "helper_original": helper_raw, "helper_canonical": str(helper), "helper_expected_sha256": expected,
            "helper_actual_sha256": actual, "helper_bytes": size, "helper_bundle_relative": QUALIFICATION_HELPER_RELATIVE,
            "helper_linked_sha256": "sha256:" + expected}


def qualification_writable_destinations(output, receipts):
    output, receipts = Path(output), Path(receipts)
    return [output, receipts] + [output.with_name(output.name + suffix) for suffix in
                                 ("-go-cache", "-go-tmp", "-temp", "-mu-stage", "-client-stage", "-client-receipts")]


def qualification_destinations_disjoint(binding, output, receipts):
    if not binding["enabled"]:
        return
    protected = [Path(binding["root_canonical"]), Path(binding["helper_canonical"])]
    for destination in qualification_writable_destinations(output, receipts):
        candidate = destination.resolve()
        for source in protected:
            try:
                common = ntpath.commonpath((str(candidate), str(source))).casefold()
            except ValueError:
                continue
            if common in (str(candidate).casefold(), str(source).casefold()):
                raise RuntimeError("qualification root or helper overlaps a writable build destination")


def qualification_linker(binding):
    if not binding["enabled"]:
        return None
    root, digest = binding["root_original"], binding["helper_linked_sha256"]
    return f"-X {QUALIFICATION_ROOT_SYMBOL}={root} -X {QUALIFICATION_HELPER_SYMBOL}={digest}"


def core_build_argv(go, control, binding):
    argv = [go, "build", "-mod=readonly", "-trimpath"]
    if binding["enabled"]:
        argv.extend(["-ldflags", qualification_linker(binding)])
    return argv + ["-o", Path(control) / "researchos-control.exe", "./apps/control"]


def verifier_build_argv(go, control):
    return [go, "build", "-mod=readonly", "-trimpath", "-o", Path(control) / "runtime-verifier.exe", "./apps/runtime-verifier"]


def child_environment(ambient, tools, module_cache, go_cache, go_tmp, temp):
    env = ambient.copy()
    env.update({"GOENV": "off", "GOFLAGS": "", "GOTOOLCHAIN": "local", "GOROOT": str(tools["go"].parent.parent),
                "GOPATH": str(Path(module_cache).resolve().parent.parent),
                "GOMODCACHE": str(Path(module_cache).resolve()), "GOCACHE": str(go_cache),
                "GOTMPDIR": str(go_tmp), "GOPROXY": "off", "GOSUMDB": "off",
                "TEMP": str(temp), "TMP": str(temp), "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def qualification_original_build(main_root, binding, snapshot):
    """Bind the supplied prebuilt bytes to the earlier owned build receipt."""
    if not binding["enabled"]:
        return None
    receipt = Path(main_root) / QUALIFICATION_HELPER_BUILD_RECEIPT
    names = ("RESULT.json", "POSTCHECK.json", "scope.json", "MANIFEST.json")
    for name in names:
        if not regular(receipt / name):
            raise RuntimeError(f"original helper build receipt missing: {name}")
    result = json.loads((receipt / "RESULT.json").read_bytes())
    post = json.loads((receipt / "POSTCHECK.json").read_bytes())
    prepared = json.loads((receipt / "MANIFEST.json").read_bytes())
    scope = json.loads((receipt / "scope.json").read_bytes())
    scope_hash = sha256(receipt / "scope.json")
    if (scope.get("schema") != "researchos.owned-windows-run/1" or
            scope.get("scope_id") != QUALIFICATION_HELPER_SCOPE_ID or scope.get("purpose") != "build" or
            scope.get("authorization") != "ROOT_REVIEWED_EXACT_COMMAND" or
            result.get("scope_id") != QUALIFICATION_HELPER_SCOPE_ID or result.get("scope_sha256") != scope_hash or
            post.get("scope_sha256") != scope_hash or result.get("status") != "COMPLETED_OWNED_JOB_STOPPED" or
            result.get("root_exit_code") != 0 or not result.get("stop_proved") or not result.get("job_active_zero") or
            result.get("input_drift") is not False or result.get("errors") != [] or
            result.get("automatic_retry") is not False or result.get("terminate_job_attempts") != 0 or
            result.get("terminate_original_root_attempts") != 0 or
            post.get("status") != "BUILT_NOT_EXECUTED_NOT_NATIVE_QUALIFIED" or not post.get("stop_proved") or
            post.get("forced") is not False or post.get("model_native_helper_execution") is not False or
            post.get("job_processes") != result.get("job_total_processes") or
            post.get("sha256") != binding["helper_expected_sha256"] or post.get("bytes") != binding["helper_bytes"] or
            str(Path(post.get("path", ""))) != binding["helper_canonical"]):
        raise RuntimeError("original owned helper build does not bind supplied input")
    helper_path = Path(binding["helper_canonical"])
    build_root = helper_path.parent.parent
    expected_cwd = str(build_root / "source")
    expected_argv = ["build", "-trimpath", "-buildvcs=false", "-o", str(helper_path),
                     "./cmd/researchos-qualification-helper"]
    if (build_root.name != "product-v1-native-helper-build01" or helper_path.parent.name != "buildout" or
            scope.get("argv") != expected_argv or prepared.get("argv") != expected_argv or
            scope.get("cwd") != expected_cwd or prepared.get("cwd") != expected_cwd or
            scope.get("controller_sha256") != prepared.get("controller_sha256") or
            scope.get("executable_sha256") != prepared.get("go_sdk_sha256") or
            prepared.get("schema") != "researchos.native-qualification-helper-build-manifest/1" or
            prepared.get("source_binding") != "HELPER_ONLY_SELECTED_GO_FILES_NOT_WHOLE_APPLICATION"):
        raise RuntimeError("original helper scope command or prepared build identity changed")
    inputs = scope.get("inputs")
    prepared_files = prepared.get("files")
    if not isinstance(inputs, list) or not isinstance(prepared_files, list) or any(not isinstance(row, dict) or not isinstance(row.get("path"), str) or not isinstance(row.get("sha256"), str) for row in inputs + prepared_files):
        raise RuntimeError("original helper build input inventory unavailable")
    input_paths = [row["path"].casefold() for row in inputs]
    prepared_paths = [row["path"].casefold() for row in prepared_files]
    if len(input_paths) != len(set(input_paths)) or len(prepared_paths) != len(set(prepared_paths)):
        raise RuntimeError("original helper build input inventory ambiguous")
    scope_inputs = {row["path"].casefold(): row["sha256"] for row in inputs}
    manifest_input = str(build_root / "MANIFEST.json").casefold()
    controller_inputs = [row for row in inputs if Path(row["path"]).name == "owned_run.py"]
    b3_inputs = [row for row in inputs if row["path"].replace("/", "\\").casefold().endswith("product-v1-native-qualification-producer-author-20261105-rev4\\manifest.json")]
    if (scope_inputs.get(manifest_input) != sha256(receipt / "MANIFEST.json") or
            scope_inputs.get(str(Path(scope["executable"])).casefold()) != scope.get("executable_sha256") or
            len(controller_inputs) != 1 or controller_inputs[0]["sha256"] != scope.get("controller_sha256") or
            len(b3_inputs) != 1 or b3_inputs[0]["sha256"] != prepared.get("approved_b3_manifest_sha256")):
        raise RuntimeError("original prepared manifest or compiler detached from registered scope")
    original_sources = {row["path"].removeprefix("source/"): row["sha256"] for row in prepared_files}
    current_sources = {row["path"]: row["sha256"] for row in snapshot["files"]}
    selected = ("cmd/researchos-qualification-helper/main_windows.go", "internal/qualificationprobe/plan.go", "go.mod", "go.sum")
    if any(sum(row["path"] == "source/" + name for row in prepared_files) != 1 or
           original_sources.get(name) != current_sources.get(name) or
           scope_inputs.get(str(Path(expected_cwd) / name).casefold()) != original_sources.get(name)
           for name in selected):
        raise RuntimeError("current helper source differs from original prebuilt helper source")
    return {"provenance": "PREBUILT_ORIGINAL_OWNED_BUILD_RECEIPT_NOT_CURRENT_GO_LIST",
            "receipt_root": str(receipt), "receipt_sha256": {name: sha256(receipt / name) for name in names},
            "source_head": prepared.get("source_head"), "selected_source_sha256": {name: current_sources[name] for name in selected},
            "helper_sha256": binding["helper_expected_sha256"], "helper_bytes": binding["helper_bytes"]}


def qualification_copy_helper(binding, output):
    if not binding["enabled"]:
        return None
    output = Path(output)
    source = qualification_no_reparse(Path(binding["helper_original"]))
    if sha256(source) != binding["helper_expected_sha256"] or source.stat().st_size != binding["helper_bytes"]:
        raise RuntimeError("qualification helper changed before bundle copy")
    target = output / QUALIFICATION_HELPER_RELATIVE
    if not target.is_relative_to(output) or target.exists() or target.parent.exists():
        raise RuntimeError("qualification helper bundle target collided")
    qualification_no_reparse(target.parent.parent)
    target.parent.mkdir(parents=False, exist_ok=False)
    qualification_no_reparse(target.parent)
    exact_copy(source, target)
    if sha256(source) != binding["helper_expected_sha256"] or sha256(target) != binding["helper_expected_sha256"] or target.stat().st_size != binding["helper_bytes"]:
        raise RuntimeError("qualification helper copy drift")
    return target


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def source_snapshot():
    """Freeze tracked source plus the explicitly admitted build source files."""
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
                 "environment": {key: env.get(key) for key in ["GOENV", "GOFLAGS", "GOTOOLCHAIN", "GOPATH", "GOMODCACHE", "GOCACHE", "GOTMPDIR", "GOPROXY", "GOSUMDB", "TEMP", "TMP"]}}
    put(location / "recipe.json", invocation)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (location / "stdout.raw").open("xb") as stdout, (location / "stderr.raw").open("xb") as stderr:
        process = subprocess.Popen([str(item) for item in argv], cwd=cwd, env=env,
                                   stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, shell=False)
        code = process.wait()
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    put(location / "result.json", {"started_at": started, "ended_at": ended, "pid": process.pid,
                                   "native_exit": code, "stdout_sha256": sha256(location / "stdout.raw"),
                                   "stderr_sha256": sha256(location / "stderr.raw")})
    if code:
        raise RuntimeError(f"{name} exited {code}; retained {location}")
    return (location / "stdout.raw").read_bytes()


def build(args, receipt_created=None):
    qualification = qualification_inputs(args)
    qualification_initial = qualification.copy()
    output, receipts = Path(args.output).resolve(), Path(args.receipts).resolve()
    qualification_destinations_disjoint(qualification, output, receipts)
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
    qualification_origin = qualification_original_build(mu_common, qualification, source_before)
    receipts.mkdir(parents=True, exist_ok=False)
    if receipt_created is not None:
        receipt_created(receipts, qualification)
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
    env = child_environment(os.environ, tools, args.module_cache, go_cache, go_tmp, temp)
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
    core_argv = core_build_argv(tools["go"], control, qualification)
    run_command(receipts, "core-go-build", core_argv, ROOT, env)
    copied_helper = qualification_copy_helper(qualification, output)
    run_command(receipts, "verifier-go-build", verifier_build_argv(tools["go"], control), ROOT, env)
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
    if qualification["enabled"]:
        if qualification_inputs(args) != qualification_initial or qualification_original_build(mu_common, qualification, source_after) != qualification_origin:
            raise RuntimeError("qualification root, helper, or original build provenance drift")
        qualification_no_reparse(Path(qualification["helper_original"]))
        qualification_no_reparse(copied_helper)
        if (sha256(qualification["helper_original"]) != qualification["helper_expected_sha256"] or
                sha256(copied_helper) != qualification["helper_expected_sha256"] or
                Path(qualification["helper_original"]).stat().st_size != qualification["helper_bytes"] or
                copied_helper.stat().st_size != qualification["helper_bytes"]):
            raise RuntimeError("qualification helper source or bundle copy changed during build")
        qualification["helper_copied_sha256"] = sha256(copied_helper)
        qualification["helper_copied_bytes"] = copied_helper.stat().st_size
        qualification["helper_copied_path"] = str(copied_helper)
        qualification["original_build"] = qualification_origin
        qualification["core_linker_values"] = {
            QUALIFICATION_ROOT_SYMBOL: qualification["root_original"],
            QUALIFICATION_HELPER_SYMBOL: qualification["helper_linked_sha256"]}
        qualification["core_linker_flags"] = qualification_linker(qualification)
    files = inventory(output)
    manifest = {
        "schema": SCHEMA,
        "mode": "DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED",
        "formal_acceptance": False,
        "product_acceptance": False,
        "bundle_root": str(output),
        "source": {"head": source_before["head"], "tree": source_before["tree"],
                   "digest": source_before["digest"], "candidate_delta": source_before["candidate_delta"],
                   "scoped_source_sha256": {row["path"]: row["sha256"] for row in source_before["files"] if row["candidate_delta"]}},
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
                 "build_argv": [str(item) for item in core_argv],
                 "migration_count": len(migrations), "cwd_contracts": required_contracts,
                 "compiled_input_manifest_sha256": sha256(receipts / "core-verifier-go-inputs.before.json"),
                 "go_package_count": go_before["package_count"]},
        "qualification": qualification,
        "electron": {"file_count": electron_count, "source_dist": str(Path(args.electron_dist).resolve())},
        "files": files,
    }
    put(output / "development-manifest.json", manifest)
    exact_copy(output / "development-manifest.json", receipts / "development-manifest.json")
    put(receipts / "result.json", {"status": "BUILT_NOT_NATIVE_TESTED", "source_acceptance": False,
                                   "qualification_enabled": qualification["enabled"],
                                   "source_drift": False, "public_vendor_drift": False,
                                   "output": str(output), "manifest_sha256": sha256(output / "development-manifest.json"),
                                   "files": len(files), "electron_files": electron_count,
                                   "client_wire_build_input_digest": client_result["build_input_digest"],
                                   "mu_bundle_sha256": manifest["mu"]["bundle_sha256"]})
    print(json.dumps({"status": "BUILT_NOT_NATIVE_TESTED", "output": str(output),
                      "manifest_sha256": sha256(output / "development-manifest.json"),
                      "files": len(files)}, ensure_ascii=False))


def write_owned_failure(owned, output, error):
    if owned is None:
        return
    receipts, binding = owned
    try:
        qualification_destinations_disjoint(binding, output, receipts)
        qualification_no_reparse(receipts)
        if receipts.is_dir() and not (receipts / "failed.json").exists():
            put(receipts / "failed.json", {"error_type": type(error).__name__, "error": str(error),
                                           "status": "FIRST_FAILURE_RETAINED_NO_RETRY"})
    except Exception:
        # The original failure and outer owned-run raw logs remain authoritative.
        return


def main():
    parser = argparse.ArgumentParser()
    for flag in ["go", "node", "electron-dist", "module-cache", "web-modules", "mu-common", "output", "receipts"]:
        parser.add_argument("--" + flag, required=True)
    for flag in ["qualification-root", "qualification-helper", "qualification-helper-sha256"]:
        parser.add_argument("--" + flag)
    args = parser.parse_args()
    owned_receipts = []
    try:
        build(args, lambda path, binding: owned_receipts.append((path, binding)))
    except Exception as error:
        write_owned_failure(owned_receipts[0] if owned_receipts else None, Path(args.output).resolve(), error)
        print(f"development build failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
