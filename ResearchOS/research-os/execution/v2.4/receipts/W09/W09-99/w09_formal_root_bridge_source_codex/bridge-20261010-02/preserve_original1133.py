import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
audit=Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
 b=Path(p).read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def put(name,obj,raw=False):
 p=N/name
 with p.open("xb") as f:f.write(obj if raw else (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
with audit.open("rb") as f:
 prefix=os.fstat(f.fileno()).st_size;header=f.readline();hd=json.loads(header)
 assert hd["payload"]["agent_path"]=="/root/attach_restore_independent_review"
 calls={};found=None
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  rec=json.loads(line);p=rec.get("payload",{})
  if not isinstance(p,dict):continue
  kind,cid=p.get("type"),p.get("call_id")
  if kind in ("custom_tool_call","function_call"):calls[cid]=(off,line,rec)
  elif kind in ("custom_tool_call_output","function_call_output") and b"672df4" in line and cid in calls:
   found=(calls[cid],off,line,rec);break
 assert found is not None,"MISSING_672DF4"
 call,off,line,rec=found;co,cl,cr=call
 rawref=put("original-1133.raw.jsonl",header+cl+line,True)
 binding={"schema":"researchos.Source-author-actual-tool-binding.v1","Source_author":"codex:/root/attach_restore_independent_review",
  "actual_agent_path":"/root/attach_restore_independent_review","actual_thread":hd["payload"]["id"],
  "actual_parent_thread":hd["payload"]["parent_thread_id"],"source_audit_path":str(audit),
  "source_prefix_bytes":prefix,"source_line_offsets":[0,co,off],"source_line_bytes":[len(header),len(cl),len(line)],
  "source_line_sha256":[sha(header),sha(cl),sha(line)],"original_capture_ref":rawref,
  "actual_call_id":cr["payload"]["call_id"],"Root_issuer":False,"execution_grant":False,"formal_acceptance":False}
 bindref=put("original-1133.binding.json",binding)
 ioref=put("original-1133.complete-IO.json",{"original_call":cr,"original_output":rec,
     "actual_outer_exit":1,"actual_Python_exit":None,"actual_Native_exit":None,"actual_dispatcher_exit":None,
     "component_exit_not_separately_observed":None,"successful_directory_listing_prefix_preserved":True})
 origin=put("original-1133.origin.json",{"schema":"researchos.original-source-failure-origin.v1",
    "original_ordinal":1133,"original_chunk_id":"672df4","actual_outer_exit":1,"actual_python_exit":None,
    "actual_native_exit":None,"actual_dispatcher_exit":None,"actual_model_exit":None,
    "component_exit_not_separately_observed":None,"counter_reset":False,"raw_ref":rawref,
    "actual_host_binding_ref":bindref,"complete_IO_ref":ioref,"successful_prefix_preserved":True})
print(json.dumps({"origin_ref":origin,"raw_ref":rawref,"binding_ref":bindref,"complete_IO_ref":ioref},ensure_ascii=False))

