import json,hashlib,os,re
from pathlib import Path
N=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def checked(ref):
 b=Path(ref["path"]).read_bytes()
 assert sha(b)==ref["sha256"] and len(b)==ref["bytes"],ref
 return b
def put(name,obj):
 p=N/name
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
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
observations=json.loads((N/"verified-original-observations.json").read_bytes())
chunks={1135:"95e86c",1136:"cd338a",1137:"30e2b7",1138:"4d20d9",1139:"d72b6c",1140:"950b1e",1141:"9fecd1",1142:"48a277",1143:"c8e2f1",1144:"c20c0e",1145:"5f53f9",1146:"ac9d42"}
expected={1134:(None,None),1135:(1,None),1136:(2,2),1137:(1,None),1138:(1,1),1139:(0,None),1140:(1,1),1141:(1,1),1142:(1,1),1143:(0,0),1144:(1,1),1145:(1,None),1146:(1,1)}
descriptions={
1134:"apply_patch 对 prepare_source_revision.py 的精确文本匹配失败：预期 raw=raw.replace，实际初始语句为 raw=original.replace。工具拒绝，未启动进程，全部进程退出值为 NULL。",
1135:"只读 rg 使用不存在的 ops/ci/formal_profile_w09.py；同次调用的成功目录清单和搜索输出保留。shell 退出 1，未观测 Python 或产品进程退出。",
1136:"Root 用仓库内不存在的 tools/task_packet.py 路径启动 Python；实际工具在 implementation package。shell/Python 退出 2/2。",
1137:"只读 Get-Content 请求不存在的 NF3 native_runtime.source.py；原始同批成功读取保留。shell 退出 1，Python NULL。",
1138:"Source sealer 查找旧 capture index，未定位实际 rejection call ID，退出 1/1；原有成功 Source controls 不受影响。",
1139:"首个 rg 请求不存在的 execution/v2.4/retrieval.py，后续搜索成功；整体 shell 退出 0。独立 inner rg 退出值未观测，保留 NULL。",
1140:"caller 构建的精确两行替换预期 CRLF，与实际 Source 不匹配，REPLACE_MISSING；shell/Python 退出 1/1。",
1141:"caller continuation 的 dedent 改变多行替换字符串缩进，REPLACE_MISSING，caller 未到达；shell/Python 退出 1/1。",
1142:"Root resource-only 目录准备的物理路径断言拒绝 C AppData 到 D 的别名；shell/Python 退出 1/1。旧失败及后续独立资源证据不合并。",
1143:"独立审查错误地将 78 个历史 Source 成员与 62 个 input-manifest refs 等同，原始结果有 1 个语义失败；真实 shell/Python 仍为 0/0，不改成进程失败。",
1144:"Bridge 独立 Source 审查在 ast.literal_eval(TRUSTED) 遇到 Name GUARD，尚未获取 SourceGuard；shell/Python 退出 1/1。",
1145:"Bridge03 首次读取 Task98 HDF 路径缺 W09-99，Get-Content 失败；同次 Bridge02 成功目录清单保留。shell 退出 1，Python NULL。",
1146:"Root public21 helper initialise 调用 safe_directory，再经 canonical 进入 SourceReadGuard._canonical，拒绝不满足 regular file components 的路径；真实 ac9d42 shell/Python 退出 1/1。"}
rows=[];refs={};checks=[]
for item in observations["rows"]:
 ordinal=item["ordinal"];o=item["origin_value"];raw=checked(item["raw_ref"])
 origin=json.loads(checked(item["origin_ref"]))
 pointer=item["origin_selector"]["json_pointer"]
 if pointer:origin=origin[pointer[1:]]
 assert origin==o
 checked(item["capture_binding_ref"])
 if ordinal==1146:
  assert item["origin_ref"]["sha256"]=="0c7c491e043cdf781ff5b54a23ca7e5fbd7175145848d2a67c27e3ed39088d10" and item["origin_ref"]["bytes"]==1100
 events=[json.loads(x) for x in raw.splitlines()]
 assert events[2]["payload"]==item["output_payload"]
 chunks_found=[x for x in walk(item["output_payload"].get("output")) if "chunk_id" in x and "exit_code" in x]
 if ordinal==1134:
  assert not chunks_found and origin["process_started"] is False
  assert "apply_patch verification failed" in str(item["output_payload"])
  outer=python=None;selected=None;markers=[]
 else:
  selected=[x for x in chunks_found if x["chunk_id"]==chunks[ordinal]]
  assert len(selected)==1,(ordinal,len(selected));selected=selected[0]
  outer=selected["exit_code"]
  markers=re.findall(r"\b[A-Z_]*PYTHON_EXIT=(-?\d+)",selected["output"],flags=re.I)
  assert len(set(markers))<=1
  python=int(markers[0]) if markers else None
 assert (outer,python)==expected[ordinal],(ordinal,outer,python)
 origin_outer=origin.get("actual_outer_exit",origin.get("outer_exit",outer))
 origin_python=origin.get("actual_python_exit",origin.get("actual_Python_exit",origin.get("Python_exit",python)))
 assert origin_outer==outer and origin_python==python,(ordinal,"origin discrepancy")
 row={"ordinal":ordinal,"origin_ref":item["origin_ref"],
 "origin_selector":"$"+("."+pointer[1:] if pointer else ""),
 "origin_json_pointer":pointer,"capture_binding_ref":item["capture_binding_ref"],
 "description":descriptions[ordinal],"actual_outer_exit":outer,"actual_python_exit":python,
 "actual_native_exit":None,"actual_dispatcher_exit":None,"actual_model_exit":None,
 "actual_go_exit":None,"actual_Go_exit":None,"actual_TP_exit":None,"actual_SQLite_exit":None,
 "inner_rg_exit":None,"unknown_exit_policy":"NULL means no separately observed exit; never inferred from outer status",
 "source_fact_refs":[item["origin_ref"],item["capture_binding_ref"],item["raw_ref"]],
 "capture_completeness":{"original_three_lines_preserved":True,"actual_host_offsets_hashes_verified":True,
 "original_call_and_output_retained":True,"successful_same_call_output_preserved":True},
 "actual_call_id":item["actual_call_id"],"actual_chunk_id":chunks.get(ordinal),
 "semantic_failed_predicates":1 if ordinal==1143 else None,
 "source_draft_only":True,"Root_issued":False,"registered_in_current_canon_by_this_task":False}
 if ordinal==1143:
  result=json.loads(selected["output"].splitlines()[0])
  assert len(result["failed"])==1 and result["leaf_input_ref_count"]==62
  assert result["failed"][0]["id"]=="leaf78-input-closure-current-held"
  row["semantic_facts"]={"historical_Source_member_count_in_original_predicate_name":78,"actual_input_manifest_ref_count":62,
    "failed_predicate_id":"leaf78-input-closure-current-held","process_exit_unchanged":True}
  row["source_fact_refs"].append(origin["result_ref"])
 if ordinal==1134:row["process_started"]=False
 for ref in row["source_fact_refs"]:
  checked(ref);refs[ref["path"]]=ref
 rows.append(row)
 checks.append({"ordinal":ordinal,"original_ref_bytes_verified":True,"host_binding_verified":True,
 "selected_chunk":chunks.get(ordinal),"observed_outer":outer,"observed_python":python,"python_exit_markers":markers,
 "original_semantic_failure_preserved":ordinal==1143})
