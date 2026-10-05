"""W18-02: production backup -> new data root -> real CLI and Electron.

Run only from the integrated main checkout with an exclusive GUI window. The
scenario is a constructed FIXTURE; it never invokes a provider or a Run.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import uuid


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(label, argv, cwd, receipt, env=None, timeout=180):
    options = {"cwd": str(cwd), "env": env, "encoding": "utf-8", "errors": "replace", "capture_output": True, "timeout": timeout}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run([str(arg) for arg in argv], **options)
    (receipt / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (receipt / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    save(receipt / f"{label}.command.json", {"argv": list(map(str, argv)), "cwd": str(cwd), "exit_code": result.returncode})
    if result.returncode:
        raise RuntimeError(f"{label} exit {result.returncode}; see raw receipt")
    return result


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_host(discovery_path, proc):
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError(f"control exited {proc.returncode}")
        try:
            discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
            with urllib.request.urlopen(discovery["url"] + "/healthz", timeout=1) as response:
                if response.status == 200:
                    return discovery
        except (OSError, ValueError, KeyError, TimeoutError):
            pass
        time.sleep(0.2)
    raise RuntimeError("restored control host did not become ready")


def stop_owned(proc):
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--receipt-base", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if os.name != "nt":
        raise RuntimeError("Windows native Host/Electron scenario only")
    locked_file = repo / "execution" / "toolchains" / "locked.json"
    locked = json.loads(locked_file.read_text(encoding="utf-8"))["tools"]
    tools = {name: Path(locked[name]["path"]).resolve() for name in ("go", "node", "python")}
    for name, executable in tools.items():
        if not executable.is_file() or sha256(executable).lower() != locked[name]["sha256"].lower():
            raise RuntimeError(f"locked {name} path or SHA-256 mismatch: {executable}")
    if Path(sys.executable).resolve() != tools["python"]:
        raise RuntimeError("launch gui_restore_run.py with locked Python interpreter")
    root = (repo / ".local" / "w1802-gui" / ("run-" + uuid.uuid4().hex[:12])).resolve()
    root.mkdir(parents=True, exist_ok=False)
    receipt_base = (args.receipt_base or repo / "execution" / "v2.4" / "receipts" / "W18").resolve()
    receipt = receipt_base / ("W18-02-gui-" + time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    receipt.mkdir(parents=True, exist_ok=False)
    build = root / "build"
    build.mkdir()
    binaries = {name: build / (name + ".exe") for name in ("backup", "gui_fixture", "control", "researchos")}
    sources = {
        "backup": "./ops/backup",
        "gui_fixture": "./tests/backup/gui_fixture",
        "control": "./apps/control",
        "researchos": "./apps/cli",
    }
    stage = "build"
    control = electron = None
    save(receipt / "provenance.json", {"mode": "FIXTURE", "scenario": "W18-02 restored new data root, same session/goal/next task", "source_repo": str(repo), "fixture_dir": str(root), "provider_calls_by_harness": 0})
    save(receipt / "locked-tools.json", {"source": str(locked_file), "source_sha256": sha256(locked_file),
                                         "verified": {name: {"path": str(exe), "sha256": sha256(exe)} for name, exe in tools.items()}})
    try:
        for name, source in sources.items():
            command("build-" + name, [tools["go"], "build", "-o", binaries[name], source], repo, receipt)
        # The integrated React sources may be newer than an ignored local dist.
        vite = repo / "apps" / "web" / "node_modules" / "vite" / "bin" / "vite.js"
        if not vite.is_file():
            raise RuntimeError("installed Vite entry unavailable")
        command("build-web", [tools["node"], vite, "build"], repo / "apps" / "web", receipt)
        dist = repo / "apps" / "web" / "dist" / "index.html"
        if not dist.is_file():
            raise RuntimeError("React web dist unavailable; build it in integrated main before the GUI window")
        electron_exe = repo / "apps" / "desktop" / "node_modules" / "electron" / "dist" / "electron.exe"
        if not electron_exe.is_file():
            raise RuntimeError("installed Electron executable unavailable")
        save(receipt / "source-hashes.json", {str(path.relative_to(repo)): sha256(path) for path in [
            repo / "tests" / "backup" / "gui_fixture" / "main_windows.go",
            repo / "tests" / "backup" / "gui_restore.cjs",
            repo / "tests" / "backup" / "gui_restore_run.py",
            locked_file, vite,
            repo / "ops" / "backup" / "main.go",
            repo / "apps" / "control" / "main.go",
            repo / "apps" / "cli" / "main.go",
            repo / "apps" / "desktop" / "main" / "main.js",
            repo / "apps" / "web" / "src" / "workbench.jsx", dist,
        ]})
        save(receipt / "web-dist-hashes.json", {str(path.relative_to(repo)): sha256(path)
                                               for path in sorted(dist.parent.rglob("*")) if path.is_file()})
        save(receipt / "tool-hashes.json", {name: sha256(binary) for name, binary in binaries.items()} |
             {"electron.exe": sha256(electron_exe), "vite.js": sha256(vite)})
        stage = "fixture_and_restore"
        fixture_dir = root / "fixture"
        fixture = command("fixture", [binaries["gui_fixture"], "--repo", repo, "--dir", fixture_dir,
                                      "--backup-exe", binaries["backup"]], repo, receipt)
        meta = json.loads(fixture.stdout)
        meta_path = fixture_dir / "metadata.json"
        save(receipt / "fixture-metadata.json", meta)
        save(receipt / "backup-command-results.json", json.loads((fixture_dir / "setup-commands.json").read_text(encoding="utf-8")))
        restored = Path(meta["restored_data_root"])
        if restored.resolve() == Path(meta["source_data_root"]).resolve() or restored.resolve() == Path(meta["source_workspace"]).resolve():
            raise RuntimeError("restore reused source directory")
        stage = "restored_control"
        discovery_path = root / "restored-discovery.json"
        env = os.environ.copy()
        env.update(RESEARCHOS_DATA_DIR=str(restored), RESEARCHOS_WEB_DIR=str(repo / "apps" / "web" / "dist"),
                   RESEARCHOS_LISTEN="127.0.0.1:0", RESEARCHOS_CLI_DISCOVERY=str(discovery_path),
                   RESEARCHOS_HOST_DISCOVERY=str(discovery_path), RESEARCHOS_CLI_CONFIG=str(root / "cli-config.json"))
        out = open(receipt / "control.stdout.txt", "w", encoding="utf-8")
        err = open(receipt / "control.stderr.txt", "w", encoding="utf-8")
        control = subprocess.Popen([str(binaries["control"]), "--discovery-file", str(discovery_path)], cwd=repo,
                                   env=env, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            discovery = wait_host(discovery_path, control)
        finally:
            out.close(); err.close()
        if Path(discovery["data_dir"]).resolve() != restored.resolve():
            raise RuntimeError("control connected to wrong data root")
        save(receipt / "restored-discovery-redacted.json", {k: discovery[k] for k in ("url", "pid", "data_dir", "host_instance_id") if k in discovery})
        stage = "cli"
        cli = command("cli-status", [binaries["researchos"], "status", "--project", meta["project_id"],
                                     "--session", meta["session_id"], "--output", "jsonl"], repo, receipt, env)
        cli_rows = [json.loads(line) for line in cli.stdout.splitlines() if line.strip()]
        operations = cli_rows[0].get("operations", []) if len(cli_rows) == 1 else []
        session_result = next((row.get("result", {}) for row in operations if row.get("method") == "session.get"), {})
        continuation = cli_rows[0].get("continuation", {}) if len(cli_rows) == 1 else {}
        next_step = continuation.get("next_step") or {}
        unfinished = continuation.get("unfinished_tasks") or []
        cli_checks = {"session_id_exact": session_result.get("session_id") == meta["session_id"],
                      "project_id_exact": session_result.get("project_id") == meta["project_id"],
                      "goal_id_exact": session_result.get("goal_id") == meta["goal_id"],
                      "restored_event_cursor": session_result.get("event_sequence") == meta["event_cursor"],
                      "continuation_available": continuation.get("status") == "AVAILABLE",
                      "continuation_scope_exact": continuation.get("project_id") == meta["project_id"] and
                      continuation.get("session_id") == meta["session_id"] and continuation.get("goal_id") == meta["goal_id"],
                      "continuation_watermark_exact": continuation.get("event_watermark") == meta["event_cursor"],
                      "continuation_goal_exact": continuation.get("goal", {}).get("id") == meta["goal_id"] and
                      continuation.get("goal", {}).get("title") == meta["goal_title"],
                      "only_unfinished_task_exact": len(unfinished) == 1 and unfinished[0].get("id") == meta["task_id"] and
                      unfinished[0].get("title") == meta["task_title"],
                      "next_step_original_task": continuation.get("selection") == "UNIQUE" and
                      next_step.get("task_id") == meta["task_id"] and next_step.get("title") == meta["task_title"] and
                      next_step.get("source") == "ONLY_UNFINISHED_TASK",
                      "host_url_matches_restored_discovery": cli_rows[0].get("host_url") == discovery["url"] if len(cli_rows) == 1 else False,
                      "status_completed": len(cli_rows) == 1 and cli_rows[0].get("status") == "COMPLETED" and
                      all(row.get("status") == "COMPLETED" for row in operations)}
        save(receipt / "cli-checks.json", cli_checks)
        save(receipt / "cli-next-task-visibility.json", {"status": "PASS" if all(cli_checks.values()) else "FAIL",
              "previous_gap": "Frozen SessionSnapshot has no task_id; earlier status only exposed session.get and host.status. Older receipts are unchanged.",
              "continuation": continuation, "task_provenance": "CLI read-only public v1 continuation and authenticated Electron ros-app Task route"})
        if not all(cli_checks.values()):
            raise RuntimeError("CLI_ASSERTION_FAILED:" + json.dumps(cli_checks))
        stage = "electron"
        cdp_port = free_port()
        user_data = root / "electron-user-data"
        env.update(RESEARCHOS_DESKTOP_USER_DATA=str(user_data), RESEARCHOS_PROJECT_ID=meta["project_id"],
                   RESEARCHOS_SESSION_ID=meta["session_id"])
        out = open(receipt / "electron.stdout.txt", "w", encoding="utf-8")
        err = open(receipt / "electron.stderr.txt", "w", encoding="utf-8")
        electron = subprocess.Popen([str(electron_exe), str(repo / "apps" / "desktop"),
                                     f"--remote-debugging-port={cdp_port}"], cwd=repo, env=env,
                                    stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            command("gui-cdp", [tools["node"], repo / "tests" / "backup" / "gui_restore.cjs", str(cdp_port), meta_path, receipt],
                    repo, receipt, env, timeout=120)
        finally:
            out.close(); err.close()
        save(receipt / "result.json", {"status": "PASS", "mode": "FIXTURE", "cli_checks": cli_checks,
                                      "gui_checks": json.loads((receipt / "gui-checks.json").read_text(encoding="utf-8")),
                                      "provider_calls_by_harness": 0, "restored_data_root": str(restored)})
        print(json.dumps({"status": "PASS", "receipt": str(receipt), "restored_data_root": str(restored)}))
    except Exception as exc:
        save(receipt / "result.json", {"status": "FAIL", "stage": stage, "error": str(exc), "mode": "FIXTURE"})
        print(json.dumps({"status": "FAIL", "stage": stage, "error": str(exc), "receipt": str(receipt)}), file=sys.stderr)
        return 1
    finally:
        stop_owned(electron)
        stop_owned(control)
    return 0


if __name__ == "__main__":
    sys.exit(main())
