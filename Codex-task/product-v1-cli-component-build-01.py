#!/usr/bin/env python3
"""CLI component only. Run under Root's registered f13 Job; never runs the CLI."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
WORKTREE = Path(r"D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104")
COMMON = Path(r"D:/作品集/ResearchOS/research-os")
EXPECTED_HEAD = "c4029c0b57599e1aafed6d01ea4034b0cf465ccd"
BUILDER_SHA256 = "f571ef6b73b8e7e2ce94113c6749b0aac0a5e1851f59dc7fbb2eafd213690032"
EMBEDS = (
    "adapters/protectedstore/frozen_development.json",
    "internal/api/contracts/client.protocol.schema.json",
    "internal/api/contracts/domain.schema.json",
    "internal/domain/contracts/client.protocol.domain.schema.json",
    "internal/domain/contracts/client.protocol.schema.json",
    "internal/domain/contracts/coding_delivery_bindings.sql",
    "internal/domain/contracts/evaluation-v24.schema.json",
    "internal/domain/contracts/new-project-rules-v24.json",
    "internal/domain/contracts/new-project-rules-v24.md",
    "internal/domain/contracts/persistence-v24.schema.json",
    "internal/domain/contracts/prepared_run_abandonment.sql",
)

def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def main():
    root = WORKTREE.resolve(strict=True)
    output = root / ".local" / "cli-v1-artifact-01"
    output.mkdir(parents=True, exist_ok=False)  # Retain every prior outcome; never reuse.
    receipts = output / "receipts"
    receipts.mkdir()
    result = {"schema": "researchos.cli-component-build/1", "status": "FAILED",
              "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "worktree": str(root), "expected_head": EXPECTED_HEAD,
              "application_executions": 0, "native_host_operations": 0,
              "model_requests": 0, "help_executed": False, "formal_increment": 0}
    try:
        helper_path = root / "apps/desktop/build-development.py"
        if digest(helper_path) != BUILDER_SHA256:
            raise RuntimeError("registered existing build helper changed")
        spec = importlib.util.spec_from_file_location("cli_component_existing_helpers", helper_path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)  # Definitions only; never helper.main()/build().
        go_root = COMMON / ".local/tools/go1.27.1/go"
        go = go_root / "bin/go.exe"
        module_cache = COMMON / ".local/tools/gopath/pkg/mod"
        scratch = {name: output / name for name in ("go-cache", "go-tmp", "profile")}
        for path in scratch.values():
            path.mkdir()
        for name in ("tmp", "user", "appdata", "localappdata", "hooks"):
            (scratch["profile"] / name).mkdir()
        git_config = scratch["profile"] / "empty.gitconfig"
        git_config.write_bytes(b"")
        env = {name: os.environ[name] for name in
               ("SystemRoot", "WINDIR", "PATH", "PATHEXT", "COMSPEC") if name in os.environ}
        git_exe = shutil.which("git", path=env.get("PATH"))
        if not git_exe:
            raise RuntimeError("local Git metadata tool unavailable")
        git_exe = Path(git_exe).resolve(strict=True)
        system = Path(env["SystemRoot"])
        env["PATH"] = os.pathsep.join(map(str, (go.parent, git_exe.parent, system / "System32", system)))
        env.update({"GOENV": "off", "GOTOOLCHAIN": "local", "GOROOT": str(go_root),
                    "GOPATH": str(module_cache.parent.parent), "GOMODCACHE": str(module_cache),
                    "GOCACHE": str(scratch["go-cache"]), "GOTMPDIR": str(scratch["go-tmp"]),
                    "GOPROXY": "off", "GOSUMDB": "off", "GOWORK": "off", "CGO_ENABLED": "0",
                    "GOOS": "windows", "GOARCH": "amd64", "GOAMD64": "v1",
                    "GOFLAGS": "", "GOEXPERIMENT": "", "GOMAXPROCS": "2",
                    "TEMP": str(scratch["profile"] / "tmp"), "TMP": str(scratch["profile"] / "tmp"),
                    "USERPROFILE": str(scratch["profile"] / "user"),
                    "APPDATA": str(scratch["profile"] / "appdata"),
                    "LOCALAPPDATA": str(scratch["profile"] / "localappdata"),
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(git_config),
                    "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never",
                    "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.fsmonitor",
                    "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "core.hooksPath",
                    "GIT_CONFIG_VALUE_1": str(scratch["profile"] / "hooks"),
                    "PYTHONDONTWRITEBYTECODE": "1"})
        def run(name, argv):
            # Existing raw/recipe/actual-native-exit receipts. f13 bounds this process tree.
            return helper.run_command(receipts, name, argv, root, env)
        def git_state(label):
            head = run(label + "-head", [git_exe, "rev-parse", "HEAD"]).decode("ascii").strip()
            tree = run(label + "-tree", [git_exe, "show", "-s", "--format=%T", "HEAD"]).decode("ascii").strip()
            status = run(label + "-status", [git_exe, "status", "--porcelain=v1", "--untracked-files=all"])
            if head != EXPECTED_HEAD or status.strip():
                raise RuntimeError("registered source head/tree is not clean")
            return {"head": head, "tree": tree, "status_sha256": hashlib.sha256(status).hexdigest()}
        before = git_state("source-before")
        missing = [name for name in EMBEDS if not helper.regular(root / name)]
        if missing:
            raise RuntimeError("public embed materialization missing: " + ", ".join(missing))
        version_file = (go_root / "VERSION").read_bytes()
        if version_file.splitlines()[0] != b"go1.27.1":
            raise RuntimeError("locked Go VERSION mismatch")
        list_args = [go, "list", "-mod=readonly", "-deps", "-compiled", "-json", "./apps/cli"]
        raw = run("cli-go-list-before", list_args)
        closure_before = helper.go_compiled_closure([raw], go_root)
        extra = helper.file_rows([go, git_exe, root / "go.mod", root / "go.sum",
                                  root / "execution/toolchains/locked.json", helper_path, Path(__file__)])
        inputs_before = {"compiled": closure_before, "extra": extra, "source": before,
                         "effective_environment": env}
        helper.put(receipts / "inputs.before.json", inputs_before)
        binary = output / "bin/researchos.exe"
        binary.parent.mkdir()
        run("cli-go-build", [go, "build", "-mod=readonly", "-trimpath", "-buildvcs=true",
                             "-p=2", "-o", binary, "./apps/cli"])
        info = run("cli-artifact-buildinfo", [go, "version", "-m", binary]).decode("utf-8")
        if "go1.27.1" not in info or "vcs.revision=" + EXPECTED_HEAD not in info or "vcs.modified=false" not in info:
            raise RuntimeError("artifact build information differs from registered source")
        closure_after = helper.go_compiled_closure([run("cli-go-list-after", list_args)], go_root)
        after = git_state("source-after")
        extra_after = helper.file_rows([go, git_exe, root / "go.mod", root / "go.sum",
                                        root / "execution/toolchains/locked.json", helper_path, Path(__file__)])
        if closure_before != closure_after or extra != extra_after or before != after:
            raise RuntimeError("CLI source/tool/module/compiled input drift")
        helper.put(receipts / "inputs.after.json",
                   {"compiled": closure_after, "extra": extra_after, "source": after})
        manifest = {"schema": "researchos.cli-component-artifact/1", "source": after,
                    "toolchain": {"version": "go1.27.1", "go_sha256": digest(go),
                                  "git_sha256": digest(git_exe),
                                  "version_file_sha256": digest(go_root / "VERSION")},
                    "binary": {"path": str(binary), "sha256": digest(binary),
                               "bytes": binary.stat().st_size},
                    "inputs_before_sha256": digest(receipts / "inputs.before.json"),
                    "inputs_after_sha256": digest(receipts / "inputs.after.json"),
                    "recipe_sha256": digest(Path(__file__)), "build_helper_sha256": BUILDER_SHA256,
                    "go_mod_sha256": digest(root / "go.mod"), "go_sum_sha256": digest(root / "go.sum"),
                    "buildinfo_stdout_sha256": digest(receipts / "commands/cli-artifact-buildinfo/stdout.raw"),
                    "application_executed": False, "qualification": "BUILT_NOT_EXECUTED"}
        helper.put(output / "artifact-manifest.json", manifest)
        result.update({"status": "BUILT_NOT_EXECUTED", "native_exit": 0, "source": after,
                       "artifact_manifest_sha256": digest(output / "artifact-manifest.json"),
                       "binary_sha256": manifest["binary"]["sha256"],
                       "build_inputs_unchanged": True})
    except Exception as error:
        result.update({"error_type": type(error).__name__, "error": str(error), "native_exit": 1})
    result["ended_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (receipts / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "BUILT_NOT_EXECUTED" else 1

if __name__ == "__main__":
    sys.exit(main())
