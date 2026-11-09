import datetime,hashlib,json,pathlib,shutil
E=pathlib.Path(__file__).resolve().parent;R=E.parents[6]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
pins=read(E/'input-pins.json');assert all(sha(pathlib.Path(p['path']))==p['sha256'] for p in pins)
live=read(E/'live-readonly-observation.json');idle=read(E/'live-readonly-global-idle.json')
assert live['consumption']==[] and live['runtime_runs']==[] and live['task'][0]['status']=='DRAFT'
assert all(v==[{'count':0}] for v in idle['results'].values())
a=R/'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry10_codex/20261014-current-chat'
(E/'raw').mkdir()
for name in ['07-qualification-prepared.ui.txt','08-new-qualification-prepared.ui.txt','09-qualification-confirm-click.json','10-after-confirm.ui.txt','11-qualification-dialog-accepted.json','12-qualification-in-progress.ui.txt','14-original-status.ui.txt']:
    shutil.copyfile(a/name,E/'raw'/name)
put('readonly-invocations.json',[dict(actualargv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-X','utf8',str(E/name)],cwd=str(R),native_exit=0,output_ref=ref(E/out),tool_output_captured=True) for name,out in [('observe.py','live-readonly-observation.json'),('supplement.py','live-readonly-global-idle.json')]])
timeline=[dict(event='request issued',at='2026-10-13T19:30:28.7383996Z'),dict(event='preconfirm read-only observation',at='2026-10-13T19:30:49.532254Z'),dict(event='actual browser dialog accepted once',at='2026-10-13T19:31:25.969Z'),dict(event='request expires',at='2026-10-13T19:31:28.7383996Z'),dict(event='writer lease expires',at='2026-10-13T19:31:51.8266886Z'),dict(event='after-confirm read-only observation',at='2026-10-13T19:32:13.248307Z')]
put('timeline.json',dict(events=timeline,request_TTL_seconds=60,request_remaining_at_dialog_accept_seconds='2.7693996',writer_remaining_at_dialog_accept_seconds='25.8576886',private_frame_send_receive_times='not recorded',UI_status_result='EXPIRED',DB_request_consumed=False))
sources=[dict(path='source/apps/desktop/main/main.js',line=215,fact='PREPARE checks fresh Desktop writer ownership and expiry'),dict(path='source/apps/desktop/main/lib/desktop-management.js',line=197,fact='New Main management instance has null intent'),dict(path='source/apps/desktop/main/lib/desktop-management.js',line=312,fact='Retirement requires confirmSent false'),dict(path='source/apps/desktop/main/lib/desktop-management.js',line=524,fact='CONFIRM sets one-shot confirmSent before exchange; any non-RESULT becomes generic CONFIRM_REJECTED_CHECK_STATUS'),dict(path='source/apps/desktop/main/lib/desktop-management.js',line=560,fact='STATUS does not clear already-true confirmSent when consumed false'),dict(path='source/internal/host/desktop_management_windows.go',line=182,fact='Host collapses operation errors into MANAGEMENT_REJECTED and sends e.Error in private message'),dict(path='source/internal/host/desktop_management_windows.go',line=250,fact='CONFIRM validates original request before Host qualification'),dict(path='source/internal/domain/runtime_qualification_confirmation_windows.go',line=25,fact='Strict original wallclock deadline checked in confirmation validation'),dict(path='source/internal/domain/runtime_qualification_confirmation_windows.go',line=118,fact='STATUS marks EXPIRED independently of failure cause; consumption read separately'),dict(path='source/internal/domain/runtime_qualification_execution_windows.go',line=219,fact='Wallclock deadline rechecked after claim gates before consumption; rollback on expiry'),dict(path='source/internal/domain/runtime_qualification_execution_windows.go',line=233,fact='Fresh PREPARE produces new ID and 60s deadline when task remains DRAFT'),dict(path='source/internal/host/runtime_qualification_windows.go',line=157,fact='Host window, identity, full validation, verifier startup and provenance precede atomic execution claim'),dict(path='source/internal/domain/runtime_qualification_confirmation_windows.go',line=260,fact='Restart derives durable unresolved fence from consumed requests and runs/effects')]
report=dict(schema='researchos.qualification-rejection-independent-diagnosis/1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='codex:/root/attach_review_resume',verdict='ORIGINAL_EXPIRED_UNCONSUMED_FRESH_PREPARE_RECOVERY_SUPPORTED',qualification_request_id='1b4a119026c64f0347984bbc69862763',facts=['original request exists, expired and unconsumed','matching runtime has no qualification Run; Task DRAFT with null active_run_id','original coding c671505 remains CODING_CONFIGURED with new model ref mc-3f9329b391eaca14d82e7c4d3b9b6f34 and runtime db26746ff0420ca156d315f0de00fb53','writer lease was not expired at recorded dialog acceptance','global durable unresolved Runs/effects/dispatches/managed requests are all zero at independent snapshot','Desktop confirmSent latch remains true after STATUS consumed=false; retirement disallowed in that same Main instance'],causality=dict(proven='a private CONFIRM received a non-RESULT response before one-shot state was left UNRESOLVED; exact private error was not retained',leading_inference='deadline crossed during remaining Main identity checks / Host checks / verifier preparation / final transaction; only 2.7693996 seconds remained',not_proven=['precise rejected Core error or failing gate','exact private frame transmission, reception and deadline-check times','that no verifier process or administration artifact was created before refusal','absence of all non-consumption Host-side administrative effects']),recovery=dict(source_fix_required_for_attempt=False,normal_restart_supported=True,conditions=['Root normal shutdown and reopen same accepted package with original data location','retain original request, failure count and immutable coding/configuration records','reopen exact original session and confirm newref persists; acquire fresh writer authority before PREPARE','use only one newly prepared request with new ID/hash/deadline; promptly accept matching dialog with substantial TTL remaining','never resubmit expired original request or repeat committed coding CONFIRM','all ordinary runtime/Host/Owner/profile/budget/provider gates remain authoritative and may still refuse'],reason='Unconsumed expired confirmation is provenance, not a queued Run; new Main clears only volatile one-shot intent, while durable consumed-request fences remain enforced. Current durable census has no unresolved work.',success_not_guaranteed=True),source_fix_candidates_not_implemented=['Optional UX recovery for authoritative EXPIRED consumed=false while never reenabling the original CONFIRM','Optional bounded private error observability and TTL visibility; no evidence justifies extending or bypassing authorization TTL'],source_core='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2',source_desktop='c8b7adab9f0c15eb33f235f8d0d9eb205794e376',source_evidence=sources,db_snapshots=[ref(E/'live-readonly-observation.json'),ref(E/'live-readonly-global-idle.json')],database_mutations=0,GUI_actions=0,API_calls=0,CONFIRM_calls=0,new_requests=0,model_calls=0,formal_increment=0,tests='No code changed; read-only evidence and production-source inspection only',input_drift=[],source_stop_read_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
put('FINAL-report.json',report)
(E/'REVIEW.md').write_text('''# Qualification 拒绝的独立只读诊断

结论：原请求 `1b4a119026c64f0347984bbc69862763` 已过期且未消费。当前证据支持 Root 正常重开同一包、保留原数据与已保存配置，然后准备一个新请求；**恢复尝试不以源码修复为前提**。这不是对下一次资格运行成功的承诺，也不能重发原请求。

## 已确认事实

- 两份已固定 observer 与本轮只读 SQLite 快照一致：session revision 4、writer epoch 2、writer `desktop-shell`，原 coding `c671505` 保持 `CODING_CONFIGURED`，model ref 为 `mc-3f9329b391eaca14d82e7c4d3b9b6f34`。本轮没有改动配置。
- 请求消费表无原 request 行；该 runtime 无 qualification Run；Task 为 DRAFT、active_run_id 为 null。全库未结算 Run、最新未决 effect、未决 dispatch、managed qualification 持久化围栏计数均为 0。这个结论不代表所有 Host 行政副作用都没有发生，也不证明 verifier 从未启动。
- 弹窗实际接受时间为 19:31:25.969Z。写租约直到 19:31:51.8266886Z，尚余 **25.8576886 秒**，所以“接受确认前租约已经过期”不符合记录。
- 原请求仅有效至 19:31:28.7383996Z，接受时只剩 **2.7693996 秒**。19:32:13 的 observer 及后续原 STATUS 均显示过期未消费。

## 原因界限

实际 Core `a7ec7ebf` 会在 LoadLocalConfirmation、Host ValidateLocalQualification、beginManagedLocalQualification 及最终 claim 完成后检查原始 deadline。Host 校验身份、启动 verifier 和记录 provenance 位于最终 claim 之前。跨过剩余不足 3 秒的期限，是有依据的优先推断。

但 private ERROR 原帧没有留存。Desktop `c8b7adab` 将非 RESULT 笼统映射为 `CONFIRM_REJECTED_CHECK_STATUS`；Host 原错误消息只存在于 private reply。后续 STATUS 的 EXPIRED 仅证明读取时已过期，不会反推出原拒绝原因。因此不能宣称捕获了 STALE_INPUT、LEASE_EXPIRED、某个 verifier 错误，或精确失败时刻；其他 Host、配置、工作区、verifier、预算门仍是未排除的可能原因。

## 为什么当前页面不能重新准备

Main 在发送 CONFIRM 前把 `confirmSent` 置 true；STATUS 只会把它置 true，不会在 `consumed=false` 时清除。`canRetireExpiredIntent` 必须满足 `!confirmSent`。因此原 STATUS 已明确 EXPIRED 后，当前 Main 仍保留单次发送状态并禁用重新准备。这与本轮观察一致。

新 Main 实例的 `intent` 初始为 null；Core 新 PREPARE 只在当前身份、配置和 DRAFT task 等条件通过后创建新 ID 与新 60 秒期限。过期未消费记录不会自动排队执行。持久化已消费/未决 Run 的围栏仍由 Core 从数据库恢复，不因重启消失。当前只读计数没有这种未决工作，所以正常重开后新准备是合法恢复路径。

## Root 后续范围

正常退出并重开已接受包与原 data location，打开原会话、核对保存的新 model ref，再取得当前写入权；准备一个全新的 qualification request，并在充足有效期内只确认该新请求一次。保留旧请求和失败历史。不要重发 `1b4a119`，不要重复已提交的 coding `c671505`，不要改数据库、旧期限或原消费记录。

源码可以另做 UX 改善：在权威 STATUS 证明 EXPIRED 且未消费时允许明确准备新请求、展示剩余期限或保留受限错误信息；这些不是此次恢复的必要补丁。本轮没有实现或测试这些改动，也未重新验证完整当前 admission 或 provider 可用性。

证据：`live-readonly-observation.json`、`live-readonly-global-idle.json`、`historical-safe-fields.json`、`timeline.json`、`raw/` 和固定版本 `source/`。所有数据库连接使用 URI mode=ro、PRAGMA query_only=ON、BEGIN/ROLLBACK；未输出 owner token/credential。GUI/API/CONFIRM/新请求/模型调用/DB 写入均为 0，正式验收增量 0。源码行号索引见 FINAL-report.json。
''',encoding='utf-8',newline='\n')
files=[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
put('FINAL-manifest.json',dict(schema='researchos.independent-diagnosis-manifest/1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),count=len(files),members=files))
print(json.dumps(dict(report=ref(E/'FINAL-report.json'),review=ref(E/'REVIEW.md'),manifest=ref(E/'FINAL-manifest.json'),count=len(files),source_stop_read_at=report['source_stop_read_at']),ensure_ascii=False))
