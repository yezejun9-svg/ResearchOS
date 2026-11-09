import sys,json,time,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
mode=sys.argv[1]
if mode=="grandchild":
 time.sleep(120)
 raise SystemExit(0)
ready=Path(sys.argv[2])
child=None
if mode in ("cancel","timeout"):
 child=subprocess.Popen([sys.executable,"-I","-S","-B","-X","utf8",str(Path(__file__).resolve()),"grandchild"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
with ready.open("xb") as f:f.write(json.dumps(dict(mode=mode,child_pid=child.pid if child else None,public_dummy=True)).encode("utf-8"))
if mode=="normal":
 time.sleep(0.15)
 print(json.dumps(dict(mode=mode,public_dummy=True)),flush=True)
else:
 time.sleep(120)
