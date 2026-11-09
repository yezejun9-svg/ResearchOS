import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
argv = [sys.executable,"-B","-X","utf8",str(out/"register.py")]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
proc = subprocess.run(argv,cwd=r"D:\作品集\ResearchOS\research-os",capture_output=True)
for name,raw in [("register.stdout.raw",proc.stdout),("register.stderr.raw",proc.stderr)]:
    with (out/name).open("xb") as stream:
        stream.write(raw)
record = {"argv":argv,"cwd":r"D:\作品集\ResearchOS\research-os","started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"actual_exit":proc.returncode,"stdout_sha256":hashlib.sha256(proc.stdout).hexdigest(),"stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()}
with (out/"register.invocation.json").open("xb") as stream:
    stream.write((json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode())
print(proc.stdout.decode("utf8",errors="replace"))
if proc.returncode:
    print(proc.stderr.decode("utf8",errors="replace"))
sys.exit(proc.returncode)
