#!/usr/bin/env python3
"""Independent file inventory, tamper, UNBOUND, and fresh fixture checks."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import socket
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ps(script, *args):
    # A launched fixture may keep inherited pipe handles open after PowerShell
    # exits. File-backed output avoids waiting for that unrelated child EOF.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *map(str, args)],
                                stdout=stdout, stderr=stderr, timeout=90)
        stdout.seek(0)
        stderr.seek(0)
        result.stdout = stdout.read().decode("utf-8", errors="replace")
        result.stderr = stderr.read().decode("utf-8", errors="replace")
        return result


def require(condition, name, detail=""):
    if not condition:
        raise AssertionError(name + (": " + detail if detail else ""))
    return name


def run(archive: Path, fixture: bool):
    checks = []
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        checks.append(require(len(names) == len(set(names)), "unique-zip-entries"))
        checks.append(require(names == sorted(names), "sorted-zip-entries"))
        checks.append(require(all(p.parts and not p.is_absolute() and ".." not in p.parts for p in map(PurePosixPath, names)), "no-archive-escape"))
        manifest = json.loads(package.read("release-manifest.json"))
        listed = {entry["path"]: entry for entry in manifest["files"]}
        checks.append(require(set(names) == set(listed) | {"release-manifest.json"}, "exact-allowlist"))
        checks.append(require(all(len(package.read(name)) == listed[name]["size"] and sha(package.read(name)) == listed[name]["sha256"] for name in listed), "every-file-hash"))
        checks.append(require(manifest["database"]["schema13_to_final_plan"] == "NOT_IMPLEMENTED", "final-upgrade-unbound"))
        checks.append(require("release.reproduce" in manifest["commands"]["unbound_not_implemented"], "release-command-unbound"))
        with tempfile.TemporaryDirectory(prefix="researchos-r1-check-") as temporary:
            root = Path(temporary) / "release"
            root.mkdir()
            package.extractall(root)
            verify = root / "scripts/verify.ps1"
            verified = ps(verify, "-ReleaseRoot", root)
            checks.append(require(verified.returncode == 0, "powershell-verify", verified.stderr[-500:]))

            target = root / "bin/backup.exe"
            original = target.read_bytes()
            target.write_bytes(bytes((original[0] ^ 1,)) + original[1:])
            checks.append(require(ps(verify, "-ReleaseRoot", root).returncode != 0, "tamper-rejected"))
            target.write_bytes(original)

            target = root / "spec/v2.0/contracts/openapi.json"
            original = target.read_bytes()
            target.unlink()
            checks.append(require(ps(verify, "-ReleaseRoot", root).returncode != 0, "missing-contract-rejected"))
            target.write_bytes(original)

            extra = root / "unexpected.json"
            extra.write_text("{}", encoding="utf-8")
            checks.append(require(ps(verify, "-ReleaseRoot", root).returncode != 0, "extra-file-rejected"))
            extra.unlink()

            manifest_file = root / "release-manifest.json"
            original = manifest_file.read_bytes()
            altered = json.loads(original)
            altered["files"][0]["path"] = "../outside"
            manifest_file.write_text(json.dumps(altered), encoding="utf-8")
            checks.append(require(ps(verify, "-ReleaseRoot", root).returncode != 0, "path-escape-rejected"))
            manifest_file.write_bytes(original)

            if fixture:
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", 0))
                    port = probe.getsockname()[1]
                if port in (32736, 79136):
                    raise AssertionError("reserved fixture port selected")
                data = Path(temporary) / "data"
                start = root / "scripts/start.ps1"
                stop = root / "scripts/stop.ps1"
                try:
                    result = ps(start, "-DataDir", data, "-Listen", f"127.0.0.1:{port}", "-Fresh")
                    checks.append(require(result.returncode == 0, "fresh-fixture-start", (result.stderr + result.stdout)[-700:]))
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=5) as response:
                        checks.append(require(response.status == 200, "loopback-health"))
                    checks.append(require((data / "researchos.sqlite").is_file(), "external-fresh-db"))
                finally:
                    if (data / "fixture-control.pid").exists():
                        stopped = ps(stop, "-DataDir", data)
                        checks.append(require(stopped.returncode == 0, "fixture-stop"))
                checks.append(require((data / "researchos.sqlite").is_file(), "data-preserved"))
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(root))
            from execution.command_dispatcher.dispatch import execute
            command, _ = execute("release.reproduce", root=root)
            checks.append(require(command["exit_code"] == 3 and command["status"] == "NOT_IMPLEMENTED", "unbound-nonzero"))
    return {"status": "PASS", "scope": "DEVELOPMENT_FIXTURE_ONLY", "assertions": len(checks),
            "assertion_ids": checks, "archive_sha256": sha(archive.read_bytes()), "clean_windows": "NOT_RUN"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--run-fixture", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.archive.resolve(), args.run_fixture), sort_keys=True))
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error), "scope": "DEVELOPMENT_FIXTURE_ONLY"}), file=sys.stderr)
        sys.exit(1)
