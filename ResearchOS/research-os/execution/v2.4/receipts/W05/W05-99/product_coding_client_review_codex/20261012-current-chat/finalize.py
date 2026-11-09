from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'product_coding_client_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-product-coding-client-20261012'
CANDIDATE='eb7f712d21268c87f9af9428048313c9361c52d6';BASE='b3ebbbfd03d3c32f9238403317ce29718e31d321'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip();(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'source-bundle-final.json')=='a30bf849cfd9f707ddcd188af15d17df012aeb58db9e93bb64129e38f62016b6'
assert sha(AUTHOR/'manifest.json')=='277d3d8885470dfd031d356e0273d384839fa2d3e871ce612f1d734bb03d1118'
b=read(AUTHOR/'source-bundle-final.json')
for row in b['source_files']:assert sha(WT/row['path'])==row['sha256']==sha(OUT/'source'/row['path'])
v=read(OUT/'input-verification.json');assert v['checks']==v['passed']==8183 and not v['failures']
facts=read(OUT/'counterexample-results.json')['facts'];assert len(facts)==3 and all(x['defect_reproduced'] for x in facts)
dom=read(OUT/'status-refresh-results.json');assert dom['defect_reproduced'] and dom['confirms']==1 and dom['refreshes']==0 and dom['page_errors']==[]
for label in ['counterexamples','boundary','dom']:assert read(OUT/(label+'.invocation.json'))['exit_code']==0
assert 'tests 6' in (OUT/'boundary.stdout').read_text(encoding='utf-8')
findings=[
 dict(id='W05-CODING-CLIENT-001',priority='P1',title='CONFIRM_CODING lacks the required privileged human confirmation',file='apps/desktop/main/lib/ipc.js',line_start=287,line_end=287,related=['apps/web/src/workbench.jsx:358','apps/desktop/main/lib/desktop-management.js:526'],
  trigger='After a valid PREPARE, a same-origin renderer invokes the exposed codingConfirm IPC directly without pressing the visible button or accepting any user dialog.',
  observed='The final bound IPC handler invokes manager.confirmCoding immediately; one CONFIRM_CODING frame with the main-held original request id/hash is sent and CODING_CONFIGURED returned. The only confirmation is renderer window.confirm. No privileged main-process dialog or independent consent gate exists.',
  impact='Renderer code can cause persistent workspace coding authorization without the required human review and privileged confirmation of that frozen scope. Hiding request id/hash does not prevent this because the no-argument confirm endpoint supplies them.',
  evidence=['counterexample-results.json:facts[0]','fixtures/renderer-confirm-without-privileged-consent/frames.json'],
  repair='Require main-process-owned explicit confirmation showing the exact frozen workspace, relative paths/checks/limits and selected resource identities. Cancellation must send zero CONFIRM. After the awaited native dialog, recheck original host/process/context/resource generation and shared pending state before consuming and sending the original request. Renderer-controlled booleans or window.confirm are insufficient.',
  scope_requirement='CP424: human frozen result review followed by explicit privileged confirmation.'),
 dict(id='W05-CODING-CLIENT-002',priority='P2',title='Expired coding intent is retired before the shared pending-command guard',file='apps/desktop/main/lib/desktop-management.js',line_start=479,line_end=484,related=['apps/desktop/main/lib/desktop-management.js:395','apps/desktop/main/lib/desktop-management.js:568'],
  trigger='An unconfirmed coding request expires by real wall-clock time and original STATUS confirms EXPIRED. A second STATUS remains in flight; another codingPrepare IPC arrives while that shared private command is pending.',
  observed='prepareCoding appends the original intent to retiredCodingIntents and sets codingIntent=null before exchange checks pending. It then throws MANAGEMENT_COMMAND_PENDING. The late STATUS resolves its captured old object while codingSummary now reports READY; subsequent original STATUS fails CODING_ORIGINAL_REQUEST_REQUIRED.',
  impact='The shared barrier blocks the new frame only after the active original request has already been discarded. Original-request recovery is unavailable while a coding/private operation is still unresolved, violating the same-pipe retention contract.',
  evidence=['counterexample-results.json:facts[1]','fixtures/expiry-retires-during-pending-status/frames.json'],
  repair='Check the single shared pending/uncertain barrier before any coding or qualification retirement or scope mutation. Keep the original intent active until the original terminal response is handled and all retirement conditions are revalidated; preserve consumed requests and historical evidence.',
  scope_requirement='CP424: shared coding/qualification/shutdown pending barrier; preserve uncertain/original intents and late status.',
  test_clock='Synthetic original response had 400 ms remaining lifetime; actual 450 ms wait used. No clock mocking or expiry-field mutation.'),
 dict(id='W05-CODING-CLIENT-003',priority='P2',title='A context change during PREPARE loses the returned original request',file='apps/desktop/main/lib/desktop-management.js',line_start=495,line_end=498,related=['apps/desktop/main/lib/desktop-management.js:520'],
  trigger='PREPARE_CODING is sent for session-1, selection changes to session-2 before the original valid response arrives, and later the user returns to session-1.',
  observed='The response resolves the shared pending operation, then sameContext throws before storing request_id/hash. codingIntent is null, retiredCodingIntents is empty, and no pending operation remains. Returning to session-1 cannot STATUS the original request and can send a second PREPARE while the first remains unexpired.',
  impact='The original frozen request is orphaned by an ordinary selection race; renderer remount cannot recover it, and the required original-request retained state is lost.',
  evidence=['counterexample-results.json:facts[2]','fixtures/prepare-response-context-change-drops-original/frames.json'],
  repair='Retain an operation record before dispatch, validate and store the original response independently from whether the current UI selection can use it, and expose a blocked context state rather than discarding original id/hash. A second PREPARE must not bypass the original retirement/recovery policy.',
  scope_requirement='CP424: changed host/session/writer/resource choice fails closed with original request retained.'),
 dict(id='W05-CODING-CLIENT-004',priority='P2',title='STATUS recovery of a committed configuration does not refresh the original V2 views',file='apps/web/src/workbench.jsx',line_start=291,line_end=295,related=['apps/web/src/workbench.jsx:488','apps/web/src/workbench.jsx:390'],
  trigger='CONFIRM has an uncertain/lost response. Explicit codingStatus then returns the original CODING_CONFIGURED result with the new model configuration.',
  observed='The final bound React component displays CODING_CONFIGURED, but onConfigured is called only when method===codingConfirm. Actual Chromium recorded confirms=1, refreshes=0 after STATUS recovery, with no page errors.',
  impact='The recovery path reports the new configuration while leaving the workbench host/configuration views on their earlier snapshot until some separate refresh. The explicit refresh promised after the original coding commit is missing on the path intended for lost replies.',
  evidence=['status-refresh-results.json','status-refresh.dom.html','status-refresh.png'],
  repair='Reconcile any authoritative original CODING_CONFIGURED result, including STATUS, through the original V2 view refresh without resending CONFIRM. Bind reconciliation to original host/project/session/generation and avoid applying the result to a changed selection.',
  scope_requirement='CP424: refresh original V2 session/configuration only after committed new config.')
]
report=dict(schema='researchos.desktop-coding-client-independent-review/1',decision='REQUEST_CHANGES',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',candidate=CANDIDATE,base=BASE,registered_paths=8,changed_source_paths=7,blocking_findings=findings,
 author_bundle_sha256=sha(AUTHOR/'source-bundle-final.json'),author_manifest_sha256=sha(AUTHOR/'manifest.json'),
 binding=dict(checks=8183,passed=8183,raw_receipts=1699,full_build_inputs=6439,build_input_digest='cd58b95dac4f960b5c17f210c1a1d195b78a773d9645ff4b4a5dae5d9d9bdf0a',validator_sha256='bb4c0225bd2a910870724e794eda9d397008623fafabd80b8c889d6beb1a4d54',exact_git_source_and_bound_modules=True,compiled_react_asset_hashes=True,independent_rebuild=False),
 tests=dict(independent_bound_positive_cases=6,positive_passes=6,positive_failures=0,positive_skips=0,independent_bound_manager_ipc_counterexamples=3,actual_chromium_bound_react_counterexamples=1,page_errors=[],actual_model_calls=0,actual_tool_calls=0,note='Counterexample exit code zero means asserted defects were reproduced; it is not a product PASS.'),
 author_evidence=dict(verified_by_frozen_census=True,desktop_cases=203,desktop_failures=0,desktop_skips=0,dom_cases=1,rerun_all=False,normal_electron_smoke_state='BROKEN',normal_electron_smoke_reason='INSTALLED_RESOURCE_UNAVAILABLE',interpretation='Original 203-case log and one synthetic DOM pass do not cover these four negative paths. The no-install Electron smoke is not an installed managed-Core success.'),
 reviewed_positive_boundaries=['Main restricts renderer field names to path/check/limit intent (the Core private contract validates relative-path values); trusted main derives selected project/session/model, desktop client id, current writer epoch/revision/workspace and host head plus one. Absolute toolchain/vendor paths are selected through native directory dialogs and kept in main.','Private request id/hash and authority fields stay in main; codingSummary exposes reduced human scope. Confirm marks confirmSent before sending, so timeout and repeated direct confirmation cannot issue a second CONFIRM.','The existing exchange retains uncertain pending state and checks native host/process identity pre/post response; coding IPC recomputes a current summary after awaiting an action. New retirement and prepare-response paths nevertheless lose original state as reproduced.','Startup stderr capture is bounded to 8192 bytes in privileged main; smoke output exposes only bytes/hash/truncation. No new renderer raw diagnostic channel was found.','Coding results preserve REGISTERED and model_calls=0; independent qualification remains a separate operation. Source/fixture results do not qualify model transport or tool execution.'],
 limitations=['No integrated Core-native coding coupling, full installed Electron first-use, real model/tool execution, protected holdout or formal W05 acceptance.','Parent-reported actual host.status revision-1 validator rejection and Native3 chooser NATIVE_INVALID_REQUEST are separate Main first-use blockers outside this seven-file source delta. This review neither repairs them nor counts them as this candidate defects.','Final full build inputs and compiled assets were verified, not independently rebuilt. Actual Chromium used final bound React source in the independent component harness; IPC/management counterexamples used final bound modules with synthetic private frames and native identities.','Root browser/Electron/control were not controlled, signaled, restarted or killed. No second coordinator was started.','The complete author 203-case suite and Core24 matrix were not rerun once decisive independent counterexamples were established.'],
 history=['No reviewer test invocation failed: six baseline cases pass and four negative assertions reproduce defects; all raw stdout/stderr and fixture frames are retained.','Scoped deletion of the new Vite cache was rejected by automatic approval review: blocked by policy. Cache retained and excluded, no alternate deletion attempted.','Reviewer accidentally created an empty file D:/作品集/ResearchOS/ research-os/__never_used__ (space before research-os), immediately deleted that exact empty file with apply_patch. Empty sibling directory removal was rejected by automatic approval review: blocked by policy; directory retained. This did not touch the real research-os repository.'],
 actual_model_calls=0,actual_tool_calls=0,external_calls=0,paid_calls=0,public_tunnel_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,
 modifications='All review artifacts are under the new receipt directory. Candidate tracked clean; Source/Main/Canon/contracts/old receipts unchanged. The unrelated accidental empty sibling directory is disclosed in history.'
)
write('independent-review.json',report)
(OUT/'README.md').write_text('''# Desktop coding client 独立审查

**REQUEST_CHANGES — Source + fixture**。候选 `eb7f712d21268c87f9af9428048313c9361c52d6`，登记8路径、实变7文件。

四项反例已复现并保留原始证据：

1. **P1 / 001：缺少主进程明确确认。** 同origin renderer可绕过页面确认，直接调用最终bound IPC发送原CONFIRM并得到CODING_CONFIGURED。
2. **P2 / 002：共享pending期间提前退役。** 原请求真实过期并STATUS确证后，第二STATUS尚未返回时prepare先清codingIntent，再报MANAGEMENT_COMMAND_PENDING；late reply之后已无法复核原请求。
3. **P2 / 003：PREPARE期间切会话丢原请求。** 原结果到达后在保存id/hash之前抛CONTEXT_CHANGED；返回原会话可另发PREPARE，旧id/hash不在active或history。
4. **P2 / 004：STATUS恢复提交结果未刷新V2视图。** 实际bound React DOM在确认结果不确定后复核得到CODING_CONFIGURED，但刷新回调仍为0。

8183/8183绑定检查通过，包含6439完整构建输入、1699冻结证据、7份Git源码及bound模块/UI资产。独立复跑原6个coding边界测试通过；另3个bound IPC/manager反例及1个实际Chromium DOM反例成立。负例脚本exit0表示成功复现缺陷，不表示候选通过。

本轮真实模型/工具/外部/付费/隧道调用0，formal/parent +0。没有控制主线程浏览器或进程。主线程现有host.status revision与Native3目录选择阻塞属于另行修复的真实首用支路，不归入本候选7文件，也不能据本轮宣布完整流程通过。

新Vite缓存定向删除被自动审批审查以 `blocked by policy` 拒绝，保留并排除清单。另一次误操作创建的仓库旁空文件已立即删除；残留带前导空格的空目录清理同样被拒绝，真实仓库未受影响。两项均未改用其他删除方式。
''',encoding='utf-8')
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status']})
write('main-canon-end-observation.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only; concurrent parent work outside reviewer scope.'))
accidental=ROOT.parent/' research-os';write('accidental-empty-directory-observation.json',dict(path=str(accidental),exists=accidental.exists(),children=[p.name for p in accidental.iterdir()] if accidental.exists() else [],original_empty_file_exists=(accidental/'__never_used__').exists(),real_repository_untouched=True))
excluded={'vite-coding-status-cache':'Retained Vite cache; scoped deletion blocked by policy.','test-temp':'Temporary baseline fixture root, excluded from evidence package.'}
files=[]
for p in sorted(OUT.rglob('*')):
 rel=p.relative_to(OUT)
 if p.is_file() and rel.parts[0]not in excluded and p.name not in ['receipt_manifest.json','review-seal.json']:
  files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write('receipt_manifest.json',dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='REQUEST_CHANGES',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',candidate=CANDIDATE,model_calls=0,excluded_retained_runtime_roots=excluded,files=files))
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='REQUEST_CHANGES',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
write('review-seal.json',seal);print(json.dumps(seal))
