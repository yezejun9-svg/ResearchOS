"""Run one predeclared local command with immutable raw stdout/stderr capture."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_logged.py recipe.json")
    recipe_path = Path(sys.argv[1]).resolve()
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    root = recipe_path.parent
    tag = recipe["tag"]
    if not tag or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in tag):
        raise SystemExit("invalid tag")
    paths = {suffix: root / f"{tag}.{suffix}" for suffix in ("command.json", "stdout.raw", "stderr.raw", "result.json")}
    if any(path.exists() for path in paths.values()):
        raise SystemExit("capture path exists; never overwrite an attempt")
    argv = recipe["argv"]
    cwd = str(Path(recipe["cwd"]).resolve())
    overrides = recipe.get("env_allowlist", {})
    env = os.environ.copy()
    env.update(overrides)
    command = {
        "schema": "researchos.command-capture.v1",
        "at_utc_before_execution": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recipe": recipe_path.name,
        "recipe_sha256": hashlib.sha256(recipe_path.read_bytes()).hexdigest(),
        "argv": argv,
        "cwd": cwd,
        "env_allowlist": overrides,
        "inherited_environment": "not_exhaustively_captured",
        "stdout": paths["stdout.raw"].name,
        "stderr": paths["stderr.raw"].name,
    }
    paths["command.json"].write_text(json.dumps(command, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if "GOTMPDIR" in overrides:
        Path(overrides["GOTMPDIR"]).mkdir(parents=True, exist_ok=True)
    try:
        with paths["stdout.raw"].open("xb") as out, paths["stderr.raw"].open("xb") as err:
            exit_code = subprocess.run(argv, cwd=cwd, env=env, stdout=out, stderr=err, check=False).returncode
    except Exception as exc:
        exit_code = None
        with paths["stderr.raw"].open("ab") as err:
            err.write(f"runner exception: {type(exc).__name__}: {exc}\n".encode("utf-8"))
    result = {
        "schema": "researchos.command-capture-result.v1",
        "at_utc_after_execution": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "native_exit": exit_code,
        "stdout_sha256": hashlib.sha256(paths["stdout.raw"].read_bytes()).hexdigest(),
        "stdout_bytes": paths["stdout.raw"].stat().st_size,
        "stderr_sha256": hashlib.sha256(paths["stderr.raw"].read_bytes()).hexdigest(),
        "stderr_bytes": paths["stderr.raw"].stat().st_size,
    }
    paths["result.json"].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tag": tag, **result}, ensure_ascii=False))
    if recipe.get("show_stdout", False):
        sys.stdout.buffer.write(paths["stdout.raw"].read_bytes())
        sys.stdout.flush()
    if recipe.get("show_stderr", False):
        sys.stderr.buffer.write(paths["stderr.raw"].read_bytes())
        sys.stderr.flush()
    return exit_code if isinstance(exit_code, int) else 127


if __name__ == "__main__":
    sys.exit(main())
