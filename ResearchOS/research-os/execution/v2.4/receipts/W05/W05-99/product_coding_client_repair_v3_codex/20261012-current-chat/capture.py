"""Capture a bounded fixture command without replacing existing evidence."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

name, cwd, *argv = sys.argv[1:]
folder = pathlib.Path(__file__).resolve().parent / "raw"
folder.mkdir(exist_ok=True)
for suffix in ("stdout", "stderr", "invocation.json"):
    if (folder / f"{name}.{suffix}").exists():
        raise SystemExit(f"receipt already exists: {name}.{suffix}")

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(argv, cwd=cwd, env=os.environ.copy(), capture_output=True, timeout=120)
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
    with (folder / f"{name}.{suffix}").open("xb") as stream:
        stream.write(data)
record = {
    "argv": argv,
    "cwd": cwd,
    "started_at": started,
    "ended_at": ended,
    "exit": result.returncode,
    "stdout": f"raw/{name}.stdout",
    "stderr": f"raw/{name}.stderr",
    "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
    "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
    "selected_environment": {key: os.environ[key] for key in (
        "RESEARCHOS_SHARED_ROOT", "RESEARCHOS_UI_SOURCE", "ROS_STATUS_RECOVERY",
        "ROS_REFRESH_FAIL_ONCE", "RESEARCHOS_DESKTOP_VALIDATOR_ROOT",
    ) if key in os.environ},
}
with (folder / f"{name}.invocation.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"name": name, "exit": result.returncode,
                  "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr)}))
raise SystemExit(result.returncode)
