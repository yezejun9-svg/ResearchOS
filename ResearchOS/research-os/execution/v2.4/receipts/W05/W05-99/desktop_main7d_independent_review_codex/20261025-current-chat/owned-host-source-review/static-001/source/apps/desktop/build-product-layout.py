#!/usr/bin/env python3
"""Build a location-bound, owned Windows product layout; no installation or launch.

The output is a complete product-host candidate in this worktree's .local,
including a real CLI. It is intentionally not a Windows installer.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("desktop_development_builder", HERE / "build-development.py")
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)

SCHEMA = "researchos.product-layout/1"
ALLOWLIST = {
    "apps/desktop/main/main.js", "apps/desktop/main/lib/product-layout.js",
    "apps/cli/main.go", "apps/cli/cli_contract.go", "apps/cli/cli_doctor.go",
    "apps/cli/cli_native.go", "apps/cli/cli_verbs.go", "apps/cli/product_host_windows.go",
    "apps/cli/product_host_other.go", "apps/cli/product_host_windows_test.go",
    "tests/ui/desktop/product-host.test.mjs", "tests/ui/desktop/product-layout.test.py",
    "docs/installation/desktop-product-host.md", "apps/desktop/build-product-layout.py",
}


def snapshot():
    tracked = {p.decode() for p in dev.git("ls-files", "-z").split(b"\0") if p}
    changed = {p.decode() for p in dev.git("diff", "--name-only", "-z").split(b"\0") if p}
    changed |= {p.decode() for p in dev.git("diff", "--cached", "--name-only", "-z").split(b"\0") if p}
    changed |= {p.decode() for p in dev.git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p}
    if not changed <= ALLOWLIST:
        raise RuntimeError(f"source outside product-host exact14 scope: {sorted(changed - ALLOWLIST)}")
    prefixes = dev.SOURCE_PREFIXES + ("apps/cli/",)
    files = {p for p in tracked if p.startswith(prefixes) or p in dev.SOURCE_EXACT} | ALLOWLIST
    rows = []
    for name in sorted(files):
        p = ROOT / name
        if not dev.regular(p):
            raise RuntimeError(f"product source unavailable or redirected: {name}")
        rows.append({"path": name, "sha256": dev.sha256(p), "bytes": p.stat().st_size})
    return {"head": dev.git("rev-parse", "HEAD").decode().strip(),
            "tree": dev.git("show", "-s", "--format=%T", "HEAD").decode().strip(),
            "candidate_delta": sorted(changed), "files": rows,
            "digest": hashlib.sha256(dev.canonical(rows)).hexdigest()}


def install_id(source_commit, version, protocol, schema_version, binaries):
    values = [SCHEMA, source_commit, version, protocol, str(schema_version)]
    values += [binaries[k]["sha256"] for k in ("cli", "control", "electron", "verifier", "validator")]
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def build(args):
    output, receipts = Path(args.output).resolve(), Path(args.receipts).resolve()
    if not output.is_relative_to(ROOT / ".local") or output.exists() or receipts.exists():
        raise RuntimeError("product output must be new in this worktree .local and receipts create-new")
    lock = json.loads((ROOT / "execution/toolchains/locked.json").read_bytes())
    tools = {"go": Path(args.go).resolve(), "node": Path(args.node).resolve(),
             "python": Path(sys.executable).resolve(), "electron": Path(args.electron_dist).resolve() / "electron.exe"}
    for name, tool in tools.items():
        expected = lock["tools"].get(name, {}).get("sha256") if name != "electron" else \
            "8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac"
        if not dev.regular(tool) or dev.sha256(tool) != expected:
            raise RuntimeError(f"locked tool unavailable or changed: {name}")
    common_raw = dev.git("rev-parse", "--git-common-dir").decode().strip()
    common = Path(common_raw)
    if not common.is_absolute():
        common = (ROOT / common).resolve()
    common = common.parent.resolve()
    if Path(args.mu_common).resolve() != common:
        raise RuntimeError("Mu public source must be common Main")
    migrations = dev.validate_migrations(ROOT)
    contracts = ["spec/v2.0/contracts/domain.schema.json", "spec/v2.0/contracts/openapi.json",
                 "internal/api/contracts/client.protocol.schema.json", "internal/api/contracts/domain.schema.json"]
    if any(not dev.regular(ROOT / p) for p in contracts):
        raise RuntimeError("Core cwd contracts unavailable")
    before = snapshot()
    receipts.mkdir(parents=True, exist_ok=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    dev.put(receipts / "source.before.json", before)
    vendor_before = dev.mu_vendor_closure(common)
    dev.put(receipts / "mu-vendor-5083.before.json", vendor_before)
    public = {name: common / name for name in ["execution/v2.4/component_lock.json",
              "third_party/VENDORED_FROM.md", "third_party/mu.MANIFEST.json",
              "third_party/mu/node_modules/esbuild/package.json"]}
    public_before = {name: {"sha256": dev.sha256(p), "bytes": p.stat().st_size} for name, p in public.items()}
    dev.put(receipts / "public-mu.before.json", public_before)
    scratch = {name: output.with_name(output.name + "-" + name) for name in
               ["go-cache", "go-tmp", "temp", "mu-stage", "client-stage", "client-receipts"]}
    if any(p.exists() for p in scratch.values()):
        raise RuntimeError("product scratch path already exists")
    for name in ["go-cache", "go-tmp", "temp"]:
        scratch[name].mkdir()
    env = os.environ.copy()
    env.update({"GOENV": "off", "GOTOOLCHAIN": "local", "GOROOT": str(tools["go"].parent.parent),
                "GOPATH": str(Path(args.module_cache).resolve().parent.parent),
                "GOMODCACHE": str(Path(args.module_cache).resolve()), "GOCACHE": str(scratch["go-cache"]),
                "GOTMPDIR": str(scratch["go-tmp"]), "GOPROXY": "off", "GOSUMDB": "off",
                "TEMP": str(scratch["temp"]), "TMP": str(scratch["temp"]), "PYTHONDONTWRITEBYTECODE": "1"})
    go_lists = [dev.run_command(receipts, name + "-go-list",
                [tools["go"], "list", "-deps", "-compiled", "-json", "./apps/" + name], ROOT, env)
                for name in ["control", "runtime-verifier", "cli"]]
    go_before = dev.go_compiled_closure(go_lists, tools["go"].parent.parent)
    dev.put(receipts / "go-compiled-inputs.before.json", go_before)
    mu_file = scratch["mu-stage"] / "mu-worker.mjs"
    mu_raw = dev.run_command(receipts, "mu-source-build",
                             [tools["node"], ROOT / "adapters/runtime/mu/build.mjs", mu_file], ROOT, env)
    mu_meta = json.loads(Path(str(mu_file) + ".build.json").read_bytes())
    if mu_meta.get("mu_commit") != dev.MU_COMMIT or mu_meta.get("vendored_files_verified") != 5083 or \
       mu_meta.get("bundle_sha256") != dev.sha256(mu_file) or json.loads(mu_raw) != mu_meta:
        raise RuntimeError("current Mu producer mismatch")
    mu_compiled = dev.mu_compiled_closure(common, ROOT, mu_meta, tools["node"],
                                          scratch["mu-stage"], receipts, env, dev.run_command)
    dev.put(receipts / "mu-compiled-inputs.before.json", mu_compiled)
    dev.run_command(receipts, "client-wire-source-build",
                    [tools["python"], "-B", "-X", "utf8", ROOT / "apps/desktop/build-validator.py",
                     "--go", tools["go"], "--node", tools["node"], "--electron", tools["electron"],
                     "--module-cache", Path(args.module_cache).resolve(),
                     "--web-modules", Path(args.web_modules).resolve(),
                     "--output", scratch["client-stage"], "--receipts", scratch["client-receipts"]], ROOT, env)
    dev.copy_tree(scratch["client-receipts"], receipts / "client-wire-builder")
    client_result = json.loads((scratch["client-receipts"] / "result.json").read_bytes())
    if client_result.get("status") != "BUILT_NOT_TESTED" or client_result.get("drift") != [] or snapshot() != before:
        raise RuntimeError("current client-wire closure or source changed")
    output.mkdir(parents=True, exist_ok=False)
    for name in ["apps/desktop/main", "apps/desktop/preload", "apps/web/dist"]:
        dev.copy_tree(scratch["client-stage"] / name, output / name)
    dev.exact_copy(scratch["client-stage"] / "apps/desktop/package.json", output / "apps/desktop/package.json")
    dev.copy_tree(scratch["client-stage"] / "apps/desktop/resources/client-wire",
                  output / "apps/desktop/resources/client-wire")
    for name in contracts:
        dev.exact_copy(ROOT / name, output / name)
    for migration in migrations:
        dev.exact_copy(migration, output / "migrations/sqlite" / migration.name)
    dev.exact_copy(ROOT / "docs/installation/desktop-product-host.md", output / "docs/desktop-product-host.md")
    control = output / "apps/desktop/resources/control"
    control.mkdir(parents=True)
    binaries = {"control": control / "researchos-control.exe",
                "verifier": control / "runtime-verifier.exe",
                "cli": output / "bin/researchos.exe",
                "electron": output / "runtime/electron/electron.exe",
                "validator": output / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe"}
    for key, package in [("control", "control"), ("verifier", "runtime-verifier"), ("cli", "cli")]:
        binaries[key].parent.mkdir(parents=True, exist_ok=True)
        dev.run_command(receipts, key + "-go-build",
                        [tools["go"], "build", "-mod=readonly", "-trimpath", "-o", binaries[key], "./apps/" + package], ROOT, env)
    dev.put(control / "runtime-verifier-installation.json", {
        "schema": "researchos.runtime-verifier-installation.v1",
        "service_id": "researchos.runtime-qualification-verifier.v1",
        "protocol": "researchos.runtime-verifier/1",
        "executable": str(binaries["verifier"]),
        "executable_hash": "sha256:" + dev.sha256(binaries["verifier"]),
        "source_commit": before["head"], "arguments": [],
    })
    runtime = control / "runtime"
    dev.exact_copy(mu_file, runtime / "mu-worker.mjs")
    dev.exact_copy(Path(str(mu_file) + ".build.json"), runtime / "mu-worker.mjs.build.json")
    dev.exact_copy(tools["node"], runtime / "node.exe")
    electron_count = dev.copy_tree(Path(args.electron_dist).resolve(), output / "runtime/electron")
    if electron_count < 50 or dev.sha256(binaries["electron"]) != dev.sha256(tools["electron"]):
        raise RuntimeError("pinned Electron distribution incomplete")
    after = snapshot()
    dev.put(receipts / "source.after.json", after)
    if after != before:
        raise RuntimeError("source changed during product build")
    go_after = {**go_before, "files": dev.file_rows(row["path"] for row in go_before["files"])}
    dev.put(receipts / "go-compiled-inputs.after.json", go_after)
    if go_after != go_before:
        raise RuntimeError("Go toolchain or compiled source changed")
    vendor_after = dev.mu_vendor_closure(common)
    dev.put(receipts / "mu-vendor-5083.after.json", vendor_after)
    if vendor_after != vendor_before:
        raise RuntimeError("Mu public vendor changed")
    mu_after = {**mu_compiled, "files": dev.file_rows(row["path"] for row in mu_compiled["files"])}
    dev.put(receipts / "mu-compiled-inputs.after.json", mu_after)
    if mu_after != mu_compiled:
        raise RuntimeError("Mu compiled input changed")
    public_after = {name: {"sha256": dev.sha256(p), "bytes": p.stat().st_size} for name, p in public.items()}
    dev.put(receipts / "public-mu.after.json", public_after)
    if public_after != public_before:
        raise RuntimeError("Mu public external input changed")
    files = dev.inventory(output)
    paths = {name: {"path": path.relative_to(output).as_posix(), "sha256": dev.sha256(path)}
             for name, path in binaries.items()}
    numbered = [int(p.name[:4]) for p in migrations if re.match(r"^\d{4}_", p.name)]
    schema_version = max(numbered)
    marker = {"schema": SCHEMA, "mode": "OWNED_PRODUCT_LAYOUT_NOT_INSTALLER",
              "install_root": str(output), "source_commit": before["head"],
              "source_digest": before["digest"], "product_version": "2.4.0",
              "client_protocol": "researchos-client/2", "schema_version": schema_version,
              "binaries": paths, "files": files,
              "tool_hashes": {name: dev.sha256(path) for name, path in tools.items()},
              "go_compiled_input_sha256": dev.sha256(receipts / "go-compiled-inputs.before.json"),
              "mu_compiled_input_sha256": dev.sha256(receipts / "mu-compiled-inputs.before.json"),
              "mu_vendor_5083_sha256": dev.sha256(receipts / "mu-vendor-5083.before.json"),
              "client_wire_input_digest": client_result["build_input_digest"]}
    marker["installation_id"] = install_id(before["head"], "2.4.0", "researchos-client/2", schema_version, paths)
    dev.put(output / "installed-product.json", marker)
    dev.exact_copy(output / "installed-product.json", receipts / "installed-product.json")
    dev.put(receipts / "result.json", {"status": "BUILT_NOT_NATIVE_TESTED_NOT_INSTALLER",
                                      "output": str(output), "installation_id": marker["installation_id"],
                                      "manifest_sha256": dev.sha256(output / "installed-product.json"),
                                      "file_count": len(files), "electron_file_count": electron_count,
                                      "source_drift": False, "input_drift": False, "formal_increment": 0})
    print(json.dumps({"status": "BUILT_NOT_NATIVE_TESTED_NOT_INSTALLER", "output": str(output),
                      "manifest_sha256": dev.sha256(output / "installed-product.json"),
                      "installation_id": marker["installation_id"], "files": len(files)}))


def main():
    parser = argparse.ArgumentParser()
    for name in ["go", "node", "electron-dist", "module-cache", "web-modules", "mu-common", "output", "receipts"]:
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        build(args)
    except Exception as error:
        receipts = Path(args.receipts)
        if receipts.is_dir() and not (receipts / "failed.json").exists():
            dev.put(receipts / "failed.json", {"status": "FIRST_FAILURE_RETAINED", "error": str(error),
                                               "error_type": type(error).__name__})
        print(f"product layout build failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
