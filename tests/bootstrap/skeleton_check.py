#!/usr/bin/env python3
"""Live W02 startup probe. Development evidence only."""
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / ".local" / "bin" / ("researchos-control.exe" if os.name == "nt" else "researchos-control")
IDS = ["W02-STARTUP-HTTP", "W02-STARTUP-DB", "W03-STARTUP-AUTH-REQUIRED"]


def main():
    if not BIN.is_file():
        raise RuntimeError(f"missing built control binary: {BIN}")
    with tempfile.TemporaryDirectory() as temp:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        env = os.environ.copy()
        env.update(RESEARCHOS_DATA_DIR=temp, RESEARCHOS_LISTEN=f"127.0.0.1:{port}",
                   RESEARCHOS_WEB_DIR=str(ROOT / "apps" / "web" / "dist"))
        process = subprocess.Popen([str(BIN)], cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, text=True)
        try:
            base = f"http://127.0.0.1:{port}"
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"server exited {process.returncode}: {process.stderr.read()}")
                try:
                    with urlopen(base + "/healthz", timeout=1) as response:
                        health = json.load(response)
                        assert response.status == 200 and health == {
                            "status": "ready", "scope": "DEVELOPMENT_ONLY", "database": "sqlite"}
                    break
                except (URLError, TimeoutError):
                    if time.monotonic() > deadline:
                        raise RuntimeError("healthz did not become ready")
                    time.sleep(.1)
            with urlopen(base + "/", timeout=2) as response:
                html = response.read().decode("utf-8")
                assert response.status == 200 and "ResearchOS" in html and "/assets/" in html
            asset = re.search(r'(?:(?:src|href)="(/assets/[^"]+)")', html)
            assert asset, "built asset URL missing"
            with urlopen(base + asset.group(1), timeout=2) as response:
                assert response.status == 200 and len(response.read()) > 0
            db_path = Path(temp) / "researchos.sqlite"
            with closing(sqlite3.connect(db_path)) as db:
                assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
                assert db.execute("PRAGMA synchronous").fetchone()[0] == 2
                expected = sorted((int(path.name.split('_', 1)[0]),)
                                  for path in (ROOT / 'migrations/sqlite').glob('*.sql'))
                assert db.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall() == expected
            try:
                urlopen(base + "/v1/projects", timeout=2)
                raise AssertionError("unauthenticated business endpoint succeeded")
            except HTTPError as exc:
                if exc.code != 401:
                    raise
                assert json.load(exc)["code"] == "UNAUTHENTICATED"
        finally:
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()


if __name__ == "__main__":
    try:
        main()
        result = {"status": "PASS", "assertions": len(IDS), "assertion_ids": IDS,
                  "scope": "DEVELOPMENT_ONLY"}
    except Exception as exc:
        result = {"status": "FAIL", "assertions": 1,
                  "assertion_ids": ["W02-STARTUP-FAILED"], "scope": "DEVELOPMENT_ONLY",
                  "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["status"] == "PASS" else 1)
