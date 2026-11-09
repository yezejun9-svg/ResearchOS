import sys
sys.dont_write_bytecode=True
import ast,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 raw=Path(p).read_bytes();return dict(path=str(Path(p).resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
ast.parse((O/"prepare_one_spec.actual.py").read_text(encoding="utf-8"))
authority=json.loads((O/"precise_launch_authority.source.json").read_bytes())
for v in (authority["checkpoint_ref"],authority["config_ref"]):
 actual=pin(v["path"]);assert actual["sha256"]==v["sha256"].removeprefix("sha256:") and actual["bytes"]==v["bytes"]
for p in authority["Root_outputs"]:assert Path(p).is_dir() and not list(Path(p).iterdir())
mf=save("MF.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
hd=save("HDF.json",dict(status="ROOT_ONE_SPEC_SOURCE_AND_PRECISE_LAUNCH_INTENT_PENDING_PRELAUNCH_REVIEW",manifest_ref=mf,spec_source_ref=pin(O/"prepare_one_spec.actual.py"),precise_launch_authority_ref=pin(O/"precise_launch_authority.source.json"),Native_not_launched=True,formal_acceptance=False))
print(json.dumps(dict(handoff_ref=hd,manifest_ref=mf)))

