"""Append-only raw command capture for CP516 Source revision."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not argv: parser.error("missing command")
    env = os.environ.copy()
    allowed = {}
    for item in args.env:
        key, value = item.split("=", 1)
        env[key] = value
        allowed[key] = value
    root = Path(__file__).resolve().parent / "command-captures"
    root.mkdir(parents=True, exist_ok=True)
    capture = root / (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + args.label + "-" + uuid.uuid4().hex[:8])
    capture.mkdir()
    meta = {"argv": argv, "cwd": str(Path(args.cwd).resolve()), "allowlist_env": allowed,
            "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (capture / "before.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        result = subprocess.run(argv, cwd=args.cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except OSError as exc:
        code, stdout, stderr = 127, b"", repr(exc).encode("utf-8")
    (capture / "stdout.bin").write_bytes(stdout)
    (capture / "stderr.bin").write_bytes(stderr)
    (capture / "after.json").write_text(json.dumps({"native_exit": code,
            "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stdout_bytes": len(stdout), "stderr_bytes": len(stderr)}, indent=2), encoding="utf-8")
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    return code

if __name__ == "__main__": raise SystemExit(main())
