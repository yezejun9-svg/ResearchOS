import json,hashlib,os,re,ast
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts"
FULL=B/"W05/W05-99/schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-02"
S=B/"W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
CORE=B/"W09/W09-99/w09_nf4_root_registration_source_codex/register-20261010-01/adoption_core.source.py"
facts={}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 p=Path(p);b=p.read_bytes()
 return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def exact(ref):
 p=Path(ref["path"]);b=p.read_bytes()
 assert sha(b)==ref["sha256"] and len(b)==ref["bytes"],ref
 facts[str(p)]=ref
 return b
def read(p):return json.loads(exact(pin(p)))
def put(name,obj):
 p=N/name
 with p.open("xb") as f:
  f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(p)
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
 elif isinstance(v,str):
  try:x=json.loads(v)
  except (ValueError,TypeError):return
  if not isinstance(x,str):yield from walk(x)
core_ref=pin(CORE);parsed=ast.parse(exact(core_ref))
exit_fields=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id=="EXIT_FIELDS" for t in n.targets))
assert exit_fields==("actual_outer_exit","actual_python_exit","actual_native_exit","actual_Go_exit",
                     "actual_SQLite_exit","actual_dispatcher_exit","actual_model_exit")
hdf_ref=pin(FULL/"HDF.json");hdf=json.loads(exact(hdf_ref))
review_ref=hdf["review_report_ref"];review=json.loads(exact(review_ref))
assert hdf["independent_checks_passed"]==review["unique_passed_checks"]==14
assert hdf["full_new_Source_refs_verified"]==review["full_new_Source_refs_verified"]==59
assert hdf["all_guards_closed"] and hdf["retained_handles_count"]==0
assert review["full_Source_guards_closed_zero"]
exact(hdf["manifest_ref"])
for gr in hdf["guard_refs"]:
 g=json.loads(exact(gr))
 assert g["closed"] and g["retained_handles_count"]==0 and not g["errors"]
for key in ("successful_prefix_ref","successful_tail_ref","final_author_check_ref"):exact(review[key])
chunks={1149:"b63c6a",1150:"0a7d51",1151:"a4fc75",1152:"a8563f",1153:"885737"}
rootpins={1152:("dc44ac5e8b0eeb71fe69b5004bc593d32eed8e3dc3325dd010f5a647613705ab",1578),
          1153:("a19513893dee5e75ef2b1e6ba2766f4300e9a5ca7e8ac7e6f12b9e3c58b96714",1566)}
