import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
h=json.loads((N/"HDF.json").read_bytes());assert pin(Path(h["manifest_ref"]["path"]))==h["manifest_ref"]
m=json.loads((N/"MF.json").read_bytes())
for ref in m["members"]:assert pin(Path(ref["path"]))==ref
refs=json.loads((N/"input-pins.json").read_bytes())
for ref in refs:assert pin(Path(ref["path"]))==ref
value=dict(status="PASS_POSTSEAL",HDF=pin(N/"HDF.json"),MF=pin(N/"MF.json"),member_count=len(m["members"]),input_count=len(refs),pins_unchanged=True,observation_only_no_OS_held_guard=True)
with (N/"postseal.json").open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(dict(postseal=pin(N/"postseal.json")),ensure_ascii=False))

