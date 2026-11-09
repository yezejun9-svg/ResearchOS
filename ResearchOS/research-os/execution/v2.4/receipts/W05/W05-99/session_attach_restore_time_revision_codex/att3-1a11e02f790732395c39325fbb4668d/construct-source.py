"""Construct immutable ATT3 Source only. No Go/native/SQL/model execution."""
import json,hashlib,difflib
from pathlib import Path
P=Path(__file__).resolve().parent
old=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/session_attach_restore_revision_codex/1a11e02f790732395c39325fbb4668d")
review=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/session_attach_restore_independent_review_codex/attach_restore_independent_review")
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(n,b):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b)
def out(n,v):new(n,(json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
pins=[(old/"HDF.json","3c42827e70828e299f5af16205a61de32e83ecb12ef76ad81949fcd38a0f450f",6485),(old/"MF.json","fa0be08e74c96a820048101646a1fcbf6b0d3f2f984ef28953fee8434e388c26",4811),(review/"HDF.json","d3a211c8e4df71abc55c604ecf05e1f670f0f9e065e520277934843dd080a877",4570),(review/"MF.json","2789162e47ddc0db851446f65b6d62f811c9541460f0fa787ff81d103ccbbeb5",4229)]
for p,h,n in pins:
 actual=ref(p);assert actual["sha256"]==h and actual["bytes"]==n
for d in (old,review):
 members=json.loads((d/"MF.json").read_bytes())["members"]
 if isinstance(members,dict):members=members.values()
 for pin in members:
  actual=ref(Path(pin["path"]));assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
payload=json.loads((P/"source-input.json").read_bytes())
base=old/"candidate-root/internal/domain/client_protocol.go"
before=base.read_bytes().decode()
assert ref(base)["sha256"]=="95953bdfa360aee012263c128f3f6a9dc969fc6fe58a0eb7efa05d732e99f08e"
start=before.index("// clientAttachRestoreState reads durable restore evidence")
end=before.index("// journal appends one typed event",start)
previous=before[start:end]
after=before[:start]+payload["helper"]+before[end:]
assert (after[:start]+previous+after[start+len(payload["helper"]):]).encode()==base.read_bytes()
new("candidate-root/internal/domain/client_protocol.go",after.encode())
for name in ("client_protocol_attach_contract_windows_test.go","client_protocol_attach_restore_windows_test.go"):
 new("candidate-root/internal/domain/"+name,(old/"candidate-root/internal/domain"/name).read_bytes())
new("candidate-root/internal/domain/client_protocol_attach_restore_time_windows_test.go",payload["tests"].encode())
out("production-replacements.json",[{"position":start,"before":previous,"after":payload["helper"]}])
new("restore-time.patch","".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(base),tofile="candidate-root/internal/domain/client_protocol.go")).encode())
inputs=[ref(p) for p,h,n in pins]+[ref(base)]
inputs.extend(ref(old/"candidate-root/internal/domain"/name) for name in ("client_protocol_attach_contract_windows_test.go","client_protocol_attach_restore_windows_test.go"))
inputs.extend(ref(review/n) for n in ("report.md","timestamp-counterexample.json","findings.json"))
# Prior direct public production pins remain frozen; Root canonical progress is excluded.
prior=json.loads((old/"public-input-pins.json").read_bytes())["inputs"]
for pin in prior:
 actual=ref(Path(pin["path"]));assert actual==pin
 if pin not in inputs:inputs.append(pin)
out("public-input-pins.json",{"inputs":inputs})
out("static-evidence.json",{"base_ref":ref(base),"candidate_ref":ref(P/"candidate-root/internal/domain/client_protocol.go"),"exact_inverse_bytes":True,"old_two_test_files_byte_equal":True,"source_only":True,"Go_SQL_native_model_executed":False})
print(json.dumps({"root":str(P),"candidate":ref(P/"candidate-root/internal/domain/client_protocol.go"),"inputs":len(inputs),"inverse":True},ensure_ascii=True))

