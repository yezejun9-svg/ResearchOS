import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931")
I=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_io_codex/814-b6832e-76618678c33e47ffb4e2ad9bd5e9c208")
def pin(p):
    b=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
mf=json.loads((Q/"MF.json").read_text(encoding="utf-8"))
members=mf.get("members",[])
assert members, "MF members missing"
checked=0
for m in members:
    p=Path(m["path"])
    actual=pin(p)
    assert actual["sha256"]==m["sha256"] and actual["bytes"]==m["bytes"],p
    checked+=1
refs={name:pin(Q/name) for name in ["MF.json","HDF.json","report.md","source-refs.json","static-checks.json","scope-map.json","tool-io.json","seal-tool-io.json"]}
extra={name:pin(I/name) for name in ["failure-origin.814.json","sealing-io.json","fingerprint.py"]}
result={"authority":"NONE","formal_acceptance":False,"source_namespace":Q.as_posix(),"postseal_io_namespace":I.as_posix(),"MF_members_rechecked":checked,"MF_member_drift":0,"source_refs":refs,"IO_refs":extra,"failure_ordinal":814,"failure_not_reset":True,"source_modified_by_this_check":False}
with (I/"fingerprints.json").open("x",encoding="utf-8",newline="\n") as f:
    f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
