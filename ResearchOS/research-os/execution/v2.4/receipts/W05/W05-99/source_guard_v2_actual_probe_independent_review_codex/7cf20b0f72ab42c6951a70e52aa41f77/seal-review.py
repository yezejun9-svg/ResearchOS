import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
a=json.loads((O/"bound-audit.json").read_bytes())
for row in a["rows"]:
 r=row["source_ref"];current=ref(pathlib.Path(r["path"]))
 assert current["sha256"]==r["sha256"] and current["bytes"]==r["bytes"]
report="""SourceReadGuard v2 实际 Windows probe 独立复核

结论：PASS_ACTUAL_PRIVATE_WINDOWS_COMPONENT_IN_SCOPE。仅接受本次私有目标组件 probe 的实际证据；不接受整条 Controller、Host、SDK trial、runtime qualification 或正式验收。C4-R01 未确认 Job 清理分支释放 Source guard 的问题保持 OPEN。

本次 Root 原始工具调用 c4a7ea outer exit=0、父 Python exit=0，owned child native exit=0。原始 stdout 的 proof 引用与 PID 41408、probe.invocation 的 owned_child_pid、最终 closed 引用逐项一致。固定的 windows_owned_process.py 实际赋予新建进程该 helper 的 unnamed Job，随后 ResumeThread；记录确认 assigned_before_resume、primary exit、Job active_processes=0、handles_closed、errors=[]。因此使用完整 producer/原始调用/PID/assignment/cleanup 链，不从 IsProcessInJob(..., NULL) 单独推出 exact Job 身份。

被测 Guard Source e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85/11404 与 w05 非作者 PASS_SOURCE_ONLY 精确一致。实际取得三个可读但拒绝写/删除共享的句柄：两个私有源文件和当前固定 Python 可执行文件。三个 entries 的字节、最终路径验证通过，close 后 retained_handles_count=0、errors=[]。针对 Python 仅验证真实 held handle 和精确 bytes，没有尝试修改 Python。

对中文私有目标文件，持有期间读取成功；raw CreateFileW 写句柄与 DeleteFileW 均失败且 GetLastError=32。MoveFileExW 返回失败且 GetLastError=5；同一个 raw_replace 函数、相同 source/destination 路径，在取得 Guard 前与关闭后均成功。因此保留真实值 5，并结合前后阳性对照确认该范围内的替换阻止，不伪写成 32。三个负例先写 journal、flush/fsync，再断言，journal 与最终 proof 完全一致。关闭后写入、替换成功，证明私有目标可恢复使用。两个 fixture 的 held-time bytes 在持有期间检查不变；关闭后其中一个 fixture 被阳性控制主动改变，不能把 held-time pin 当作其事后的当前内容。

Root 父 producer 对 canonical4 与 Main5 记录了执行前 pins，并在 finally 逐字节比较，九项均 unchanged=true；本审查首次读取时也独立复算九项当前 hash，与 probe-time pins 一致。后续 Root 正常更新 canonical 不属于此 probe 的写入，也不据此改写历史比较。

旧失败仍为失败。696 原始 outer/父 Python/child native 均为 1：Python stdio PermissionError13 已记录写入拒绝，随后 producer 强行期望 winerror32 导致断言失败。698 原始 outer/父 Python/child native 亦均为 1：表达式 not succeeded and observed==32 在 replacement 步骤断言失败，旧 producer 没持久 raw success flag 和错误值，原 stderr 无法说明哪个条件失败；这两个值保持未知，不能把本次 5 回填为旧结果。两轮旧 guard cleanup 和 owned Job cleanup 均核验完成。每轮原有单一因果链保留，不增加、不重置或重复计算历史失败。

最终 Root MF 的 13 个 members、41 条输入记录全部字节绑定，无漂移。本审查只读取文件、核 hash、解析 JSON/AST；未导入或重跑 probe/Guard/native，没有 WinAPI、SQL、provider 或 Main/canonical 写入，也没有新审查工具失败。所有审查写入限本独立 namespace。
"""
(O/"review.md").write_text(report,encoding="utf-8")
review={"schema":"researchos.source-read-guard-actual-probe-independent-review.v1","actor_id":"codex:/root/command_queue_impl","source_author":"codex:/root","independent":True,"decision":"PASS_ACTUAL_PRIVATE_WINDOWS_COMPONENT_IN_SCOPE","scope":"ROOT_GUARD_V2_PROBE_V3_PRIVATE_TARGETS_ONLY","source_handoff_ref":a["source_handoff_ref"],"source_manifest_ref":a["source_manifest_ref"],"root_original_tool_io_ref":a["root_original_io_ref"],"guard_source_ref":a["guard_source_ref"],"guard_source_independent_review_ref":a["guard_source_review_ref"],"invocation_ref":a["invocation_ref"],"closed_ref":a["closed_ref"],"actual_pid":41408,"actual_exits":{"root_outer":0,"root_parent_python":0,"owned_child_native":0},"actual_component_evidence_verified":True,"exact_job_inference_basis":a["exact_owned_child_basis"],"any_job_alone_is_insufficient":True,"held_handle_count":3,"guard_handle_cleanup":{"closed":True,"retained":0,"errors":[]},"owned_job_cleanup_confirmed":True,"actual_winerrors":{"write":32,"delete":32,"replacement":5},"same_path_replacement_before_after_success":True,"root_negative_events_are_expected_controls":True,"source_package_members_verified":13,"input_records":a["input_records"],"input_drift":0,"preserved_old_failed_probes":a["old_failed_probe_results"],"old_failures_recounted":False,"new_reviewer_tool_failures":0,"reviewer_native_WinAPI_calls":0,"reviewer_candidate_module_imports":0,"reviewer_SQL_provider_calls":0,"reviewer_Main_canonical_writes":0,"whole_controller_ready":False,"runtime_qualification":False,"execution_grant_issued":False,"formal_acceptance":False,"formal_case_increment":0,"audit_ref":ref(O/"bound-audit.json"),"report_ref":ref(O/"review.md"),"reviewer_original_io_ref":ref(O/"original-review-tool-io.json"),"open":["C4-R01_SOURCE_GUARD_LIFETIME_ON_UNCONFIRMED_JOB_CLEANUP","C5_PROPOSED_SOURCE_NOT_REVIEWED_HERE","ACTUAL_WHOLE_CONTROLLER_AND_TRUSTED_HOST_LIFECYCLE","SDK_QUALIFICATION_AND_FORMAL_TRIAL_NOT_EXECUTED"],"stopped":True}
write("review.json",review)
write("source-exit-integrity.json",{"input_records":len(a["rows"]),"input_refs":[r["source_ref"] for r in a["rows"]],"drift":[]})
print(json.dumps({"decision":review["decision"],"review_ref":ref(O/"review.json"),"report_ref":ref(O/"review.md"),"input_records":len(a["rows"]),"new_tool_failures":0},ensure_ascii=False,indent=2))

