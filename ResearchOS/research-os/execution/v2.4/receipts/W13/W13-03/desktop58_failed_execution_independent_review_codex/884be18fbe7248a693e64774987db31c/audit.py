import json,hashlib,os,stat,ast,difflib
from pathlib import Path
from collections import Counter
R=Path("D:/作品集/ResearchOS/research-os")
O=Path(__file__).parent
N=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1"
checks=[]; reads={}
def ck(name,ok,detail=None):checks.append({"name":name,"pass":bool(ok),"detail":detail})
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def raw(p):
 p=path(p)
 for a in (p,*p.parents):
  if a==R or a.is_relative_to(R):
   st=a.lstat()
   if stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&1024:raise ValueError("reparse read forbidden "+str(a))
 b=p.read_bytes();reads[str(p)]={"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};return b
def pin(p):
 raw(p);return reads[str(path(p))]
def vr(r):
 b=raw(r["path"]);ck("pin:"+r["path"],len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]);return b
def doc(p):return json.loads(raw(p))
def jd(r):return json.loads(vr(r))
def put(n,d):
 with (O/n).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
m=doc(N/"manifest.json");r=doc(N/"report.json");h=doc(N/"handoff.json")
for x in m["entries"]:vr(x)
ck("root manifest immutable",m.get("mutable_after_seal") is False)
ck("manifest member paths unique",len({str(path(x["path"])) for x in m["entries"]})==len(m["entries"]))
closed=r["all_closed_original_refs"]
ck("closed files count",len(closed)==108)
for x in closed:vr(x)
t=jd(r["failed_export_tree_ref"]);ck("export files count",len(t["files"])==5960)
for x in t["files"]:vr(x)
eroot=path(t["root"]);actual=[];wit=[];stack=[eroot]
while stack:
 d=stack.pop()
 with os.scandir(d) as it:entries=sorted(it,key=lambda e:e.name)
 for e in entries:
  p=Path(e.path);s=e.stat(follow_symlinks=False)
  if stat.S_ISLNK(s.st_mode) or getattr(s,"st_file_attributes",0)&1024:
   wit.append({"path":p.relative_to(R).as_posix(),"file_attributes":getattr(s,"st_file_attributes",None),"reparse_tag":getattr(s,"st_reparse_tag",None),"readlink_text":os.readlink(p),"followed":False,"qualification":False})
  elif stat.S_ISDIR(s.st_mode):stack.append(p)
  elif stat.S_ISREG(s.st_mode):actual.append(p.relative_to(R).as_posix())
  else:ck("no unusual file:"+str(p),False)
