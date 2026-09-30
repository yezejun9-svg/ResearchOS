#!/usr/bin/env python3
"""Build a deterministic, allowlisted Windows development release bundle."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = (
    "spec/v2.0", "migrations/sqlite", "adapters", "internal", "apps/control",
    "apps/web/src", "ops", "tests", "bootstrap", "evaluation/development",
    "evaluation/evolution", "evaluation/skills", "execution/command_dispatcher",
    "release", "docs/installation",
)
SOURCE_FILES = ("go.mod", "go.sum", "apps/web/package.json", "apps/web/package-lock.json",
                "apps/web/index.html", "execution/commands.json")
SOURCE_SUFFIXES = {".go", ".py", ".js", ".jsx", ".css", ".json", ".html", ".md", ".ps1", ".sql"}
EXCLUDED_PARTS = {".local", "node_modules", "dist", "__pycache__", ".git", "receipts", "verifier"}
UNSAFE_BYTES = (b"C:" + bytes((92,)) + b"Users" + bytes((92,)),
                b"C:" + bytes((47,)) + b"Users" + bytes((47,)),
                ("D:" + chr(92) + "作品集" + chr(92)).encode(),
                ("D:" + chr(47) + "作品集" + chr(47)).encode())
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
FROZEN_DIRS = (
    "adapters", "apps", "bootstrap", "contracts", "evaluation", "internal",
    "migrations", "ops", "qualification", "release", "spec", "tests",
    "docs/installation", "execution/command_dispatcher",
)
FROZEN_ROOT_FILES = {"go.mod", "go.sum", "go.work", "go.work.sum"}
GENERATED_DIRS = {".git", ".local", "node_modules", "dist", "__pycache__"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def frozen_path(relative: str) -> bool:
    parts = Path(relative).parts
    if any(part in GENERATED_DIRS for part in parts):
        return False
    return relative in FROZEN_ROOT_FILES or any(
        relative == directory or relative.startswith(directory + "/") for directory in FROZEN_DIRS
    )


def check_frozen_inputs(root: Path, previous=None):
    """Refuse dirty, missing, or untracked build/package inputs, including ignored files."""
    oid_format = run(["git", "rev-parse", "--show-object-format"], root).strip()
    if oid_format not in ("sha1", "sha256"):
        raise RuntimeError("unsupported Git object format")
    tree = subprocess.run(["git", "ls-tree", "-r", "-z", "HEAD"], cwd=root, capture_output=True, check=True).stdout
    expected = {}
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        meta, name = entry.split(b"\t", 1)
        relative = name.decode("utf-8")
        if frozen_path(relative):
            mode, kind, oid = meta.decode("ascii").split()
            if kind != "blob" or mode not in ("100644", "100755"):
                raise RuntimeError(f"non-regular frozen Git input: {relative}")
            expected[relative] = oid
    actual = set()
    roots = [root / directory for directory in FROZEN_DIRS]
    for base in roots:
        if not base.is_dir() or base.is_symlink():
            raise RuntimeError(f"frozen input directory unavailable: {base.relative_to(root)}")
        for current, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d not in GENERATED_DIRS]
            for directory in dirs:
                if (Path(current) / directory).is_symlink():
                    raise RuntimeError(f"symlink in frozen input: {(Path(current) / directory).relative_to(root)}")
            for name in files:
                path = Path(current) / name
                relative = path.relative_to(root).as_posix()
                if not frozen_path(relative):
                    continue
                if path.is_symlink() or not path.is_file() or relative not in expected:
                    raise RuntimeError(f"untracked or non-regular frozen input: {relative}")
                raw = path.read_bytes()
                oid = hashlib.new(oid_format, f"blob {len(raw)}\0".encode() + raw).hexdigest()
                if oid != expected[relative]:
                    raise RuntimeError(f"dirty frozen Git input: {relative}")
                actual.add(relative)
    for relative in FROZEN_ROOT_FILES:
        path = root / relative
        if path.exists() or relative in expected:
            if path.is_symlink() or not path.is_file() or relative not in expected:
                raise RuntimeError(f"untracked or missing frozen root input: {relative}")
            raw = path.read_bytes()
            oid = hashlib.new(oid_format, f"blob {len(raw)}\0".encode() + raw).hexdigest()
            if oid != expected[relative]:
                raise RuntimeError(f"dirty frozen Git input: {relative}")
            actual.add(relative)
    missing = set(expected) - actual
    if missing:
        raise RuntimeError(f"missing frozen Git input: {sorted(missing)[0]}")
    snapshot = digest(canonical(expected))
    if previous is not None and snapshot != previous:
        raise RuntimeError("frozen Git inputs changed during build")
    return snapshot


def run(argv, cwd: Path, env=None) -> str:
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{Path(argv[0]).name} exited {result.returncode}: {result.stderr[-900:]}")
    return result.stdout


def checked_tool(lock, name: str) -> Path:
    item = lock["tools"][name]
    path = Path(item["path"])
    if not path.is_file() or digest(path.read_bytes()) != item["sha256"]:
        raise RuntimeError(f"locked {name} missing or hash changed")
    return path


def safe_source(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if any(part in EXCLUDED_PARTS or part.startswith(".") for part in Path(relative).parts):
        raise ValueError(f"excluded package path: {relative}")
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"non-regular or escaping package path: {relative}")
    return relative


def add_source(files: dict[str, bytes], root: Path, relative: str):
    path = root / relative
    safe_source(path, root)
    raw = path.read_bytes()
    if any(marker in raw for marker in UNSAFE_BYTES):
        raise ValueError(f"developer absolute path in package input: {relative}")
    if relative in files:
        raise ValueError(f"duplicate package path: {relative}")
    files[relative] = raw


def collect_sources(root: Path) -> dict[str, bytes]:
    files = {}
    for relative in SOURCE_FILES:
        add_source(files, root, relative)
    for directory in SOURCE_DIRS:
        base = root / directory
        if not base.is_dir():
            raise RuntimeError(f"required package source missing: {directory}")
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if any(part in EXCLUDED_PARTS or part.startswith(".") for part in path.relative_to(root).parts):
                continue
            # This legacy browser fixture hardcodes a developer tool path. It
            # remains a source-checkout prerequisite, never release content.
            if relative == "tests/ui/browser_smoke.py":
                continue
            add_source(files, root, relative)
    for relative in ("ops/release/start.ps1", "ops/release/stop.ps1", "ops/release/verify.ps1"):
        if relative not in files:
            raise RuntimeError(f"release script missing: {relative}")
    files["scripts/start.ps1"] = files["ops/release/start.ps1"]
    files["scripts/stop.ps1"] = files["ops/release/stop.ps1"]
    files["scripts/verify.ps1"] = files["ops/release/verify.ps1"]
    return files


def module_licenses(go: Path, root: Path, env, files: dict[str, bytes]):
    modules = []
    gaps = []
    cache = Path(run([go, "env", "GOMODCACHE"], root, env).strip())
    compiled = {}
    for binary in ("control", "runtime", "backup"):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temporary:
            temporary.write(files[f"bin/{binary}.exe"])
            path = Path(temporary.name)
        try:
            for line in run([go, "version", "-m", path], root, env).splitlines():
                fields = line.strip().split("\t")
                if len(fields) >= 4 and fields[0] == "dep":
                    compiled[(fields[1], fields[2])] = fields[3]
        finally:
            path.unlink()
    for name, version in sorted(compiled):
        item = {"name": name, "version": version or "main"}
        item["sum"] = compiled[(name, version)]
        escaped = "".join("!" + ch.lower() if ch.isupper() else ch for ch in name)
        directory = cache / (escaped + "@" + version)
        choices = sorted(p for p in directory.glob("LICENSE*") if p.is_file())
        if not choices:
            item["license"] = "UNKNOWN"
            gaps.append(f"Go {name}: license file unavailable")
        else:
            raw = choices[0].read_bytes()
            target = f"licenses/go/{len(modules):03d}.txt"
            files[target] = raw
            item["license_file"] = target
            item["license_sha256"] = digest(raw)
        modules.append(item)
    if not (root / "LICENSE").is_file():
        gaps.append("ResearchOS main module: license file unavailable")
    return modules, gaps


def npm_licenses(root: Path, files: dict[str, bytes]):
    lock = json.loads((root / "apps/web/package-lock.json").read_text(encoding="utf-8"))
    modules, gaps = [], []
    for path, data in sorted(lock["packages"].items()):
        if not path:
            continue
        item = {"name": path.removeprefix("node_modules/"), "version": data.get("version", "UNKNOWN"),
                "integrity": data.get("integrity", "UNKNOWN")}
        directory = root / "apps/web" / path
        choices = sorted(p for p in directory.glob("LICENSE*") if p.is_file())
        if not choices:
            item["license"] = "UNKNOWN"
            gaps.append(f"npm {item['name']}: license file unavailable")
        else:
            raw = choices[0].read_bytes()
            target = f"licenses/npm/{len(modules):03d}.txt"
            files[target] = raw
            item["license_file"] = target
            item["license_sha256"] = digest(raw)
        modules.append(item)
    return modules, gaps


def command_requirements(files: dict[str, bytes]):
    registry = json.loads(files["execution/commands.json"])
    missing = []
    bound = []
    unbound = []
    for name, item in sorted(registry["commands"].items()):
        if item["state"] != "BOUND":
            unbound.append(name)
            continue
        bound.append(name)
        for arg in item.get("argv", []):
            if isinstance(arg, str) and re.fullmatch(r"[A-Za-z0-9_./-]+\.(py|js|go)", arg) and arg not in files:
                missing.append(f"{name}: {arg}")
    if missing:
        raise RuntimeError("declared command script absent: " + ", ".join(missing))
    return {"bound": bound, "unbound_not_implemented": unbound,
            "execution_scope": "construction source checkout and pinned tools required; bundled scripts do not grant acceptance",
            "source_checkout_gap": "tests/ui/browser_smoke.py excluded for developer absolute path; W13 browser command requires clean source checkout"}


def build(root: Path, output: Path, lock_path: Path):
    frozen = check_frozen_inputs(root)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    go = checked_tool(lock, "go")
    node = checked_tool(lock, "node")
    npm = checked_tool(lock, "npm_cli")
    env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", GOPROXY="off", GOSUMDB="off", CGO_ENABLED="0", GOWORK="off", GOFLAGS="-mod=readonly", NODE_OPTIONS="")
    for name, tool, argv in (("go", go, [go, "version"]), ("node", node, [node, "--version"]),
                             ("npm_cli", npm, [node, npm, "--version"])):
        if run(argv, root, env).strip() != lock["tools"][name]["version_output"]:
            raise RuntimeError(f"locked {name} version changed")
    run([go, "mod", "verify"], root, env)
    web = root / "apps/web"
    run([node, npm, "ci", "--offline", "--no-audit", "--no-fund"], web, env)
    run([node, web / "node_modules/vite/bin/vite.js", "build"], web, env)
    if not (web / "dist/index.html").is_file():
        raise RuntimeError("web build has no index.html")
    files = collect_sources(root)
    with tempfile.TemporaryDirectory(prefix="researchos-release-build-") as temporary:
        for name, package in (("control", "./apps/control"), ("runtime", "./ops/runtime"), ("backup", "./ops/backup")):
            binary = Path(temporary) / f"{name}.exe"
            run([go, "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", binary, package], root, env)
            files[f"bin/{name}.exe"] = binary.read_bytes()
    for path in sorted((web / "dist").rglob("*")):
        if path.is_file():
            files["web/dist/" + path.relative_to(web / "dist").as_posix()] = path.read_bytes()
    go_modules, go_gaps = module_licenses(go, root, env, files)
    npm_modules, npm_gaps = npm_licenses(root, files)
    command_scope = command_requirements(files)
    check_frozen_inputs(root, frozen)
    commit = run(["git", "rev-parse", "HEAD"], root).strip()
    source_hash = digest(canonical({name: digest(raw) for name, raw in sorted(files.items()) if not name.startswith(("bin/", "web/dist/", "licenses/"))}))
    migration_names = sorted(p.name for p in (root / "migrations/sqlite").glob("[0-9][0-9][0-9][0-9]_*.sql"))
    manifest = {
        "format": "RESEARCHOS_WINDOWS_X64_R1_FIXTURE_BUNDLE_V1", "source_commit": commit,
        "source_tree_sha256": source_hash, "build_id": source_hash[:20],
        "platform": "windows/amd64", "build_flags": ["-trimpath", "-buildvcs=false", "-ldflags=-buildid="],
        "tools": {name: {"version": lock["tools"][name]["version_output"], "sha256": lock["tools"][name]["sha256"]} for name in ("go", "node", "npm_cli")},
        "locks": {name: digest(files[name]) for name in ("go.mod", "go.sum", "apps/web/package-lock.json")},
        "api_schema_sha256": digest(files["spec/v2.0/contracts/openapi.json"]),
        "contract_schema_sha256": digest(files["spec/v2.0/contracts/domain.schema.json"]),
        "migrations": [{"name": name, "sha256": digest(files[f"migrations/sqlite/{name}"])} for name in migration_names],
        "database": {"fresh_fixture": True, "fresh_fixture_schema": int(migration_names[-1][:4]),
                     "populated_read_write_range": "NOT_QUALIFIED_R1; PREBACKUP_GUARD_APPLIES",
                     "final_release_schema": "ROOT_TO_PIN_AFTER_RUNTIME_S2", "existing_pinned_upgrade": "schema13-to14-remote-access-v1",
                     "schema13_to_final_plan": "NOT_IMPLEMENTED"},
        "commands": command_scope,
        "sbom": {"go": go_modules, "npm": npm_modules, "license_gaps": go_gaps + npm_gaps},
        "runtime_profile": {"adapter_versions": "NOT_QUALIFIED_R1", "model_identity": "NOT_OBSERVED",
                            "provider_credentials": "NOT_BUNDLED"},
        "rollback": {"fixture": "stop disposable process and retain external data", "populated_authority": "NOT_IMPLEMENTED"},
        "evidence_index": {"W18_A12": "external limited review; not bundled or stage accepted",
                           "W20_A15": "NOT_RUN", "archive_hash": "external build receipt, not self-referential"},
        "acceptance": {"A15_clean_windows": "NOT_RUN", "W20": "NOT_ACCEPTED", "normal_live_runtime": "CLOSED"},
        "files": [{"path": name, "sha256": digest(raw), "size": len(raw)} for name, raw in sorted(files.items())],
    }
    files["release-manifest.json"] = canonical(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"archive": str(output), "archive_sha256": digest(output.read_bytes()), "archive_size": output.stat().st_size,
            "manifest_sha256": digest(files["release-manifest.json"]), "build_id": manifest["build_id"],
            "source_commit": commit, "file_count": len(files), "license_gaps": len(go_gaps + npm_gaps)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tool-lock", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    locked = args.tool_lock or source / "execution/toolchains/locked.json"
    try:
        print(json.dumps(build(source, args.output.resolve(), locked.resolve()), sort_keys=True))
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        print(f"release build failed: {exc}", file=sys.stderr)
        sys.exit(1)
