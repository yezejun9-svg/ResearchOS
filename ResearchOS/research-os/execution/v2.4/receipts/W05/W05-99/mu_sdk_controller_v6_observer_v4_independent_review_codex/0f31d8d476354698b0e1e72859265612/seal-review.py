import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(name,value):
 p=O/name;p.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());return ref(p)
a=json.loads((O/"intake.json").read_bytes());controls=json.loads((O/"independent-controls.json").read_bytes())
drift=[]
for row in a["rows"]:
 current=ref(row["source_ref"]["path"])
 if current!=row["source_ref"]:drift.append({"expected":row["source_ref"],"actual":current})
assert not drift,drift
put("final-input-recheck.json",{"schema":"researchos.c6-o4-input-recheck.v1","records":len(a["rows"]),"drift":drift,
 "source_handoff_and_manifest_pins_current":True,"canonical_files_read_or_frozen":False})
counter=next(x for x in controls["cases"] if not x["matches_expected"])
finding={"id":"C6-O4-R01","priority":"P1","title":"Pass the complete reviewed Source context into the actual O4 callback",
 "controller_source_ref":a["tuple"]["controller_source_ref"],"controller_line":counter["controller_line"],
 "observer_source_ref":a["tuple"]["observer_source_ref"],"observer_lines":[180,184,195,208,278],
 "trigger":"Root uses the immutable C6 launch_reviewed_phase with a valid independently reviewed C6/O4 tuple and reaches before_resume.",
 "actual":"C6 constructs its observer context without canonical_transactions_source, job_watchdog_source, source_guard_source and base_owned_process_source. O4 validate_context calls validate_source_review, then source_author_provenance indexes the absent canonical_transactions_source key. It raises KeyError before OS observation, receipt publication or ResumeThread.",
 "impact":"All otherwise-valid real phase launches fail admission. The later complete provenance_context is constructed only after observer.observe_assigned_before_resume returns, so it cannot repair this caller contract.",
 "independent_counterexample":counter,
 "smallest_fix":"Construct the complete fixed Source context before invoking observer.observe_assigned_before_resume and pass the four already guarded constants. Reuse that same context for the later author check. Bind the new C6 bytes in a fresh Source revision; do not change sealed C6/O4 artifacts.",
 "scope":"Source wiring failure only. No native launch or provider call was attempted by this reviewer."}