ck("export complete nofollow membership",sorted(actual)==sorted(x["path"] for x in t["files"]))
ck("export reparse witness exact",wit==t["reparse_witnesses_not_followed"],wit)
ck("export diagnostic only",t["qualification"] is False and t["posthoc_resource_union"] is False)
pv=doc(N/"original-tool-payload.v2.json")
s=jd(r["scope_ref"]);b=jd(r["binding_ref"]);g=jd(r["grant_ref"])
ck("grant scope exact dictionary",g["scope_ref"]==r["scope_ref"])
ck("grant actual authority",g["actor"]=="codex:/root" and g["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED" and g["actual_registration_completed"] is True)
for k in ("grant_closed_io_ref","registration_closed_io_ref","caller_source_ref","caller_source_review_ref"):vr(pv[k])
for x in r["canonical_refs_unchanged"]:vr(x)
copies=g["canonical_copies"];copyrows=list(copies.values()) if isinstance(copies,dict) else copies
ck("four grant copies",len(copyrows)==4)
ck("live canonical bytes match grant copies",[(x["sha256"],x["bytes"]) for x in r["canonical_refs_unchanged"]]==[(x["sha256"],x["bytes"]) for x in copyrows])
for x in copyrows:vr(x)
for k in ("registration_refs","authority_review_refs","runtime_observation_refs"):
 rows=g[k];rows=list(rows.values()) if isinstance(rows,dict) else rows
 for x in rows:
  if isinstance(x,dict) and {"path","sha256","bytes"}<=set(x):vr(x)
ck("canonical tuple",r["canonical_tuple"]==[337,165,617])
ck("snapshot failures",r["registered_failure_count"]==617 and r["observed_failure_count"]==635 and r["pending_count"]==18)
ps=r["pending_failure_origin_records"]
ck("unique pending indices", [x["failure_index"] for x in ps]==list(range(618,636)))
for x in ps:jd(x["origin_ref"])
E=Path(s["output_root"]);L=Path(s["outer_output_root"]);C=R/pv["caller_out_rel"]
er=jd(pv["executor_result_ref"]);bi=jd(pv["builder_invocation_ref"]);lr=doc(L/"result.json");ci=doc(C/"root-launch.invocation.json")
br=bi["result"];dc=br["debug_capture"];jc=br["job_cleanup"]
ck("builder original matches last child",br==er["last_child_result"])
ck("first cause preserved",er["first_error"]==r["executor_first_error"] and er["first_error"].get("actual_native_exit") is None)
ck("requested termination code",br["actual_exit"]==3758097160==jc["termination_code_requested"] and jc["termination_requested"] and jc["termination_succeeded"])
ck("not timeout",br["timed_out"] is False)
ck("cleanup actually idle and all handles closed",jc["job_idle_confirmed"] and jc["primary_exit_confirmed"] and jc["active_processes_last_observed"]==0 and jc["handles_closed"] and jc["explicit_owned_handle_close_successes"]==8942 and jc["explicit_owned_handles_remaining"]==0)
ck("capture incomplete error retained",dc["complete"] is False and jc["errors"]==["RuntimeError: Evidence finalization incomplete after earlier failure; no success"])
ck("805 lifecycle counts",dc["create_process_count"]==805 and dc["exit_process_count"]==805)
rf=dc["rejected_load_facts"]
ck("one diagnostic rejected module",len(rf)==1 and rf[0]["expected_pin"] is None and rf[0]["qualified_module"] is False and rf[0]["diagnostic_only"] is True)
ck("rejected actual conhost exact",rf[0]["before"]=={"sha256":"e449bce01f275cd08f3d4e64bb73b3b43ae845a0dbdb3e6131426e66537705e5","bytes":1003520} and rf[0]["pid"]==85216 and rf[0]["creation_time_100ns"]==134359151391343478 and rf[0]["process_generation"]==805)
states=er["all_case_states"];vals=list(states.values()) if isinstance(states,dict) else states
counts=Counter(x.get("state",x.get("status")) if isinstance(x,dict) else x for x in vals)
ck("170 cases genuinely not started",len(vals)==170 and counts=={"NOT_STARTED":170} and er["rows"]==[])
ck("HTTP0 top native3",er["actual_observed_HTTP_total"]==0 and er["actual_native_top_commands"]==3)
ck("caller actual exit preserves NULL outer",ci["actual_launcher_native_exit"]==1 and ci["actual_outer_tool_exit"] is None and ci["caller_error"] is None and ci["secondary"]==[] and ci["caller_OS_lifecycle_qualification"] is False)
ck("launcher propagation and NULL",lr["actual_native_inner_exit"]==1 and lr["actual_outer_native_exit"] is None)
ck("launcher job closed",lr["inner_result"]["job_cleanup"]["job_idle_confirmed"] and lr["inner_result"]["job_cleanup"]["handles_closed"] and lr["inner_result"]["job_cleanup"]["errors"]==[])
rr=pv["root_originals"];ck("initial plus three poll originals",len(rr)==4 and rr[0]["full_tool_result"]["session_id"]==25309 and all(x["input"].get("session_id")==25309 for x in rr[1:]))
ck("terminal explicit native bridge",rr[-1]["full_tool_result"]["exit_code"]==1 and "ACTUAL_PYTHON_EXIT=1" in rr[-1]["full_tool_result"]["output"])
ck("Root launch scope/grant/source pins in original command",all(v in rr[0]["input"]["cmd"] for v in [r["scope_ref"]["sha256"],r["grant_ref"]["sha256"],pv["caller_source_ref"]["sha256"]]))
for name in ("git-head","export-blobs","build-current58"):
 inv=doc(E/(name+".invocation.json"))
 ck(name+" saved invocation present", isinstance(inv,dict))
# Inspect large structures by shape, retain without lossy numeric translation.
shapes={"debug":{k:{"type":type(v).__name__,"len":len(v) if isinstance(v,(dict,list)) else None} for k,v in dc.items()},"invocation_keys":list(bi),"grant_registration":g["registration_refs"],"root_members":len(m["entries"])}
vec={}
for f in sorted(E.glob("*.vector.json")):
 v=doc(f);vec[f.name]={"type":type(v).__name__,"keys":list(v) if isinstance(v,dict) else None,"len":len(v),"first":(v[0] if isinstance(v,list) and v else None)}
# Sealer correction: preserve strict file guard and all original functions except new diagnostic walker.
v1=raw(N/"seal_failed_execution_metadata.sixth.py").decode();v2=raw(N/"seal_failed_execution_metadata.sixth.v2.py").decode()
a1=ast.parse(v1);a2=ast.parse(v2)
defs1={x.name:ast.dump(x,include_attributes=False) for x in a1.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
defs2={x.name:ast.dump(x,include_attributes=False) for x in a2.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
ck("all old sealer helpers AST unchanged",all(defs2.get(k)==v for k,v in defs1.items()))
ck("v2 walker nofollow", "entry.stat(follow_symlinks=False)" in v2 and 'files.append(ref(q))' in v2)
ann=pin(N/"tool-observations.failed-closure.closed.original.json");ck("annex exact expected",ann["sha256"]=="a0f2ea85823046e05d7ddb78fa6c4ab9730661cd04668638374f5c375dd0497b" and ann["bytes"]==9454)
put("sealer.diff.txt.json",list(difflib.unified_diff(v1.splitlines(),v2.splitlines())))
put("audit.json",{"checks":checks,"passed":sum(x["pass"] for x in checks),"failed":[x for x in checks if not x["pass"]],"shapes":shapes,"vectors":vec,"reads":list(reads.values()),"case_counts":dict(counts),"candidate_executed":False,"new_native_calls":0})
print(json.dumps({"checks":len(checks),"failed":[x for x in checks if not x["pass"]],"debug_shape":shapes["debug"],"vectors":vec},ensure_ascii=False))

