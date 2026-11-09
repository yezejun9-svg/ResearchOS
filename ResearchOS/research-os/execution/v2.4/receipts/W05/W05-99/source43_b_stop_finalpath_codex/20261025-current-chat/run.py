import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    root = pathlib.Path(__file__).resolve().parent
    ident, cwd, *argv = sys.argv[1:]
    target = root / ident
    if target.exists():
        raise SystemExit(f"receipt exists: {target}")
    target.mkdir(parents=True)
    names = ["TMP", "TEMP", "GOTMPDIR", "GOCACHE", "GOPATH", "GOTOOLCHAIN", "GOPROXY", "GOSUMDB", "GOFLAGS", "PYTHONUTF8", "RESEARCHOS_SOURCE43_ASCII_FIXTURE_ROOT", "RESEARCHOS_OWNED_STOP_FIXTURE_EXE"]
    env = {name: os.environ.get(name) for name in names}
    invocation = {"id": ident, "argv": argv, "cwd": cwd, "env": env, "start_utc": now()}
    (target / "invocation.json").write_text(json.dumps(invocation, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "recipe.json").write_text(json.dumps(invocation, ensure_ascii=False, indent=2), encoding="utf-8")
    with (target / "stdout.raw").open("wb") as out, (target / "stderr.raw").open("wb") as err:
        result = subprocess.run(argv, cwd=cwd, env=os.environ.copy(), stdout=out, stderr=err, check=False)
    (target / "exit.json").write_text(json.dumps({"exit": result.returncode, "end_utc": now()}, indent=2), encoding="utf-8")
    sys.stdout.buffer.write((target / "stdout.raw").read_bytes())
    sys.stderr.buffer.write((target / "stderr.raw").read_bytes())
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
