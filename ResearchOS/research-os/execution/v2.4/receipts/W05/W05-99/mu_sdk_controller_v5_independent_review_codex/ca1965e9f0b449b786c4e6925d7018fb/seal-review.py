import ast,hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
a=json.loads((O/"intake.json").read_bytes());controls=json.loads((O/"independent-controls.json").read_bytes())
for row in a["rows"]:
 r=row["source_ref"];now=ref(pathlib.Path(r["path"]))
 assert now["sha256"]==r["sha256"] and now["bytes"]==r["bytes"]
controller=ast.parse(pathlib.Path(a["source_ref"]["path"]).read_bytes());observer=ast.parse(pathlib.Path(a["tuple"]["observer_source_ref"]["path"]).read_bytes())
launch=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
reconcile=next(n for n in controller.body if isinstance(n,ast.FunctionDef) and n.name=="reconcile_retained_sources")
obsvalidate=next(n for n in observer.body if isinstance(n,ast.FunctionDef) and n.name=="validate_source_review")
actorline=next(n.lineno for n in ast.walk(launch) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Call) and isinstance(n.left.func,ast.Attribute) and n.left.func.attr=="get" and n.left.args and isinstance(n.left.args[0],ast.Constant) and n.left.args[0].value=="actor_id")
findings=[
{"id":"C5-R01","priority":1,"title":"Current controller Source author can satisfy the independent review gates","source_ref":a["source_ref"],"line":actorline,"related_observer_ref":a["tuple"]["observer_source_ref"],"related_observer_line":obsvalidate.lineno,"source_author":a["source_author"],"counterexample":"Exact C5 gate and unchanged O3 validate_source_review both accept actor_id codex:/root/live_resource_lookup with otherwise correct schema/decision/callback/complete six refs/formal=false.","impact":"The actual C5 author may supply the review accepted as independent for this Source tuple; the old Root/w05 exclusion list no longer covers the current tuple authors.","requested_change":"Bind the current Source tuple authors at the pre-import admission boundary and reject any matching reviewer identity, including the C5 controller author. Preserve exact six-ref checks and ensure the observer path cannot be used to bypass that author binding.","control":"CURRENT_AUTHOR_PROVENANCE_codex:/root/live_resource_lookup","actual_runtime_executed":False},
{"id":"C5-R02","priority":1,"title":"Reconciliation releases retained protection from an unbound callback result","source_ref":a["source_ref"],"start_line":reconcile.lineno,"end_line":211,"counterexamples":["With current clock 100 and retained time 100, observed_monotonic=1000000 is accepted and releases both guard/watchdog.","A free callback returning matching run_uuid/owner_pid and a clean-looking native_result releases guard/watchdog and removes the resident record without any verified cleanup-producer source or retained Job/child identity. A foreign producer/Job marker is ignored because no such binding is present."],"impact":"The original unconfirmed-Job retention can be ended without evidence that its actual remaining consumers have terminated; dictionary shape and a lower-bound timestamp do not establish a fresh owned-Job observation.","requested_change":"Require an independently reviewed, exact-byte-bound cleanup producer that executes under retained Source protection (or implement the query internally in the reviewed module). Bind its proof to the actual retained Job and child PID/creation identity, not only the parent PID/run label. Validate a finite observation time within the fresh call's actual start/end window; retain all resources on any missing/mismatched provenance or cleanup field. Preserve the same-PID owner/residency prerequisite and do not turn recovery into a new model attempt or reset a deadline/budget.","controls":["RECONCILE_FUTURE_OBSERVATION_MUST_REJECT","RECONCILE_UNBOUND_CALLBACK_SOURCE_MUST_NOT_RELEASE"],"schema_note":"The foreign marker control demonstrates the absence of producer/Job binding; it does not claim those optional marker fields are part of the current published schema.","actual_runtime_executed":False}
]
fr=write("findings.json",{"decision":"REQUEST_CHANGES","findings":findings})
report="""C5 Controller 独立 Source 审查

结论：REQUEST_CHANGES，2 个 P1：C5-R01（当前作者可自签独立 review）与 C5-R02（reconcile 接受未绑定真实来源的 cleanup 字典，并接受未来时间）。不发 whole Source READY，不把本轮纯内存控制当成实际 Windows 生命周期证明。

C4 原问题的直接分支已经修复。结果为 None、仍有 active child、cleanup errors、active count 为 bool/float 时，Source guard 和 watchdog 均不 close，记录进入 RETAINED_UNCONFIRMED，强引用由当前 PID 的 sys-anchored owner 保留。outer finally 遇到中断的 NATIVE_INVOKED 也只 retain。PRE_NATIVE 能证明从未调用 native，允许清理；正常确认 cleanup 先在 Guard 内加载 canonical transaction，再关闭 Source guard。Guard/duplicate 清理失败时保留对象。owner 跨 PID 调用被拒绝；本机制只在该 PID 存活期间有效。

C5-R01：C5 handoff 的作者是 codex:/root/live_resource_lookup，但 controller 的 review actor 拒绝名单仍仅 Root/w05；O3 的拒绝名单同样没有当前 controller 作者。独立构造了其他全部字段和六 refs 合法的 review，两处实际 AST gate 都接受该作者。应在当前 tuple 的实际准入边界绑定所有 Source 作者，拒绝任一作者自行签发 independent review；不能只沿用上一版的作者名单。

C5-R02：reconcile 接受任意 callable，只检查返回值的 run_uuid、owner_pid、observed_monotonic>=retained 和 cleanup 字典形状。独立控制在 now=100、retained=100 时传入 observed=1000000，函数仍关闭 guard/watchdog 并删除 owner 记录。另一个完全未被审查或绑定到 retained Job 的 callable，只要返回同样的字典便能释放；附加 foreign producer/Job 标记也被忽略。这不是要求当前 schema 凭空支持某个字段，而是说明真实 cleanup 来源与 Job 身份根本没有进入强制条件。需要将已审、精确 pin、受 Source 保护的 producer 与 retained Job/child 身份绑定，并使用有限且落在本次 fresh call 开始至返回之间的时间；任何来源、身份或观测缺口都必须继续 retain。实际 Root 常驻进程和 producer 的未来 wiring 可以保持 LIVE_INTEGRATION_OPEN，但 Source 的释放接口本身必须先具备这些强制条件。

新增 26 项独立纯控制中 23 符合，3 个反例归上述 2 个 finding。控制只编译选定 AST 方法、finally 块和判断式，PID/时钟/RLock/sys/Guard/watchdog/transaction 都使用独立内存替身，没有真实线程、WinAPI 或 native 调用；callback 的形状阳性仅验证解析路径，不表示获得了实际 cleanup 证据。作者 20 项控制未执行、未当成独审。

C4 到 C5 的完整正逆 diff 均独立应用并精确恢复，五个 helper 字节不变；仅 cleanup_confirmed、close_canonical_lease、inner/outer launch 改动，并新增 resident owner/reconcile 支持。O3/v9 的原独审、Guard v2 的 31+28 控制及实际私有目标 probe 原封结果复用，未重跑 39/8/31/28 或任何 native probe。本轮 50 条输入记录无漂移，0 新增工具失败。作者 699-701 在 Source 包中是开发失败摘要，本审查不把该摘要冒充完整原 IO，也不重新计数。

六个 Source/Python refs 均非 NULL、按当前 C5/O3/v9/固定 Python 精确绑定。Main/canonical/SQL/provider 未触碰。实际 Root resident caller、fresh cleanup producer、完整 Controller/Host 生命周期、资格与正式 SDK trial 仍 OPEN。
"""
(O/"review.md").write_text(report,encoding="utf-8")
helpers={}
for n in controller.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF","SOURCE_READ_GUARD_REF","BASE_OWNED_PROCESS_REF"):
  helpers[n.targets[0].id]=ast.literal_eval(n.value)
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","actor_id":"codex:/root/command_queue_impl","source_author":a["source_author"],"decision":"REQUEST_CHANGES",**a["tuple"],"callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME","formal_acceptance":False,"execution_ready":False,"execution_grant_issued":False,"runtime_qualification":False,"additional_dependencies":list(helpers.values()),"source_handoff_ref":a["source_handoff_ref"],"source_manifest_ref":a["source_manifest_ref"],"prior_c4_review_ref":a["prior_c4_review_ref"],"actual_guard_probe_review_ref":a["actual_guard_probe_review_ref"],"reused_not_rerun":a["reused_prior_evidence_not_rerun"],"new_independent_controls":26,"matched":23,"counterexamples":3,"distinct_findings":2,"prior_c4_direct_unconditional_close_branch_fixed_in_source":True,"unconfirmed_cleanup_end_to_end_release_safety":"OPEN_C5_R02","resident_owner_scope":"SAME_PARENT_PID_ONLY_REQUIRES_ACTUAL_PARENT_LIVENESS","findings_ref":fr,"controls_ref":ref(O/"independent-controls.json"),"report_ref":ref(O/"review.md"),"original_tool_io_ref":ref(O/"original-tool-io.json"),"input_records":len(a["rows"]),"input_drift":0,"author_controls_executed":0,"new_tool_failures":0,"candidate_actual_entry_or_WinAPI_SQL_provider_calls":0,"real_threads_started":0,"Main_canonical_writes":0,"formal_case_increment":0,"open":["C5-R01_CURRENT_AUTHOR_REVIEW_IDENTITY","C5-R02_BOUND_FRESH_ACTUAL_JOB_CLEANUP_PROOF","ROOT_PARENT_RESIDENCY_AND_TRUSTED_CLEANUP_PRODUCER_INTEGRATION","ACTUAL_WHOLE_CONTROLLER_HOST_LIFECYCLE","NO_QUALIFICATION_OR_FORMAL_TRIAL"],"stopped":True}
assert all(review[k] is not None for k in a["tuple"])
write("independent-source-review.json",review)
write("source-exit-integrity.json",{"input_refs":[row["source_ref"] for row in a["rows"]],"records":len(a["rows"]),"drift":[]})
print(json.dumps({"decision":"REQUEST_CHANGES","review_ref":ref(O/"independent-source-review.json"),"findings_ref":fr,"report_ref":ref(O/"review.md"),"lines":{"C5-R01":actorline,"O3_related":obsvalidate.lineno,"C5-R02":reconcile.lineno},"new_tool_failures":0},ensure_ascii=False,indent=2))

