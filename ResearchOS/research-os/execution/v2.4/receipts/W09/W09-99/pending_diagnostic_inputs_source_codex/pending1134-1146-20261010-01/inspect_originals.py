import json,hashlib,os
from pathlib import Path
N=Path(__file__).resolve().parent
B=Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts")
D={
 "caller":B/"W05/W05-99/schema21_public_root_caller_source_codex/s21public-caller-20261010-01",
 "resource":B/"W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01",
 "root":B/"W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009",
 "nf4":B/"W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-04",
 "register":B/"W09/W09-99/w09_nf4_root_registration_source_codex/register-20261010-01",
 "review":B/"W05/W05-99/schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-01",
 "bridge_review":B/"W09/W09-99/w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-02",
 "bridge":B/"W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-03"}
SPEC=[
 (1134,"caller","failure-origin.1134.json",""),
 (1135,"resource","HDF.json","original_diagnostic"),
 (1136,"root","original1136.actual-host.binding.json",""),
 (1137,"nf4","original-1137.origin.json",""),
 (1138,"caller","failure-origin.1138.json",""),
 (1139,"nf4","original-1139.origin.json",""),
 (1140,"register","original-1140.origin.json",""),
 (1141,"register","original-1141.origin.json",""),
 (1142,"root","original1142.actual-host.binding.json",""),
 (1143,"review","HDF.json","original1143"),
 (1144,"bridge_review","original1144.failure-origin.json",""),
 (1145,"bridge","original-1145.origin.json",""),
 (1146,"root","w09.public21-root-helper-original1146.actual-audit.root.json","")]
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=Path(p).read_bytes()
 return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def checked(ref):
 p=Path(ref["path"]);b=p.read_bytes()
 assert sha(b)==ref["sha256"] and len(b)==ref["bytes"],str(p)
 return b
def first(obj,names):
 for k in names:
  if k in obj:return obj[k]
 return None
rows=[]
for ordinal,key,name,selector in SPEC:
 op=D[key]/name;ref=pin(op);full=json.loads(checked(ref));o=full[selector] if selector else full
 br=first(o,["actual_host_binding_ref","binding_ref"])
 if br is None:
  if ordinal in (1137,1139,1140,1141):br=pin(D[key]/("original-"+str(ordinal)+".binding.json"))
  else:br=ref
 binding=json.loads(checked(br))
 rr=first(o,["raw_ref","actual_raw_ref","original_capture_ref","original_raw_ref"])
 if rr is None:rr=first(binding,["original_capture_ref","original_raw_ref"])
 raw=checked(rr);lines=raw.splitlines(keepends=True)
 assert len(lines)==3,(ordinal,len(lines))
 events=[json.loads(x) for x in lines];payloads=[x["payload"] for x in events]
 host=o if "source_audit_path" in o else binding
 hashes=first(host,["original_line_sha256","source_line_sha256"])
 assert [sha(x) for x in lines]==hashes,ordinal
 offsets=host["source_line_offsets"]
 with Path(host["source_audit_path"]).open("rb") as f:
  for offset,line in zip(offsets,lines):
   f.seek(offset);assert f.read(len(line))==line,ordinal
 assert payloads[1]["call_id"]==payloads[2]["call_id"],ordinal
 output=payloads[2].get("output")
 rows.append({"ordinal":ordinal,"origin_ref":ref,"origin_selector":{"json_pointer":"/"+selector if selector else ""},
  "capture_binding_ref":br,"raw_ref":rr,"origin_value":o,
  "host_binding_verified":True,"actual_call_id":payloads[1]["call_id"],
  "actual_actor":payloads[0].get("agent_path"),"actual_thread":payloads[0].get("id"),
  "call_payload":payloads[1],"output_payload":payloads[2]})
 print(json.dumps({"ordinal":ordinal,"output":output},ensure_ascii=False))
p=N/"verified-original-observations.json"
with p.open("xb") as f:f.write((json.dumps({"rows":rows},ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
print(json.dumps({"observations_ref":pin(p),"verified_rows":len(rows)},ensure_ascii=False))