descs={
1149:"审查器 AST 查询误以为存在顶层 own_source 函数，StopIteration；尚未获取 guard，实际 shell/Python 1/1。",
1150:"审查器误要求 source-inputs.references 字节完全相同；实际仅将历史 Caller01 ref 替换为当前 Caller02。实际 shell/Python 1/1，11 个成功检查前缀及 59 refs 的 closed0 guard 保留。",
1151:"审查器将 D:/ 发布展示 ref 与 Windows 反斜杠执行门 ref 按完整字典比较，造成机械谓词失败；真实文件、SHA、bytes、actor 对应一致。实际 shell/Python 1/1，既有 11+2 成功检查保留。",
1152:"Root 只读请求猜测的 source.contract.json 不存在，实际文件名为 root-calling-contract.source.json；实际 a8563f PowerShell 1、Python NULL，不涉及 Source 或 Scope 执行。",
1153:"public observer 绑定检查发现同一 exec 含两个 host 结果，EXPECTED_ACTUAL_EXEC_HOST_RESULT 拒绝；实际 885737 Root shell/Python 1/1。旧原件及此前两次成功 SourceGuard 观察保留，不把后续单独 host 的成功改写进本次退出值。"}
rows=[];checks=[]
for ordinal in range(1149,1154):
 if ordinal<=1151:
  origin_ref=next(r["origin_ref"] for r in hdf["new_original_failures"] if r["ordinal"]==ordinal)
  origin=json.loads(exact(origin_ref))
  io=origin.get("original_complete_IO",origin.get("complete_original_IO"))
  br=io["binding_ref"];rr=io["raw_ref"]
 else:
  bp=S/("original"+str(ordinal)+".actual-root.binding.json")
  origin_ref={"path":str(bp),"sha256":rootpins[ordinal][0],"bytes":rootpins[ordinal][1]}
  origin=json.loads(exact(origin_ref));br=origin_ref;rr=origin["original_capture_ref"]
 binding=json.loads(exact(br));raw=exact(rr);lines=raw.splitlines(keepends=True)
 assert len(lines)==3 and all(x.endswith(b"\n") for x in lines)
 assert [sha(x) for x in lines]==binding["original_line_sha256"]
 assert [len(x) for x in lines]==binding.get("source_line_bytes",binding.get("original_line_bytes"))
 offsets=binding["source_line_offsets"]
 assert offsets==sorted(set(offsets)) and offsets[0]==0
 prefix=binding["source_prefix_size_observed"]
 # Only finite byte ranges are read; the live append-only audit is never guarded or pinned in full.
 with Path(binding["source_audit_path"]).open("rb") as f:
  for offset,line in zip(offsets,lines):
   assert offset+len(line)<=prefix
   f.seek(offset);assert f.read(len(line))==line
 events=[json.loads(x) for x in lines]
 assert events[0]["type"]=="session_meta"
 assert events[1]["payload"]["call_id"]==events[2]["payload"]["call_id"]
 result=events[2]["payload"]
 candidates=[v for v in walk(result.get("output")) if v.get("chunk_id")==chunks[ordinal] and "exit_code" in v]
 assert len(candidates)==1
 host=candidates[0];outer=host["exit_code"]
 markers=re.findall(r"\b[A-Z_]*PYTHON_EXIT=(-?\d+)",host["output"],flags=re.I)
 assert len(set(markers))<=1
 python=int(markers[0]) if markers else None
 assert (outer,python)==((1,None) if ordinal==1152 else (1,1))
 assert binding["actual_outer_exit"]==outer and binding["actual_python_exit"]==python
 assert origin.get("actual_outer_exit",origin.get("outer_exit"))==outer
 assert origin.get("actual_python_exit",origin.get("Python_exit"))==python
 semantic_refs=[]
 if ordinal<=1151:
  semantic_refs += [hdf_ref,review_ref]
  for key in ("original_report_ref","original_closed_guard_ref","original_guard_ref"):
   if key in origin:exact(origin[key]);semantic_refs.append(origin[key])
 if ordinal==1150:assert origin["successful_prefix_checks"]==11 and origin["59_resources_guard_closed_zero"]
 if ordinal==1151:assert origin["successful_prefix_checks"]==11 and origin["successful_tail_checks"]==2 and origin["retained_handles_count"]==0
 row={"ordinal":ordinal,"origin_ref":origin_ref,"origin_selector":"$","origin_json_pointer":"",
      "capture_binding_ref":br,"description":descs[ordinal],
      **{key:(outer if key=="actual_outer_exit" else python if key=="actual_python_exit" else None) for key in exit_fields},
      "source_fact_refs":[origin_ref,br,rr,*semantic_refs],
      "capture_completeness":{"original_call_and_output_preserved":True,"three_actual_host_lines_verified":True,
                              "same_call_successful_prefix_preserved":True},
      "actual_call_id":events[1]["payload"]["call_id"],"actual_chunk_id":chunks[ordinal],
      "source_draft_only":True,"Root_issued":False}
 # Deduplicate refs even when origin and binding are the same immutable document.
 seen=set();row["source_fact_refs"]=[x for x in row["source_fact_refs"] if not (x["path"] in seen or seen.add(x["path"]))]
 assert all(k in row and (row[k] is None or type(row[k]) is int) for k in exit_fields)
 rows.append(row)
 checks.append({"ordinal":ordinal,"raw_ref":rr,"binding_ref":br,"binding_sha256":br["sha256"],
  "source_audit_path":binding["source_audit_path"],"source_line_offsets":offsets,
  "original_line_sha256":binding["original_line_sha256"],"actual_host_bytes_verified":True,
  "actual_call_id":events[1]["payload"]["call_id"],"actual_host_result":host,
  "observed_exit_pair":[outer,python],"python_exit_markers":markers})
