"""Task-owned Core/SQLite/Owner browser observation of the real React build."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

REPO = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025")
TMP = Path(r"D:\作品集\ResearchOS\research-os\.local\react-workbench-redesign-20261025-tmp")
RUN = sys.argv[1] if len(sys.argv) > 1 else "03"
if not RUN.isdigit() or len(RUN) != 2:
    raise SystemExit("run suffix must be two digits")
OUT = Path(__file__).parent / f"real-isolated-{RUN}"
CONTROL = TMP / "control.exe"
DATA = TMP / f"real-isolated-{RUN}-data"
CREDS = TMP / f"real-isolated-{RUN}-owner.json"


def record(name, argv, env, mode="run"):
    target = OUT / "commands" / name
    target.mkdir(parents=True, exist_ok=False)
    relevant_env = {key: env[key] for key in ("RESEARCHOS_DATA_DIR", "RESEARCHOS_WEB_DIR", "RESEARCHOS_LISTEN", "RESEARCHOS_CLI_DISCOVERY") if key in env}
    (target / "recipe.json").write_text(json.dumps({"argv": argv, "cwd": str(REPO), "env": relevant_env, "mode": mode}, ensure_ascii=False, indent=2), encoding="utf-8")
    stdout = (target / "stdout.bin").open("wb")
    stderr = (target / "stderr.bin").open("wb")
    if mode == "start":
        proc = subprocess.Popen(argv, cwd=REPO, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        (target / "result.json").write_text(json.dumps({"owned_pid": proc.pid}, indent=2), encoding="utf-8")
        stdout.close(); stderr.close()
        return proc
    result = subprocess.run(argv, cwd=REPO, env=env, stdout=stdout, stderr=stderr, check=False)
    stdout.close(); stderr.close()
    (target / "result.json").write_text(json.dumps({"native_exit": result.returncode}, indent=2), encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} exited {result.returncode}; see retained stderr")


def main():
    if DATA.exists() or CREDS.exists() or OUT.exists():
        raise RuntimeError("fresh task-owned data and output paths required")
    OUT.mkdir(parents=True)
    assert CONTROL.is_file() and (REPO / "apps/web/dist/index.html").is_file()
    env = os.environ.copy()
    env.update(RESEARCHOS_DATA_DIR=str(DATA), RESEARCHOS_WEB_DIR=str(REPO / "apps/web/dist"),
               RESEARCHOS_CLI_DISCOVERY=str(DATA / "discovery.json"))
    report = {"schema": "researchos.react-real-isolated-ui.v1", "kind": "REAL_ISOLATED_CORE_SQLITE_OWNER_UI", "checks": [],
              "limitations": ["Task-owned Owner and SQLite; no external model/provider or worker dispatch.", "No native Desktop, independent review, or formal acceptance asserted."]}
    server = None
    try:
        record("01-bootstrap-owner", [str(CONTROL), "-bootstrap-owner", "-credential-file", str(CREDS)], env)
        owner = json.loads(CREDS.read_text(encoding="utf-8-sig"))
        assert owner["token"] and owner["principal_id"]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env["RESEARCHOS_LISTEN"] = f"127.0.0.1:{port}"
        server = record("02-core-service", [str(CONTROL)], env, "start")
        base = f"http://127.0.0.1:{port}"
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError("owned Core exited before health probe")
            try:
                with urlopen(base + "/healthz", timeout=.4) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(.2)
        else:
            raise RuntimeError("owned Core health probe timed out")
        report["checks"].append("owned Core healthy on loopback with fresh SQLite")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/", wait_until="domcontentloaded")
                page.get_by_label("访问令牌").fill(owner["token"])
                page.get_by_role("button", name="打开工作台").click()
                page.get_by_role("heading", name="项目入口").wait_for(timeout=15000)
                page.get_by_label("项目名称").fill("隔离河流研究")
                page.get_by_label("要解决的问题").fill("核对采样记录来源")
                page.get_by_label("首个明确范围").fill("仅本地隔离数据")
                page.get_by_role("button", name="创建项目").click()
                page.get_by_role("heading", name="隔离河流研究").wait_for(timeout=15000)
                project_url = page.url
                if not project_url.startswith(base + "/p/"):
                    raise RuntimeError("UI did not navigate to the new project")
                report["checks"].append("new project created through real browser UI and opened in workbench")
                page.get_by_role("link", name="研究周期").click()
                page.get_by_role("heading", name="选择研究周期", exact=True, level=1).wait_for(timeout=15000)
                report["checks"].append("research cycle page reached by real navigation")
                page.go_back(wait_until="domcontentloaded")
                page.get_by_role("heading", name="隔离河流研究").wait_for(timeout=15000)
                report["checks"].append("history back restored project workbench")
                if errors:
                    raise RuntimeError("browser page errors: " + repr(errors))
                report["checks"].append("no uncaught browser page errors")
                shot = OUT / "real-project-workbench.png"
                page.screenshot(path=str(shot), full_page=True)
                report["screenshot"] = {"path": str(shot), "sha256": hashlib.sha256(shot.read_bytes()).hexdigest()}
                report["project_path"] = project_url.removeprefix(base)
                report["browser_version"] = browser.version
            finally:
                browser.close()
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = repr(error)
        raise
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=10)
            (OUT / "commands/02-core-service/stop.json").write_text(json.dumps({"owned_pid": server.pid, "native_exit": server.returncode, "stopped_at_unix": time.time()}, indent=2), encoding="utf-8")
        (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"], "checks": report["checks"], "error": report.get("error")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
