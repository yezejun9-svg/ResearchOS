import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
state = ROOT / "execution/v2.4/step_state.json"
tool = ROOT / ".local/worktrees/v24-continuation/spec/v2.4/tools/task_packet.py"
before = hashlib.sha256(state.read_bytes()).hexdigest()
argv = [sys.executable, "-B", "-X", "utf8", str(tool), "show", "W05-99", "--state", str(state)]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
for name, raw in [("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)]:
    with (OUT / name).open("xb") as stream:
        stream.write(raw)
record = {"argv": argv, "cwd": str(ROOT), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode, "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(), "tool_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(), "state_before_sha256": before, "state_after_sha256": hashlib.sha256(state.read_bytes()).hexdigest(), "read_only": True, "formal_increment": 0}
with (OUT / "invocation.json").open("xb") as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode())
assert record["state_before_sha256"] == record["state_after_sha256"]
print(json.dumps(record, ensure_ascii=False))
sys.exit(proc.returncode)
