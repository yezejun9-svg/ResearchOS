import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
request = json.load(sys.stdin)
base = Path(__file__).resolve().parent
label = request["label"]
if not label or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in label):
    raise SystemExit("invalid label")
cwd = str(Path.cwd())
env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH", "PATHEXT", "COMSPEC") if k in os.environ}
env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
argv = [sys.executable, "-X", "utf8", "-c", request["script"]]
recipe = {"schema": "researchos.readonly-semantic-command.v1", "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "cwd": cwd, "argv": argv, "environment_exact": env, "mode": "READONLY_SOURCE_ANALYSIS_OWN_RECEIPTS_ONLY"}
with (base / (label + ".recipe.json")).open("x", encoding="utf8") as f:
    json.dump(recipe, f, ensure_ascii=False, indent=2)
    f.write("\n")
result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True)
refs = []
for suffix, data in (("stdout.raw", result.stdout), ("stderr.raw", result.stderr)):
    p = base / (label + "." + suffix)
    p.open("xb").write(data)
    refs.append({"path": p.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
with (base / (label + ".result.json")).open("x", encoding="utf8") as f:
    json.dump({"ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "native_exit": result.returncode, "raw": refs}, f, indent=2)
    f.write("\n")
print(result.stdout.decode("utf8", errors="backslashreplace"))
if result.stderr:
    print("STDERR:")
    print(result.stderr.decode("utf8", errors="backslashreplace"))
print("native_exit=" + str(result.returncode))
sys.exit(result.returncode)