findings=put("findings.json",{"schema":"researchos.c6-o4-independent-findings.v1","decision":"REQUEST_CHANGES","findings":[finding]})
report="""独立结论：REQUEST_CHANGES。C6/O4 固定 Source 组合存在一个 P1 接线问题，当前不能签发 READY_SOURCE_ONLY。

C6-O4-R01：before_resume 构造并传给 O4 的 context 缺少 canonical_transactions_source、job_watchdog_source、source_guard_source、base_owned_process_source。O4 的固定 11-role provenance 必须读取这四项，因此合法精确 review 在真实 callback 上仍会抛 KeyError('canonical_transactions_source')。C6 后续才构造完整 provenance_context，无法帮助前面的 observer 调用。独立控制直接求值原始 callback context AST，再调用原始 O4 pure gate，复现失败。诊断中补入这四个既有 pin 后 gate 通过；没有修改任何候选 Source。

C5-R01 的作者政策已在 Source 中修正：Root、w05、live 和自动 observer 均不能自评整个 Source tuple；固定 11-role provenance 不使用 review 自称的作者列表。C6 pre-import gate 和 O4 gate 在完整 context 下拒绝作者与 provenance 篡改，新增 cleanup_producer_ref 与 review 精确绑定。C6 固定 O4 hash；O4 从受保护 context 接受 controller pin，未形成互相嵌入 Source hash 的循环。上述政策修复仍受本次实际 caller 缺项阻断。

C5-R02 的任意 callback 接口已移除。新 producer 在 ResumeThread 前从实际 Job/process handle 复制句柄，记录 runner PID、creation time、run UUID 和 Job binding；parent resident record 在捕获前已持有 producer，部分捕获失败也保留成功复制的句柄。恢复逻辑从该 producer 查询 Job active count 和 signaled primary，再要求调用内时间、两秒上限、精确身份、strict int zero 和无查询错误。future/NaN/Inf、活子进程、未退出、身份错配、OS 查询错误均不能关闭 Source。失败 CloseHandle 保留句柄与 owner record，成功重试不重复关闭已关闭句柄。watchdog 用显式 TerminateJobObject，因此 producer 持有另一个 Job duplicate 不会使 deadline 仅依赖 kill-on-last-close。

本次新增 67 项独立 pure AST/fake 控制，66 项符合，1 项反例对应上述单一 P1。控制还覆盖 normal/None/live-child/pre-native/部分capture/最终清理中断、guard/watchdog/producer close failure、Thread.start failure 和 join timeout。没有导入候选模块，没有调用候选入口、Windows API、SQL 或 provider，也没有真实线程。测试的 fake kernel 结果不是实际 Windows cleanup。

59 个不同输入记录已逐字节 pin 并在封存前复核，零漂移。C6 controller、O4 observer、新 producer 的正向与逆向 diff 均实际应用后逐字节匹配；独立生成的 hunks 相同。五个已有 helper 与 C5 完全相同。旧 O2/v9/Guard Source controls、actual private Guard probe 和既有 cancel 证据沿用其原范围，不重复运行，不提升为完整 trial 证据。作者 167 O4 与 7 C6 controls 未作为独立结果重跑。

Root 常驻父进程的真实存活、实际 duplicated-handle lifecycle、Host sibling Job/stdio/common deadline 接入、真实 qualification/acceptance/provider reconciliation 保持 OPEN。Source reviewer 未给 Root execution grant，formal acceptance 增量为零。未读或写 Main/canonical 状态。仅本独立 review 目录写入。

本审查新增工具失败为零。此前 caller locator 704、O4 locator 705、C6 author fake fixture 706 是原有独立 origin，本审查不重计、覆盖或借用后续成功结果改写它们。
"""
(O/"review.md").write_bytes(report.encode("utf-8"))
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2",
 "actor_id":"codex:/root/command_queue_impl","decision":"REQUEST_CHANGES",**a["tuple"],
 "source_provenance":controls["source_provenance"],"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME",
 "formal_acceptance":False,"execution_ready":False,"execution_grant_issued":False,"runtime_qualification":False,
 "controller_handoff_ref":a["controller_handoff_ref"],"controller_manifest_ref":a["controller_manifest_ref"],
 "observer_handoff_ref":a["observer_handoff_ref"],"observer_manifest_ref":a["observer_manifest_ref"],
 "additional_dependencies":[v for k,v in a["source_context"].items() if k in
 ("canonical_transactions_source","job_watchdog_source","source_guard_source","base_owned_process_source","cleanup_producer_source")],
 "prior_c5_review_ref":a["prior_c5_review_ref"],"prior_c4_review_ref":a["prior_c4_review_ref"],
 "actual_guard_probe_review_ref":a["actual_guard_probe_review_ref"],"reused_not_rerun":a["reused_not_rerun"],
 "new_independent_controls":controls["summary"]["total"],"matched":controls["summary"]["matched"],
 "counterexamples":len(controls["summary"]["counterexamples"]),"distinct_findings":1,
 "C5_R01":"FIXED_POLICY_IN_SOURCE_BUT_REAL_CALLBACK_CONTEXT_BLOCKED_BY_C6_O4_R01",
 "C5_R02":"FIXED_IN_REVIEWED_SOURCE_AND_FAKE_CONTROLS_ACTUAL_OS_LIFECYCLE_OPEN",
 "findings_ref":findings,"controls_ref":ref(O/"independent-controls.json"),"report_ref":ref(O/"review.md"),
 "original_tool_io_ref":ref(O/"original-tool-io.json"),"input_records":len(a["rows"]),"input_drift":0,
 "author_controls_executed":0,"new_tool_failures":0,"candidate_actual_entry_or_WinAPI_SQL_provider_calls":0,
 "real_threads_started":0,"Main_canonical_writes":0,"formal_case_increment":0,
 "open":["C6_O4_R01_ACTUAL_CALLBACK_CONTEXT","ROOT_PARENT_RESIDENCY","ACTUAL_HELD_JOB_CLEANUP",
 "ROOT_HOST_SIBLING_JOB_STDIN_COMMON_DEADLINE","NO_QUALIFICATION_OR_FORMAL_TRIAL"],"stopped":True}
review_ref=put("independent-source-review.json",review)
print(json.dumps({"review_ref":review_ref,"findings_ref":findings,"report_ref":ref(O/"review.md"),
 "decision":review["decision"],"controls":controls["summary"],"input_drift":len(drift)},ensure_ascii=False,indent=2))