# Preserve old twin-host observations and fresh single-host observations as separate source facts.
observer_facts=[]
for stem in ("public21-caller02-source-observed","public21-caller02-runner-observed",
             "public21-caller02-source-observed-host02","public21-caller02-runner-observed-host02"):
 ap=S/("w09."+stem+".actual-audit.root.json");ar=pin(ap);a=json.loads(exact(ar));rr=a["original_capture_ref"]
 raw=exact(rr);lines=raw.splitlines(keepends=True)
 assert len(lines)==3 and [sha(x) for x in lines]==a["original_line_sha256"]
 event=json.loads(lines[2]);hosts=[v for v in walk(event["payload"].get("output")) if "chunk_id" in v and "exit_code" in v]
 assert len(hosts)==(1 if "host02" in stem else 2)
 assert all(x["exit_code"]==0 for x in hosts)
 observer_facts.append({"observation":stem,"audit_ref":ar,"raw_ref":rr,"actual_host_results":hosts,
  "success_preserved_separately_from_original1153":True,"not_execution_qualification_by_this_draft":True})
rows[-1]["source_fact_refs"].extend([x[k] for x in observer_facts for k in ("audit_ref","raw_ref")])
assert [r["ordinal"] for r in rows]==list(range(1149,1154))
assert len({(r["origin_ref"]["sha256"],r["origin_selector"]) for r in rows})==5
for ref in list(facts.values()):exact(ref)
draft={"schema":"researchos.Source-pending-diagnostic-inputs-draft.v1",
 "draft_author":"codex:/root/attach_restore_independent_review","Root_issued":False,
 "origin_selector_syntax":"JSONPath document selector; exact RFC6901 origin_json_pointer also provided",
 "EXIT_FIELDS":list(exit_fields),"exit_fields_source_ref":core_ref,
 "Root_assignment_context_only":{"registered_cutoff":1148,"Root_live_next_at_assignment":1154,
                                 "verified_live_Canon_by_this_task":False},
 "range":{"first":1149,"last":1153,"count":5},"pending":rows,
 "counter_reset":False,"Root_counter_authority":False,"Root_pending_issued":False,
 "Canon_written":False,"Scope_issued":False,"execution_grant":False,"formal_acceptance":False}
dref=put("pending-diagnostic-inputs.draft.json",draft)
vref=put("verification.json",{"schema":"researchos.Source-diagnostic-original-verification.v1","checks":checks,
 "passed_rows":5,"failed_rows":0,"source_only_checking":True,"live_Root_audit_held":False,
 "Full_final_facts":{"HDF_ref":hdf_ref,"report_ref":review_ref,"passed":14,"held_refs":59,
                    "all_guards_closed_zero":True,"original_successful_prefix":11,"original_successful_tail":2},
 "observer_facts":observer_facts,"old_successful_checks_rerun":False,"old_failed_commands_rerun":False,
 "new_original_failures_observed":0,"native_go_model_TP_calls":0})
sref=put("source-fact-pins.json",{"references":list(facts.values()),"count":len(facts),"all_rechecked_unchanged":True})
h={"schema":"researchos.pending-diagnostic-inputs-source-handoff.v1",
 "source_author":"codex:/root/attach_restore_independent_review","status":"SOURCE_DRAFT_COMPLETE_PENDING_ROOT_REVIEW",
 "draft_ref":dref,"verification_ref":vref,"source_fact_pins_ref":sref,"actual_tool_io_ref":pin(N/"actual-tool-io.json"),
 "ordinals":list(range(1149,1154)),"rows":5,"original_host_bindings_verified":5,
 "new_original_failures":0,"Root_issued":False,"Root_pending_written":False,"Canon_written":False,
 "Scope_written":False,"Root_counter_authority":False,"old_failures_retried":False,"unknown_exits_fabricated":False,
 "live_Root_audit_held":False,"Native_Go_SQL_model_TP_calls":0,
 "execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,"STOP":True}
put("HDF.json",h)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
put("MF.json",{"schema":"researchos.source-manifest.v1","members":members,"member_count":len(members),
 "exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
for ref in members:
 b=Path(ref["path"]).read_bytes();assert sha(b)==ref["sha256"] and len(b)==ref["bytes"]
print(json.dumps({"status":h["status"],"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"draft_ref":dref,"verification_ref":vref,
 "rows":5,"source_fact_refs":len(facts),"exit_pairs":[[r["ordinal"],r["actual_outer_exit"],r["actual_python_exit"]] for r in rows]},ensure_ascii=False))

