from pathlib import Path
import json,hashlib,re
from datetime import datetime,timezone
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W09/W09-99"
N=B/"integration_codex/w09c19v7-root-scope-20261009"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(ref):
 b=Path(ref["path"]).read_bytes();assert hashlib.sha256(b).hexdigest()==ref["sha256"] and len(b)==ref["bytes"];return b
def save(name,value):
 p=O/name;assert not p.exists();p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8");return pin(p)
expected={"7b5b34":("a1c19f1097310ed1f2987bf0a6f9226c64e5d8eb1ec65b6f14500e34f66ef50b",5449),"6444d0":("5a1228c946022cef99001d6406b17a2376d1d9f253d796c69e7e2c9cba4b63cb",3571),"bc4ba4":("ff917b67fcd0eb330ea08f8f2ab4b2cef5007a3a13e9770f87b25262c0e9775c",3043),"868a4b":("adb9f5be84345f29b3389957812269c70427558eef1ad9fef9bb4303392cff7e",3714)}
fullrefs=[];verified=[]
for chunk,(sha,size) in expected.items():
 ref={"path":str(N/("producer-original-"+chunk+".full-tool-io.root.json")),"sha256":sha,"bytes":size};d=json.loads(read(ref));fullrefs.append(ref)
 assert d["original_chunk_id"]==chunk and d["product_rerun"] is False and d["sealed_existing_artifacts_modified"] is False
 pair=d["original_call_and_result"];assert len(pair)==2 and pair[0]["type"]=="custom_tool_call" and pair[1]["type"]=="custom_tool_call_output" and pair[0]["call_id"]==pair[1]["call_id"]==d["original_call_id"]
 original_results=json.loads(read(d["original_result_only_ref"]));prior=next(x["result"] for x in original_results["records"] if x["result"]["chunk_id"]==chunk)
 candidates=[]
 for block in pair[1]["output"]:
  text=block.get("text","")
  if text.startswith('{"chunk_id"'):candidates.append(json.loads(text))
 assert candidates==[prior]
 statement=pair[0]["input"]
 if chunk in ["7b5b34","bc4ba4"]:
  match=re.search(r'cmd:("(?:[^"\\]|\\.)*")',statement);assert match
  command=json.loads(match.group(1))
  for value in ['9628b913e83364f629a38e8cc6dce8c5ebedb8566fa7e5ce43a6b0e624ccde21',"'4302132'","'366'",'1dfed486c4cd91f043dd48bd6b6eef46dc06ca52bce9339289c6e5cb13dcffda',"'983'"]:assert value in command
  assert ('prepare_w09_c19.actual_owned.py' if chunk=='7b5b34' else 'run_w09_c19.actual_owned.py') in command
  if chunk=='bc4ba4':assert 'c606f65f383051252f6c2697d4ea76e31b0b223e2afacf377c6d43283c99a8aa' in command and "'16693'" in command and 'bc785ec6be0e4c1943539b27194d4abefc9c66dbd050b1cb3e921e18b153712a' in command
 else:assert ('session_id:81639' if chunk=='6444d0' else 'session_id:14737') in statement
 verified.append({"chunk_id":chunk,"call_id":d["original_call_id"],"full_io_ref":ref,"result_exactly_equal_earlier_result_only":True,"original_inputs_validated":True,"executed_by_reviewer":False})
