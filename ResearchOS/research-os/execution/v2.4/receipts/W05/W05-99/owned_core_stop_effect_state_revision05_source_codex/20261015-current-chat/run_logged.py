"""Capture exact argv/cwd/env before a command and raw results afterward."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--label", required=True)
parser.add_argument("--cwd", required=True)
parser.add_argument("--env", action="append", default=[])
parser.add_argument("argv", nargs=argparse.REMAINDER)
args = parser.parse_args()
argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
if not argv:
    parser.error("command required")
env = os.environ.copy()
provided = {}
for item in args.env:
    key, separator, value = item.partition("=")
    if not separator or not key:
        parser.error("--env must be KEY=VALUE")
    provided[key] = value
    env[key] = value
root = Path(__file__).resolve().parent / "command-captures"
root.mkdir(parents=True, exist_ok=True)
now = dt.datetime.now(dt.timezone.utc)
folder = root / (now.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + args.label + "-" + uuid.uuid4().hex[:8])
folder.mkdir()
before = {"argv": argv, "cwd": str(Path(args.cwd).resolve()), "allowlist_env": provided, "started_utc": now.isoformat()}
with (folder / "before.json").open("x", encoding="utf-8") as f:
    json.dump(before, f, ensure_ascii=False, indent=2)
    f.write("\n")
    f.flush()
    os.fsync(f.fileno())
try:
    completed = subprocess.run(argv, cwd=args.cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
except Exception as exc:
    code, stdout, stderr = 127, b"", repr(exc).encode("utf-8", "replace")
(folder / "stdout.bin").write_bytes(stdout)
(folder / "stderr.bin").write_bytes(stderr)
after = {"native_exit": code, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(stderr).hexdigest()}
with (folder / "after.json").open("x", encoding="utf-8") as f:
    json.dump(after, f, ensure_ascii=False, indent=2)
    f.write("\n")
    f.flush()
    os.fsync(f.fileno())
sys.stdout.buffer.write(stdout)
sys.stderr.buffer.write(stderr)
sys.exit(code)
