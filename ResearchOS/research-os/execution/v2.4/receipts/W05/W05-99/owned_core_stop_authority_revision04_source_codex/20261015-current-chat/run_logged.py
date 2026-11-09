"""Record a command before execution and preserve its unmodified process result."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent / "command-captures"

def emit(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
    if not argv:
        raise SystemExit("missing command")
    selected = {}
    environment = os.environ.copy()
    for item in args.env:
        name, sep, value = item.partition("=")
        if not sep or not name:
            raise SystemExit("bad --env")
        environment[name] = value
        selected[name] = value
    started = dt.datetime.now(dt.timezone.utc)
    slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in args.label)
    out = ROOT / (started.strftime("%Y%m%dT%H%M%S.%fZ-") + slug + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    emit(out / "before.json", {"argv": argv, "cwd": str(Path(args.cwd).resolve()), "allowlist_env": selected, "started_utc": started.isoformat()})
    proc = subprocess.run(argv, cwd=args.cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out / "stdout.bin").write_bytes(proc.stdout)
    (out / "stderr.bin").write_bytes(proc.stderr)
    emit(out / "after.json", {"native_exit": proc.returncode, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
    sys.stdout.buffer.write(proc.stdout)
    sys.stderr.buffer.write(proc.stderr)
    return proc.returncode

if __name__ == "__main__":
    raise SystemExit(main())
