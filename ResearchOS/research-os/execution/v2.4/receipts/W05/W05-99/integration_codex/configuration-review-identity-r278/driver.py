import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
root = Path(r"D:\作品集\ResearchOS\research-os")
argv = [sys.executable, "-B", "-X", "utf8", str(out / "register.py")]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(argv, cwd=root, capture_output=True)
for n, b in [("register.stdout.raw", p.stdout), ("register.stderr.raw", p.stderr)]:
    with (out / n).open("xb") as f:
        f.write(b)
v = {"argv": argv, "cwd": str(root), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": p.returncode, "stdout_sha256": hashlib.sha256(p.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(p.stderr).hexdigest()}
with (out / "register.invocation.json").open("xb") as f:
    f.write((json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode())
print(p.stdout.decode("utf8", errors="replace"))
print(p.stderr.decode("utf8", errors="replace"))
sys.exit(p.returncode)
