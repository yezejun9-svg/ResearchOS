import ast,hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
def ref(p,b=None):
 b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(name,x):
 p=O/name;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
intake=json.loads((O/"intake.json").read_bytes());extra=[]
def readref(expected):
 p=pathlib.Path(expected["path"]);b=p.read_bytes();r=ref(p,b)
 assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"]
 snapshot=O/(r["sha256"]+".raw")
 if not snapshot.exists():snapshot.write_bytes(b)
 extra.append({"source_ref":r,"snapshot_ref":ref(snapshot,b)})
 return b
gdir=B/"source_read_guard_v2_independent_review_codex/9697417e746d47d9abea9289d56db2f1"
greviewref={"path":str(gdir/"review.json"),"sha256":"e93fe5a0e2e2d3b6c18732c7259d75a6d922ab7d31e48ee75e4c2b41f84c7831","bytes":1585}
greview=json.loads(readref(greviewref))
gm=json.loads(readref({"path":str(gdir/"manifest.json"),"sha256":"28d06507c0121ad7dc8dd89d046ea4e2eac74f2174779e10e59f5ce3de60139c","bytes":8832}))
assert any(m["sha256"]==greviewref["sha256"] and m["bytes"]==greviewref["bytes"] for m in gm["members"])
readref(greview["controls_ref"]);readref(greview["source_manifest_ref"]);readref(greview["source_ref"])
assert greview["decision"]=="PASS_SOURCE_ONLY" and greview["source_ref"]==intake["helper_refs"]["SOURCE_READ_GUARD_REF"]
source=pathlib.Path(intake["tuple"]["controller_source_ref"]["path"]).read_bytes();tree=ast.parse(source)
inner=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_launch_reviewed_phase_with_guard")
outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
close_lines=[n.lineno for n in ast.walk(inner) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=="source_guard" and n.func.attr=="close"]
outer_close=[n.lineno for n in ast.walk(outer) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=="guard" and n.func.attr=="close"]
finding={"id":"C4-R01","priority":1,"prior_finding":"V3-R03","status":"REQUEST_CHANGES","title":"Unconfirmed Job cleanup releases Source read guards while consumers may remain live","source_ref":intake["tuple"]["controller_source_ref"],"lines":close_lines+outer_close,"trigger":"run_owned returns cleanup with active_processes_last_observed=1, job_idle_confirmed=false, handles_closed=false, or no native result is available after child creation.","observed":"Both inner and outer finally call close() unconditionally. Pure exact-AST controls show source_guard.held false while live-child cleanup remains unconfirmed. Canonical lease retention does not retain deny-write/deny-delete source handles.","impact":"A still-live child may load or reload phase worker, runner or helper paths after immutable-source protection has been removed; the full reviewed Source tuple is not held through all consumer lifetimes.","evidence_controls":["LIVE_CHILD_UNCONFIRMED_JOB_MUST_KEEP_SOURCE_GUARD","MISSING_NATIVE_RESULT_MUST_NOT_RELEASE_POSSIBLY_LIVE_SOURCE_CONSUMERS"],"basis":"Base owned-process helper can return cleanup errors/unconfirmed Job idle after its bounded cleanup deadline, so this is an explicit supported failure path, not a claimed actual native failure.","requested_change":"Retain the guard and its owning controller state on every unconfirmed cleanup path. Release only after independently evidenced child-tree termination/Job idle and required handle cleanup, using an explicit bounded recovery/owner-lifetime contract; avoid unconditional outer finally close. Preserve lease and cleanup evidence without automatic retry or renewed trial budget.","native_reproduced":False,"proof_scope":"Exact finalization AST with memory guard and supplied cleanup states; no real Job, WinAPI, thread or source-file mutation."}
fr=write("findings.json",{"decision":"REQUEST_CHANGES","findings":[finding]})
reg=json.loads((O/"regression-controls.json").read_bytes());wrap=json.loads((O/"wrapper-controls.json").read_bytes())
rows=intake["rows"]+extra
for row in rows:
 r=row["source_ref"];n=ref(pathlib.Path(r["path"]))
 assert r["sha256"]==n["sha256"] and r["bytes"]==n["bytes"]