assert [r["ordinal"] for r in rows]==list(range(1134,1147))
draft={"schema":"researchos.Source-pending-diagnostic-inputs-draft.v1",
 "draft_author":"codex:/root/attach_restore_independent_review","Root_issued":False,
 "origin_selector_syntax":"JSONPath document selector; exact RFC6901 origin_json_pointer also provided",
 "Root_assignment_context_only":{"canonical_checkpoint":"CP377","registered_cutoff":1133,"canonical_next":1134,"Root_live_next_at_assignment":1147,
 "verified_live_Canon_by_this_task":False},
 "range":{"first":1134,"last":1146,"count":13},"pending":rows,
 "counter_reset":False,"Root_counter_authority":False,"Root_pending_issued":False,
 "Canon_written":False,"Scope_issued":False,"execution_grant":False,"formal_acceptance":False}
dref=put("pending-diagnostic-inputs.draft.json",draft)
vref=put("verification.json",{"schema":"researchos.Source-diagnostic-original-verification.v1",
 "checks":checks,"passed_rows":13,"failed_rows":0,"product_or_old_failure_retries":0,
 "verification_kind":"raw capture parse plus original immutable ref checks and earlier actual-host byte-range verification",
 "new_original_failures_observed":0})
for ref in refs.values():checked(ref)
sref=put("source-fact-pins.json",{"references":list(refs.values()),"count":len(refs),"all_rechecked_unchanged":True})
h={"schema":"researchos.pending-diagnostic-inputs-source-handoff.v1",
 "source_author":"codex:/root/attach_restore_independent_review","status":"SOURCE_DRAFT_COMPLETE_PENDING_ROOT_REVIEW",
 "draft_ref":dref,"verification_ref":vref,"source_fact_pins_ref":sref,
 "original_observations_ref":pin(N/"verified-original-observations.json"),"actual_tool_io_ref":pin(N/"actual-tool-io.json"),
 "ordinals":list(range(1134,1147)),"rows":13,"original_host_bindings_verified":13,
 "new_original_failures":0,"Root_issued":False,"Root_pending_written":False,"Canon_written":False,"Scope_written":False,
 "Root_counter_authority":False,"old_failures_retried":False,"unknown_exits_fabricated":False,
 "execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,"STOP":True}
put("HDF.json",h)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
put("MF.json",{"schema":"researchos.source-manifest.v1","members":members,"member_count":len(members),
 "exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
for ref in members:checked(ref)
print(json.dumps({"status":h["status"],"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),
 "draft_ref":dref,"verification_ref":vref,"rows":13,"source_fact_refs":len(refs),
 "exit_pairs":[[r["ordinal"],r["actual_outer_exit"],r["actual_python_exit"]] for r in rows]},ensure_ascii=False))

