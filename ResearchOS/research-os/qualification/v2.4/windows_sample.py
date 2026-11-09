"""Install a finite, portable qualification sample and start its actual Desktop.

No system installation, provider configuration, service, or user data changes.
The product main/preload/renderer/CLI/control bytes are used without patching.
"""
import json
from contextlib import closing
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import time
import urllib.request
import zipfile

from parent_gates import REPO, digest, read, save


def tree(path):
    return {p.relative_to(path).as_posix(): digest(p) for p in sorted(path.rglob("*")) if p.is_file()}


def run_sample(g):
    stage = g.local / "assembly"
    installed = g.local / "installed"
    stage.mkdir()
    env = g.env()
    before = g.source_snapshot()
    save(g.out / "product-sources-before.json", before)
    # Copy the Electron distribution and product files to the package, without
    # borrowing mutable files from the source checkout at runtime.
    copies = ("apps/desktop/main", "apps/desktop/preload", "migrations/sqlite",
              "spec/v2.0/contracts", "internal/api/contracts", "contracts")
    for rel in copies:
        shutil.copytree(REPO / rel, stage / rel)
    shutil.copy2(REPO / "apps/desktop/package.json", stage / "apps/desktop/package.json")
    shutil.copytree(g.tool("electron").parent, stage / "runtime")
    for rel in ("third_party/mu/LICENSE", "third_party/mu/desktop/LICENSE"):
        target = stage / "licenses" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, target)
    (stage / "bin").mkdir()
    for name, source in (("control", "./apps/control"), ("researchos", "./apps/cli"),
                         ("backup", "./ops/backup"), ("gui_fixture", "./tests/backup/gui_fixture")):
        code, _, _ = g.cmd("build-" + name, [g.tool("go"), "build", "-o", stage / "bin" / (name + ".exe"), source], env=env)
        if code:
            raise RuntimeError("build failed: " + name)
    # Installed dependencies are read-only. Current main renderer inputs must
    # match the isolated source exactly before building into this owned stage.
    web_inputs = {str(p.relative_to(REPO)): digest(p) for p in (REPO / "apps/web/src").rglob("*") if p.is_file()}
    for rel in ("apps/web/index.html", "apps/web/package.json", "apps/web/package-lock.json"):
        web_inputs[rel] = digest(REPO / rel)
    for rel, value in web_inputs.items():
        g.input(rel, value, g.main)
    code, _, _ = g.cmd("build-renderer", [g.tool("node"), g.tool("vite"), "build", "--outDir", stage / "apps/web/dist"],
                        cwd=g.main / "apps/web", env=env)
    if code:
        raise RuntimeError("renderer build failed")
    assembly_hashes = tree(stage)
    save(g.out / "assembly-files.json", assembly_hashes)
    package = g.local / "qualification-portable.zip"
    with zipfile.ZipFile(package, "x", compression=zipfile.ZIP_STORED) as archive:
        for rel in assembly_hashes:
            archive.write(stage / rel, rel)
    # This is the qualification installation step: install the complete package
    # in an empty directory, compare every installed byte, launch only from it.
    installed.mkdir()
    with zipfile.ZipFile(package) as archive:
        archive.extractall(installed)
    installed_hashes = tree(installed)
    save(g.out / "installed-files.json", installed_hashes)
    save(g.out / "installation.json", {"kind": "PORTABLE_QUALIFICATION_SAMPLE", "archive_sha256": digest(package),
         "assembly": str(stage), "destination": str(installed), "file_count": len(installed_hashes),
         "algorithm": "zipfile exclusive-create archive -> extract into newly created empty directory -> SHA-256 every file",
         "system_installer": False, "production_final_installer": False, "requires_independent_scope_review": True})
    g.check("qualification_sample_installed_exactly", assembly_hashes == installed_hashes and bool(installed_hashes),
            {"files": len(installed_hashes), "installation": "Portable qualification sample installed in empty isolated directory"})
    for label, argv in (("go-version", [g.tool("go"), "version"]), ("node-version", [g.tool("node"), "--version"]),
                        ("cli-version", [installed / "bin/researchos.exe", "--version"])):
        code, stdout, _ = g.cmd(label, argv, cwd=installed, env=env)
        g.check(label, code == 0 and bool(stdout.strip()), stdout.strip())
    fixture = g.local / "fixture"
    code, raw, _ = g.cmd("fixture", [installed / "bin/gui_fixture.exe", "--repo", installed, "--dir", fixture,
                                    "--backup-exe", installed / "bin/backup.exe"], cwd=installed, env=env)
    if code:
        raise RuntimeError("qualification fixture creation failed")
    meta = json.loads(raw)
    save(g.out / "fixture-metadata.json", meta)
    save(g.out / "fixture-setup-commands.json", read(fixture / "setup-commands.json"))
    def counts():
        with closing(sqlite3.connect((Path(meta["restored_data_root"]) / "researchos.sqlite").as_uri() + "?mode=ro", uri=True)) as db:
            return {"tasks": db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", (meta["project_id"],)).fetchone()[0],
                    "runs": db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'", (meta["project_id"],)).fetchone()[0],
                    "effects": db.execute("SELECT count(*) FROM resource_effects WHERE project=?", (meta["project_id"],)).fetchone()[0]}
    prior_counts = counts()
    originals = [Path(meta["source_data_root"]) / "researchos.sqlite", Path(meta["source_workspace"]) / "src/main.go"]
    original_hashes = {str(p): digest(p) for p in originals}
    save(g.out / "business-before.json", {"counts": prior_counts, "source_hashes": original_hashes})
    discovery = g.local / "discovery.json"
    env.update(RESEARCHOS_DATA_DIR=meta["restored_data_root"], RESEARCHOS_WEB_DIR=str(installed / "apps/web/dist"),
               RESEARCHOS_LISTEN="127.0.0.1:0", RESEARCHOS_CLI_DISCOVERY=str(discovery),
               RESEARCHOS_HOST_DISCOVERY=str(discovery), RESEARCHOS_CLI_CONFIG=str(g.local / "cli-config.json"),
               RESEARCHOS_DESKTOP_USER_DATA=str(g.local / "desktop-profile"),
               RESEARCHOS_PROJECT_ID=meta["project_id"], RESEARCHOS_SESSION_ID=meta["session_id"])
    control = electron = None
    streams = []
    try:
        for suffix in ("stdout", "stderr"):
            streams.append((g.out / ("installed-control." + suffix + ".txt")).open("x", encoding="utf-8"))
        argv = [str(installed / "bin/control.exe"), "--discovery-file", str(discovery)]
        control = subprocess.Popen(argv, cwd=installed, env=env, stdout=streams[0], stderr=streams[1], creationflags=subprocess.CREATE_NO_WINDOW)
        command = {"argv": argv, "cwd": str(installed), "pid": control.pid, "isolation": "fresh data root; no provider/runtime config"}
        save(g.out / "installed-control.command.json", command)
        for _ in range(100):
            if control.poll() is not None:
                raise RuntimeError("installed control exited: " + str(control.returncode))
            try:
                info = read(discovery)
                with urllib.request.urlopen(info["url"] + "/healthz", timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("isolated installed Host not ready")
        save(g.out / "installed-host-public.json", {key: info.get(key) for key in ("url", "pid", "data_dir", "host_instance_id")})
        code, raw, _ = g.cmd("cli-status", [installed / "bin/researchos.exe", "status", "--project", meta["project_id"],
                                             "--session", meta["session_id"], "--output", "jsonl"], cwd=installed, env=env)
        cli = json.loads(raw)
        host_result = next(row["result"] for row in cli["operations"] if row["method"] == "host.status")
        g.check("installed_cli_same_host", code == 0 and cli["host_url"] == info["url"] and host_result["host_state"] == "READY",
                {"host_url": cli["host_url"], "host_instance_id": host_result["host_instance_id"], "core_build_id": host_result["core_build_id"]})
        # Start the same installed sample normally and observe actual native
        # session/Goal/Task/writer continuation through its real renderer.
        for key in ("ROS_DESKTOP_SMOKE", "ROS_DESKTOP_NATIVE_SMOKE", "ROS_DESKTOP_CAPTURE_PATH"):
            env.pop(key, None)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        for suffix in ("stdout", "stderr"):
            streams.append((g.out / ("electron." + suffix + ".txt")).open("x", encoding="utf-8"))
        argv = [str(installed / "runtime/electron.exe"), str(installed / "apps/desktop"), "--remote-debugging-port=" + str(port)]
        electron = subprocess.Popen(argv, cwd=installed, env=env, stdout=streams[2], stderr=streams[3], creationflags=subprocess.CREATE_NO_WINDOW)
        save(g.out / "electron.command.json", {"argv": argv, "cwd": str(installed), "pid": electron.pid})
        observer = g.input("tests/backup/gui_restore.cjs")
        code, _, _ = g.cmd("gui-cdp", [g.tool("node"), observer, str(port), fixture / "metadata.json", g.out], cwd=REPO, env=env)
        gui = read(g.out / "gui-checks.json")
        report_lines = (g.out / "electron.stdout.txt").read_text(encoding="utf-8").splitlines()
        reports = [json.loads(line.removeprefix("ROS_DESKTOP_REPORT ")) for line in report_lines if line.startswith("ROS_DESKTOP_REPORT ")]
        report = reports[0] if len(reports) == 1 else {}
        save(g.out / "installed-desktop-report.json", report)
        native_writer = read(g.out / "native-resumed-writer.json")
        g.check("installed_desktop_started_actual_native", code == 0 and report.get("event") == "ready_to_show" and
                report.get("host_url") == info["url"] and report.get("electron") == "37.10.3" and
                report.get("renderer", {}).get("bridge") is True and native_writer.get("host_ok") is True and
                (g.out / "01-session-list.png").is_file(), report)
        g.check("qualification_host_client_versions", report.get("protocol") == "researchos-client/2" and
                "researchos-client/2" in host_result["protocol_versions"],
                {"electron": report.get("electron"), "desktop_package": read(installed / "apps/desktop/package.json")["version"],
                 "host_core_build_id": host_result["core_build_id"], "protocol": report.get("protocol"),
                 "upstream_mu_commit": g.pin["mu_commit"], "bundle_sha256": g.pin["tools"]["mu_worker"]["sha256"]})
        after_counts = counts()
        after_originals = {str(p): digest(p) for p in originals}
        save(g.out / "business-after.json", {"counts": after_counts, "source_hashes": after_originals})
        gui.update(no_new_task_run_or_effect=prior_counts == after_counts, original_source_bytes_unchanged=original_hashes == after_originals)
        session = next(row["result"] for row in cli["operations"] if row["method"] == "session.get")
        continuation = cli["continuation"]
        cli_checks = {"session_id_exact": session["session_id"] == meta["session_id"],
          "project_id_exact": session["project_id"] == meta["project_id"], "goal_id_exact": session["goal_id"] == meta["goal_id"],
          "restored_event_cursor": session["event_sequence"] == meta["event_cursor"], "continuation_available": continuation["status"] == "AVAILABLE",
          "continuation_scope_exact": all(continuation[k] == meta[k] for k in ("project_id", "session_id", "goal_id")),
          "continuation_watermark_exact": continuation["event_watermark"] == meta["event_cursor"],
          "continuation_goal_exact": continuation["goal"]["id"] == meta["goal_id"],
          "only_unfinished_task_exact": [t["id"] for t in continuation["unfinished_tasks"]] == [meta["task_id"]],
          "next_step_original_task": continuation["next_step"]["task_id"] == meta["task_id"],
          "host_url_matches_restored_discovery": cli["host_url"] == info["url"], "status_completed": cli["status"] == "COMPLETED"}
        from parent_gates import strict_results
        rows = [{"id": k, "ok": v} for k, v in cli_checks.items()] + [{"id": "gui_" + k, "ok": v} for k, v in gui.items()]
        passed = code == 0 and strict_results(rows, g.pin["dual_end_assertions"])
        g.check("installed_actual_dual_end_current", passed, rows)
        save(g.out / "result.json", {"status": "PASS" if passed else "FAIL", "mode": "FIXTURE", "cli_checks": cli_checks,
             "gui_checks": gui, "provider_calls_by_harness": 0, "formal_cases_accepted": [], "whole_card_accepted": False})
    finally:
        if electron is not None:
            if electron.poll() is None:
                g.cmd("stop-owned-electron", ["taskkill", "/PID", str(electron.pid), "/T", "/F"], timeout=15)
                electron.wait(timeout=15)
        if control is not None:
            if control.poll() is None:
                code, _, _ = g.cmd("stop-owned-control", ["taskkill", "/PID", str(control.pid), "/T", "/F"], timeout=15)
                control.wait(timeout=15)
            save(g.out / "owned-process-cleanup.json", {"control_pid": control.pid, "control_exit": control.returncode,
                 "desktop_process": "observed GUI tree stopped by owned PID", "electron_pid": electron.pid if electron else None,
                 "electron_exit": electron.returncode if electron else None, "only_owned_pid_targeted": True})
        for stream in streams:
            stream.close()
    after = g.source_snapshot()
    save(g.out / "product-sources-after.json", after)
    save(g.out / "source-hashes.json", before)
    g.check("build_inputs_stable", before == after, "Tracked product sources unchanged")
    g.inputs.update({str(REPO / rel): value for rel, value in before.items()})
    # Formal evidence is outside .local and retained. Only this UUID's temp data
    # is removed after exact containment verification.
    resolved = g.local.resolve()
    if resolved.parent != (REPO / ".local/w0199").resolve():
        raise RuntimeError("cleanup containment failure")
    shutil.rmtree(resolved)
    save(g.out / "temporary-cleanup.json", {"path": str(resolved), "removed": not resolved.exists()})