f695=json.loads((O/"failure-origin.695.json").read_bytes());f695["original_script_snapshot_ref"]=ref(O/"intake.failed-original.py")
write("failure-origin.695.json",f695)
write("source-exit-integrity.json",{"rows":rows,"input_records":len(rows),"unique_paths":len({r["source_ref"]["path"] for r in rows}),"drift":[]})
report="""C4 + O3 完整 Source 组合独立审查

结论：REQUEST_CHANGES，剩余 1 个 P1 问题 C4-R01。六个 Source/Python 引用均为本次核验的完整非 NULL pin；本结论没有发放 READY 或执行权限。

C4-R01：当 native 结果显示 active_processes_last_observed=1、job_idle_confirmed=false、handles_closed=false 时，inner finally 仍调用 source_guard.close()，outer finally 再次调用 close()。没有 native 结果的分支也如此。两个纯 AST 反例均确认锁已释放。canonical lease 保留不能代替 Source 文件句柄的保留；可能仍活跃的子进程随后通过路径加载代码时，已失去 deny-write/deny-delete 保护。必须把 guard 和所属 owner 状态保留到 child tree/Job 结束得到确认，再通过明确恢复流程释放，不能由外层 finally 无条件释放。

既有修复有效：复用了上一轮独立内存事务 fixture，真正模拟 close 的第二次文件写入失败，使 CP 已清 active、OW 仍 ACTIVE；使用当前 refs 再准入被 C4 拒绝，canonical bytes 不再被第二次调用覆盖。两种一致的 CLOSED 状态允许准入，UUID 不一致、缺失和畸形记录拒绝。watchdog Thread.start 失败后不再 join 未启动线程，duplicate 可以关闭并保留失败原因；stop_and_close 异常被 controller 记录，不再阻断后续 cleanup 记录路径。

C4 wrapper 的 17/17 新独立控制通过：六个完整引用及五个附加引用合计 11 个锁定对象在 inner 前取得，拒绝错误 reviewer、旧 schema、REQUEST_CHANGES、formal acceptance、未准备 phase、错 runner/observer/Python/controller/hooks/worker、取得 guard 失败和 review 在取得 guard 前变化。回归控制 15 项中 13 符合、2 个反例归同一个 P1 finding，共 32 项新独立控制、30 符合。

O3 与 O2 的完整函数字节一致，仅 RUNNER_REF 的 path/hash 改为 v9；独立正逆字节恢复精确，其他 AST 一致。O2 既有 39 项及 v9 已封存 8 项控制复用，未重跑。C4 controller/watchdog diff 独立重新生成完全相同，其余 transaction/hooks/phase_worker/job_probe_helper 原始字节不变。

SourceReadGuard v2 的非作者 PASS_SOURCE_ONLY 已按其 review、manifest、controls 和 Source pin 核验并作为附加证据：31 个新内存控制、28 个既有控制复用。本轮没有把作者控制当成独立结论；guard 自身的 Source PASS 不证明 C4 的持有期正确，也不证明真实 Windows API 行为。

本轮自身新增工具失败 694（误含空格的只读规则路径，shell=1，Python/native NULL）和 695（元数据 intake 用错 C3 HDF 字段，shell=1、Python=1、产品 native NULL），完整调用/原始返回及失败脚本均封存。693 属其他 agent 的协作路由失败，无本轮原始证据，不伪造或重复计数。此前 690/691 已封存在 v9 审查中，本轮不再计数。

所有动态控制仅运行选定 AST 与独立内存路径、句柄、线程、时钟及 transaction 替身。没有候选模块导入、真实 WinAPI/线程/native/SQL/provider 执行；Main/canonical 未写。实际 Windows 私有目标 probe、实际 Job 生命周期、可信 Host、资格和正式 trial 保持 OPEN。
"""
(O/"review.md").write_text(report,encoding="utf-8")
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"REQUEST_CHANGES","actor_id":"codex:/root/command_queue_impl",**intake["tuple"],"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False,"execution_ready":False,"execution_grant_issued":False,"additional_dependencies":list(intake["helper_refs"].values()),"prior_review_refs":intake["prior_review_refs"],"source_guard_independent_review_ref":greviewref,"source_guard_independent_controls_reused":{"new_memory_controls":31,"prior_memory_controls":28,"rerun":0},"prior_observer_39_controls_reused_not_rerun":True,"prior_v9_8_controls_reused_not_rerun":True,"findings_ref":fr,"report_ref":ref(O/"review.md"),"controls_refs":[ref(O/"regression-controls.json"),ref(O/"wrapper-controls.json")],"new_independent_cases":32,"matched":30,"counterexamples":2,"distinct_findings":1,"old_issue_status":{"V3-R01":"CLOSED_SOURCE_IN_SCOPE_PARTIAL_TRANSACTION_NEW_ADMISSION_REJECTED","V3-R02":"CLOSED_SOURCE_IN_SCOPE_START_AND_CLEANUP_EXCEPTIONS_HANDLED","V3-R03":"NORMAL_PATH_HELD_SOURCE_FIXED_UNCONFIRMED_JOB_LIFETIME_OPEN"},"input_records":len(rows),"input_drift":0,"candidate_actual_entry_or_WinAPI_SQL_provider_calls":0,"real_threads_started":0,"canonical_Main_writes":0,"new_tool_failures":2,"root_assigned_failure_numbers":[694,695],"failure_origin_refs":[ref(O/"failure-origin.694.json"),ref(O/"failure-origin.695.json")],"open":["C4-R01_SOURCE_GUARD_LIFETIME_ON_UNCONFIRMED_JOB_CLEANUP","ACTUAL_OS_LOCKS_JOB_AND_CONTROLLER_LIFECYCLE","TRUSTED_HOST_WHOLE_TRIAL_LIFECYCLE","NO_RUNTIME_GRANT_OR_QUALIFICATION_ISSUED"],"stop_after_review":True}
assert all(review[k] is not None for k in intake["tuple"])
write("independent-source-review.json",review)
print(json.dumps({"decision":review["decision"],"finding_lines":finding["lines"],"review_ref":ref(O/"independent-source-review.json"),"report_ref":ref(O/"review.md"),"findings_ref":fr,"input_records":len(rows),"failure_origin_refs":review["failure_origin_refs"]},ensure_ascii=False,indent=2))