supplement=save("producer-original-full-io.supplement-review.json",{"decision":"PASS","scope":"NEW_PUBLIC_ORIGINAL_CALL_AND_RESULT_SUPPLEMENT_ONLY","records":verified,"old_producer_result_only_archive_and_sealed_review_changed":False,"producer_rerun":False,"original_source_execution_ref_not_reconstructed":True})
a=json.loads((O/"actual-consumer-summary.json").read_bytes());c=json.loads((O/"checks.json").read_bytes());gaps=json.loads((O/"formal-gaps.actual-readonly.json").read_bytes());allpins=json.loads((O/"verified-input-pins.json").read_bytes())
for ref in allpins:read(ref)
assert all(x["pass"] for x in c["checks"])
summary=dict(a["summary"],recorded_checks=len(c["checks"]))
review={"schema":"researchos.w09-c19-v7-consumer-independent-actual-review.v1","reviewed_at":datetime.now(timezone.utc).isoformat(),"actor_id":"codex:/root/native_temp_independent_review","decision":summary["decision"],"scope":"TWO_COMPONENT_CONSUMERS_SINGLE_C19_CASE_ONLY","summary":summary,"checks_ref":pin(O/"checks.json"),"actual_summary_ref":pin(O/"actual-consumer-summary.json"),"formal_gaps_ref":pin(O/"formal-gaps.actual-readonly.json"),"producer_original_full_io_supplement_ref":supplement,"root_consumer_original_full_io_ref":a["root_original_tool_io_ref"],"claims_verified":["Both observed consumer Python processes returned zero and both output status PASS","Each route reports the same three C19 formal assertion IDs while binding all five original Native assertion IDs","Same C19 case counted once; same immutable original report, tool run, Source21, current canonical 366/170 vector and common non-author mode review","Two distinct route-specific modes from the prior non-author producer review, exact candidate bytes","2351 finite inputs plus the input-list file were held by the original Windows read-only guard and all2352 entries closed; current listed bytes remain exact","Both original Windows jobs report suspended assignment, primary exit, zero active processes, idle confirmation and closed handles","Observed caller and router paths exclude formal dispatcher and preserved subprocess branch; commands registry remains byte-identical to the held baseline","Main six-source adoption, C19 formal registry binding and W09 formal verification profile remain open"],"independence":{"source_author":False,"consumer_caller_author":False,"actual_consumer_executor":False,"prior_mode_packet_author":True,"basis":"Reviewer did not author producer/consumer source or execute either consumer; prior mode packet authorship is disclosed."},"limitations":{"system_wide_process_or_network_audit":False,"fresh_guard_contention_test":False,"current_formal_acceptance_issued":False,"W09_parent_accepted":False,"A06_G01_G02_covered_by_this_run":False,"Main_adopted":False,"new_execution_grant":False,"financial_control_proven":False},"formal_case_accepted_delta":0,"formal_cases_accepted_from_this_review":0,"new_original_failures":[],"root_reported_pending_diagnostics":list(range(937,946)),"root_reported_live_next":946,"next":"Continue under Root governance for reviewed Main integration, selector-safe registry binding, remaining W09 gates and independent formal verification. Component PASS does not create CURRENT formal status."}
save("review.json",review)
save("original-failures.json",{"new_original_failures":[],"root_reported_pending_diagnostics":list(range(937,946)),"root_reported_live_next":946,"prior_diagnostic_origins_not_rewritten":True,"Root_reported_944":"Original transcript lookup used the wrong worker source and failed before any new Native execution; retained separately by Root.","Root_reported_945":"W05 Source ParserError, original refs pending at notification; not consumer Native evidence."})
text="两个 C19 组件消费者实际独审通过。两路 consumer Python exit=0，各报告3条形式断言，共同绑定同一原始报告中的5条Native断言；C19只计一个case。没有新Go Native执行，也没有产生正式验收。\n\n原Windows owned jobs均已退出且句柄关闭。2,351个有限输入与输入清单文件组成2,352项读取保护记录，全部闭合且当前字节一致。四份Canon仍为366/170对应精确向量。\n\n剩余：Main三份缺失、三份drift；C19正式registry尚未绑定；formal_case_index只实现W04/W07 profile。A06、W09-G01/G02与W09父验收不在本次完成范围。旧producer审查及result-only原档不变，新的完整原始调用补充单独校验。\n"
(O/"REPORT.md").write_text(text.replace('\n','
'),encoding="utf-8")
anchors=[a[k] for k in ["closed_ref","request_ref","scope_ref","caller_ref","guard_ref","inputs_ref","root_original_tool_io_ref","producer_review_handoff_ref","caller_review_handoff_ref"]]+a["canonical_refs"]+fullrefs
for ref in anchors:read(ref)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"MF.json","HDF.json"}]
mf=save("MF.json",{"schema":"researchos.w09-c19-v7-consumer-independent-actual-manifest.v1","members":members,"member_count":len(members),"input_anchor_refs":anchors,"verified_input_pins_ref":pin(O/"verified-input-pins.json"),"excludes_self_and_handoff":True,"input_drift":0})
hdf={"schema":"researchos.w09-c19-v7-consumer-independent-actual-handoff.v1","actor_id":review["actor_id"],"decision":review["decision"],"actual_component_status":"PASS","formal_status":"NOT_CURRENT_NOT_REGISTERED","review_ref":pin(O/"review.json"),"manifest_ref":mf,"report_ref":pin(O/"REPORT.md"),"checks_ref":pin(O/"checks.json"),"actual_summary_ref":pin(O/"actual-consumer-summary.json"),"formal_gaps_ref":pin(O/"formal-gaps.actual-readonly.json"),"producer_original_full_io_supplement_ref":supplement,"root_consumer_original_tool_io_ref":a["root_original_tool_io_ref"],"consumer_closed_ref":a["closed_ref"],"consumer_invocation_refs":[x["invocation_ref"] for x in a["consumers"]],"original_run_id":summary["run_id"],"single_case_id":"C19","formal_case_count":1,"component_routes":summary["routes"],"recorded_checks":len(c["checks"]),"held_guard_entries":2352,"finite_input_refs":2351,"consumer_python_exits":[0,0],"new_product_native_exit":None,"all_owned_jobs_closed":True,"all_guards_closed":True,"all_held_inputs_unchanged":True,"canonical_refs":a["canonical_refs"],"canonical_revisions":[366,170],"formal_case_accepted_delta":0,"formal_acceptance":False,"CURRENT_formal_status_created":False,"W09_parent_accepted":False,"Main_adopted":False,"registry_written":False,"formal_dispatcher_executed":False,"reviewer_new_product_or_consumer_execution":False,"execution_grant":False,"new_original_failures":[],"root_reported_live_next":946,"STOP":True,"FINAL":True}
save("HDF.json",hdf)
for ref in members+anchors:read(ref)
print(json.dumps({"HDF":pin(O/"HDF.json"),"MF":pin(O/"MF.json"),"review":pin(O/"review.json"),"supplement":supplement,"decision":review["decision"],"recorded_checks":len(c["checks"]),"member_count":len(members),"anchor_count":len(anchors),"new_original_failures":[]},ensure_ascii=False))
