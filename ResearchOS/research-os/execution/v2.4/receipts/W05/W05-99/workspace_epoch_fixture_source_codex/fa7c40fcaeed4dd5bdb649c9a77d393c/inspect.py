import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c")
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/remaining_full_failure_cause_review_codex/8c83a215358ce0e859da44f08b8a69d3")
F=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/current-composition-full-domain-root-0d2a82e73b754a5f")
def pin(p):
 b=p.read_bytes();return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
manifest=json.loads((C/"manifest.json").read_text(encoding="utf-8"))
for m in manifest["members"].values():
 actual=pin(Path(m["path"]));assert (actual["sha256"],actual["bytes"])==(m["sha256"],m["bytes"])
report=json.loads((C/"report.json").read_text(encoding="utf-8"))
source=json.loads((C/"source-pins.json").read_text(encoding="utf-8"))
cause_hits=[]
source_hits=[]
def walk(v,pointer,target,out):
 if isinstance(v,dict):
  if any(isinstance(x,str) and target in x.replace("\\","/") for x in v.values()):
   out.append({"pointer":pointer,"keys":list(v),"scalars":{k:x for k,x in v.items() if not isinstance(x,(dict,list))}})
  for k,x in v.items():walk(x,pointer+"/"+str(k),target,out)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,pointer+"/"+str(i),target,out)
walk(report,"","WORKSPACE_WRITER_EPOCH",cause_hits)
walk(source,"","client_workspace_test.go",source_hits)
raw=F/"full-domain-and-native-authority-offline.stdout.raw"
assert (pin(raw)["sha256"],pin(raw)["bytes"])==("b4d15819134bd1d16c976828022c76aad741859967bbf0a3617986b0ca0308ae",2661892)
target="TestClientWorkspaceImportExactBytesReplayAndEpoch"
events=[]
for n,line in enumerate(raw.read_text(encoding="utf-8").splitlines(),1):
 evt=json.loads(line)
 if evt.get("Test")==target:events.append({"raw_line":n,"event":evt})
assert sum(v["event"].get("Action")=="fail" for v in events)==1
result={"authority":"NONE","cause_manifest":pin(C/"manifest.json"),"report_ref":pin(C/"report.json"),"source_pins_ref":pin(C/"source-pins.json"),"report_top_keys":list(report),"source_pins_top_keys":list(source),"cause_matches":cause_hits,"source_matches":source_hits,"actual_FULL":pin(raw),"actual_leaf":target,"actual_events":events,"scope_failed_leaf_count":1}
with (Q/"epoch-input-facts.json").open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
