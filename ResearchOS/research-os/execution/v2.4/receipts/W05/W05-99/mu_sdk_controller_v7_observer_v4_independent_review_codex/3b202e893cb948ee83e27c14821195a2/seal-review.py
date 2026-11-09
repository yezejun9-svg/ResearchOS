import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,d):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(p)
a=json.loads((O/"intake.json").read_bytes());drift=[]
for row in a["rows"]:
 actual=ref(row["source_ref"]["path"])
 if actual!=row["source_ref"]:drift.append({"expected":row["source_ref"],"actual":actual})
assert not drift,drift
recheck=put("final-input-recheck.json",{"schema":"researchos.c7-source-input-recheck.v1","source_inputs":len(a["rows"]),"drift":drift,"canonical_state_frozen":False})
report="""结论：READY_SOURCE_ONLY。C7 对 C6-O4-R01 的四字段修复已通过独立窄范围审查。该结论只适用于本回执绑定的 C7/O4/runner/helper/Python 精确 Source tuple。

C7 的原始 before_resume context AST 现在包含 canonical_transactions_source、job_watchdog_source、source_guard_source、base_owned_process_source，各自精确使用对应受保护常量。直接求值实际 context 并送入未变 O4 validate_source_review 门禁可通过；删除这四项仍复现旧 KeyError。C7 实际 pre-import 审查前缀也接受本轮当前 tuple 与固定 11-role source_provenance。

五项独立 delta controls 全部通过。完整 forward/inverse diff 实际应用后逐字节相等；去掉四项后的完整 C7 AST 与 C6 相同。六个 helper 的字节与 C6 完全相同，包括 cleanup producer；HERE-local pins 指向 C7 当前目录，observer O4、runner v9、Python 和外部 guard/base helper 保持原已审查字节。38 个不同输入记录在封存前再次验证，零漂移。

C6/O4 的 67 项控制保持原历史结论：66 符合、1 个接线反例。本轮用五项 delta controls 关闭该反例，不重跑、不改写旧报告，也不把旧统计伪装成 C7 新执行。此前 component Source review、actual private Guard probe 与 cancel 证据继续仅在原范围内复用。作者 delta controls 未执行。

本轮没有导入候选模块或执行候选入口、真实 Windows API、线程、SQL、provider，没有 Main/canonical 写入，没有执行授权和 formal acceptance 增量。Root 常驻父进程的实际存活、真实 held-Job cleanup lifecycle、Host sibling Job/stdin/common deadline 接入、实际 qualification 与完整 trial 仍 OPEN。

原 706/709 作者控制与 seal audit 失败由各自独立 origin 保留；本轮没有重计这些历史失败。新增工具失败为零。只写本独立 review 目录，封存后 STOP。
"""
(O/"review.md").write_bytes(report.encode())
findings=put("findings.json",{"schema":"researchos.c7-independent-delta-findings.v1","decision":"READY_SOURCE_ONLY",
 "open_source_findings":[],"closed":[{"id":"C6-O4-R01","status":"CLOSED_IN_EXACT_C7_SOURCE",
 "prior_findings_ref":a["prior_findings_ref"],"evidence_ref":ref(O/"independent-delta-controls.json")}],
 "open_runtime":["ROOT_PARENT_RESIDENCY","ACTUAL_HELD_JOB_CLEANUP_LIFECYCLE","ROOT_HOST_SIBLING_JOB_STDIN_COMMON_DEADLINE","ACTUAL_QUALIFICATION_AND_TRIAL"]})
review={**a["review_fields"],"execution_ready":False,"execution_grant_issued":False,"runtime_qualification":False,
 "source_review_scope":"C7 exact four-field callback delta plus unchanged C6/O4 whole Source evidence",
 "controller_handoff_ref":a["controller_handoff_ref"],"controller_manifest_ref":a["controller_manifest_ref"],
 "prior_review_ref":a["prior_review_ref"],"prior_review_handoff_ref":a["prior_review_handoff_ref"],
 "prior_controls_ref":a["prior_controls_ref"],"prior_controls_reused_not_rerun":{"total":67,"matched":66,"counterexamples":1,"closed_by_this_delta":"C6-O4-R01"},
 "additional_dependencies":[a["source_context"][k] for k in ("canonical_transactions_source","job_watchdog_source","source_guard_source","base_owned_process_source","cleanup_producer_source")],
 "new_independent_delta_controls":5,"passed":5,"counterexamples":0,"findings_ref":findings,
 "controls_ref":ref(O/"independent-delta-controls.json"),"report_ref":ref(O/"review.md"),
 "original_tool_io_ref":ref(O/"original-tool-io.json"),"input_recheck_ref":recheck,
 "input_records":len(a["rows"]),"input_drift":0,"author_controls_executed":0,"new_tool_failures":0,
 "candidate_module_imports":0,"candidate_entry_or_WinAPI_SQL_provider_calls":0,"real_threads_started":0,
 "Main_canonical_writes":0,"formal_case_increment":0,
 "open":["ROOT_PARENT_RESIDENCY","ACTUAL_HELD_JOB_CLEANUP_LIFECYCLE","ROOT_HOST_SIBLING_JOB_STDIN_COMMON_DEADLINE","ACTUAL_QUALIFICATION_AND_TRIAL"],"stopped":True}
rr=put("independent-source-review.json",review)
print(json.dumps({"review_ref":rr,"findings_ref":findings,"report_ref":ref(O/"review.md"),"decision":review["decision"],
 "delta_controls":5,"input_records":len(a["rows"]),"input_drift":0},ensure_ascii=False,indent=2))

