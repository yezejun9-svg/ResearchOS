"""One offline build with complete argv, environment, input, and exit receipts."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


PREP = Path(__file__).resolve().parent
REPO = Path(r"D:\作品集\ResearchOS\research-os")
WORKTREE = REPO / ".local" / "worktrees" / "desktop-installed-delivery-20261025"
ARTIFACT = WORKTREE / ".local" / "native-folder-environment-cp570" / "revision02"
TOOL = REPO / ".local" / "tools" / "go1.27.1" / "go" / "bin" / "go.exe"
SCOPE = REPO / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp571/Native-folder-environment-preparation02-scope.json"
EXPECTED = {
    "scope": "dff6c62374875c158d612c0cf50c8cc5472a70cff789b5b1b2ce8c5f274cdfa1",
    "source": "e79f977b5d7b21a6cc93034120984110816a6fdfdd9148a6a4e13dbc9f4e5433",
    "go": "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490",
    "go.mod": "da440b404321e2fc6395c17b8959931ba63bdb17fb559e27de6b722f030aaf86",
    "go.sum": "f565f3ebabba59ab96c382d6672c61549e5b97a36a3d51f6439e1a492179d239",
}


def ref(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(name, payload):
    with (PREP / name).open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    if os.name != "nt" or len(sys.argv) != 1:
        raise SystemExit("offline Windows build only")
    assert ref(SCOPE)["sha256"] == EXPECTED["scope"]
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    assert scope["native_execution_authorized"] is False
    assert Path(scope["write_root"]).resolve() == PREP and Path(scope["artifact_root"]).resolve() == ARTIFACT
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKTREE, text=True).strip() == scope["candidate_commit"]
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=WORKTREE) == b""
    inputs = {"scope": ref(SCOPE), "source": ref(WORKTREE / "internal/host/native_folder_windows.go"),
              "transformed": ref(ARTIFACT / "native_folder_windows.go"),
              "main": ref(ARTIFACT / "main.go"), "go": ref(TOOL),
              "go.mod": ref(WORKTREE / "go.mod"), "go.sum": ref(WORKTREE / "go.sum")}
    for name in ("scope", "source", "go", "go.mod", "go.sum"):
        assert inputs[name]["sha256"] == EXPECTED[name]
    source = (WORKTREE / "internal/host/native_folder_windows.go").read_bytes()
    transformed = (ARTIFACT / "native_folder_windows.go").read_bytes()
    assert source.count(b"package host") == 1 and source.replace(b"package host", b"package main") == transformed
    exe = ARTIFACT / "native-folder-environment.exe"
    assert not exe.exists()
    current = os.environ
    env = {key: current[key] for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "PATH",
                                         "SystemDrive", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA")
           if key in current}
    assert env.get("SystemRoot") and env.get("USERPROFILE")
    env.update({"GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off", "GOENV": "off",
                "GOWORK": "off", "GOFLAGS": "-mod=readonly", "CGO_ENABLED": "0",
                "GOPATH": str(Path.home() / "go"), "GOMODCACHE": str(Path.home() / "go" / "pkg" / "mod"),
                "GOCACHE": str(Path.home() / "AppData" / "Local" / "go-build")})
    version_argv = [str(TOOL), "version"]
    version = subprocess.run(version_argv, cwd=WORKTREE, env=env, capture_output=True, shell=False)
    (PREP / "go-version.stdout.raw").write_bytes(version.stdout)
    (PREP / "go-version.stderr.raw").write_bytes(version.stderr)
    if version.returncode != 0 or version.stdout.strip() != b"go version go1.27.1 windows/amd64":
        raise RuntimeError("PINNED_GO_VERSION_MISMATCH")
    argv = [str(TOOL), "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", str(exe),
            str(ARTIFACT / "main.go"), str(ARTIFACT / "native_folder_windows.go")]
    write("build-command.json", {"argv": argv, "cwd": str(WORKTREE), "env": env,
                                 "version_argv": version_argv, "version_exit": version.returncode,
                                 "inputs": inputs, "network": "GOPROXY=off; GOSUMDB=off"})
    completed = subprocess.run(argv, cwd=WORKTREE, env=env, capture_output=True, shell=False)
    (PREP / "build.stdout.raw").write_bytes(completed.stdout)
    (PREP / "build.stderr.raw").write_bytes(completed.stderr)
    write("build-result.json", {"exit_code": completed.returncode, "output": ref(exe) if exe.exists() else None,
                                "stdout": ref(PREP / "build.stdout.raw"),
                                "stderr": ref(PREP / "build.stderr.raw"),
                                "go_version_stdout": ref(PREP / "go-version.stdout.raw"),
                                "go_version_stderr": ref(PREP / "go-version.stderr.raw")})
    if completed.returncode != 0 or not exe.is_file():
        raise RuntimeError("OFFLINE_BUILD_FAILED")


if __name__ == "__main__":
    main()
