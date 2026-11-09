from pathlib import Path
import hashlib,json,subprocess,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012'
AUTHOR=OUT.parents[1]/'desktop_managed_qualification_client_repair_v2_codex/20261012-current-chat'
PRIOR=OUT.parents[1]/'desktop_managed_qualification_client_review_codex/20261012-current-chat'
CANDIDATE='956225e98e17c1d9e15d4787fe4dd366a687d2e4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--short','-uno'],cwd=WT);assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'source-bundle-final.json')=='fdf4e87c764888799f1bf01a8042cd6d0792a1b1a9c237b92296e66f50df2874'
assert sha(AUTHOR/'receipt-manifest-final.json')=='d7294e8a5b4dec3b1f6c60545bcad506a5d2d0efb7253d4d27318c99c596d315'
assert sha(PRIOR/'receipt_manifest.json')=='ead81542d3840c6e6476d7776bfa84445739877c42081cd8075272896d62a4a9'
priorfiles={r['path']:r for r in read(PRIOR/'receipt_manifest.json')['files']}
priorrefs=[]
for name in ['independent-review.json','lifecycle-edges.mjs','lifecycle-dom.mjs','lifecycle-edge-results.json','lifecycle-dom-results.json','candidate-coupling-review1-result.json','candidate-coupling-review1-private-frames.json','default-smoke.stdout']:
    assert sha(PRIOR/name)==priorfiles[name]['sha256']
    priorrefs.append(dict(path=str(PRIOR/name),sha256=sha(PRIOR/name),bytes=(PRIOR/name).stat().st_size))
write('prior-frozen-evidence-references.json',dict(manifest_sha256=sha(PRIOR/'receipt_manifest.json'),references=priorrefs,note='References preserved in place; none rerun, relabeled or mutated.'))
binding=read(OUT/'input-verification.json');assert binding['checks']==binding['passed']==6501 and not binding['failures']
edges=read(OUT/'lifecycle-edge-results.json');assert len(edges['facts'])==7 and all(x['passed'] for x in edges['facts'])
dom=read(OUT/'lifecycle-dom-results.json');assert len(dom['facts'])==2 and all(x['repaired'] for x in dom['facts'])
for name in ['lifecycle-edges','lifecycle-dom','boundary','ui-v5-regression']:assert read(OUT/(name+'.invocation.json'))['exit_code']==0
assert 'tests 11' in (OUT/'boundary.stdout').read_text(encoding='utf-8')
assert 'tests 23' in (OUT/'ui-v5-regression.stdout').read_text(encoding='utf-8')
report=dict(
 schema='researchos.desktop-managed-client-independent-review/2',decision='ACCEPT',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',blocking_findings=[],
 candidate=CANDIDATE,base='fc350c97cddbf7d54e37b88ece25b0e8be8f1d87',cumulative_base='1c17662c4e4cc7058cd1d045ae0d55d9f75c3633',source_delta_files=5,cumulative_source_files=8,
 author_source_bundle_sha256=sha(AUTHOR/'source-bundle-final.json'),author_manifest_sha256=sha(AUTHOR/'receipt-manifest-final.json'),
 main_baseline=dict(head='d3a0fcaf506f1a3dd88f3f5d0a46f7bc1f0b56c1',checkpoint_revision=420,ownership_revision=208),
 closed_findings=[
  dict(id='W05-DMQ-CLIENT-001',priority='P2',status='CLOSED_SOURCE_AND_FIXTURE',repair='Validated unconfirmed original intent may retire only after genuine expiry, with no pending private command or consumed confirmation and with original native host identity intact. Original request identity/hash remain in frozen in-memory audit history.',source=['apps/desktop/main/lib/desktop-management.js:215-228','apps/desktop/main/lib/desktop-management.js:380-405'],independent_proof='Actual wall-clock expiry after session/generation change permits a second PREPARE for the new session, preserves original request/hash, sends zero CONFIRM; actual bound React DOM displays retired request and enables new confirmation.'),
  dict(id='W05-DMQ-CLIENT-002',priority='P2',status='CLOSED_SOURCE_AND_FIXTURE',repair='Every summary checks trusted native child/parent/discovery identity; mismatch is unavailable and unauthorized, retaining original request. IPC repeats summary after awaiting action. Returning host requires fresh original STATUS before current authorization.',source=['apps/desktop/main/lib/desktop-management.js:183-213','apps/desktop/main/lib/ipc.js:252-266','apps/web/src/workbench.jsx:214-225'],independent_proof='Direct and IPC current reads refuse changed host. Actual DOM clears old authorization after failed STATUS and remains unavailable on remount. Returning original host remains unauthorized until fresh STATUS; CONFIRM count remains one.')],
 validation=dict(binding='6501/6501 checks including all 6435 full build inputs, final five delta files, cumulative eight Git objects and bound source/modules/compiled assets; zero mismatches',build_input_digest=binding['build_input_digest'],validator_sha256=read(OUT/'bound-descriptor.json')['binary_sha256'],bound_boundary='11/11 directly copied candidate managed-boundary tests against final bound manager/IPC; no skip or failure; not relabeled as author 12/12',independent_causal='7/7 own cases; real short private timeout, late original response, expiry, context/host change, sticky consumed status, current IPC microtask and STATUS action-to-reply host switch',actual_chromium='2/2 original defect repairs using final bound React source component + bound IPC/manager + synthetic private frames; raw replies/DOM/screenshots retained and screenshots inspected',ui_v5_regression='23/23 selected native-host/configuration/prebuilder/ack boundaries against final bound validator'),
 invariants=['No expired-intent retirement while a private command is uncertain or pending. Original read-command terminal may release that read barrier; consumed CONFIRM remains irrevocable even after timeout, late reply and consumed:false STATUS.','Host mismatch cannot retire an expired intent, claim current availability, or reuse prior authorization. Both current and STATUS IPC response microtask switches fail closed.','Original public contract bytes, builder, main launcher and preload are unchanged from the prior reviewed candidate. Their exact cumulative Git/source/bound bytes were rechecked.','Original UI-v5 pre/post asynchronous host.status checks and monotonic write replay barriers remain present and passed necessary regression.'],
 prior_evidence='prior-frozen-evidence-references.json verifies original rejected report and counterexamples, zero-model real Core coupling and missing-resource smoke against the unchanged prior sealed manifest. No repeat Core/Electron startup was needed.',
 limitations=['Acceptance covers only source and fixtures, not full installed Desktop first-use, native model qualification, protected holdout or formal W05 acceptance.','The exact author build and all inputs were verified, not independently rebuilt. Chromium exercised bound React source through the reviewer component harness; compiled React asset hashes were verified but no new full compiled Electron smoke was run.','New private management frames and process identities are synthetic in-process fixtures. No actual model or Core process was launched this turn.','The earlier real Core coupling established only READY, OWNER_NOT_INITIALIZED PREPARE rejection and protocol shutdown; it is not qualification success.','Known Main production UNKNOWN-cost ledger drain refusal remains separately OPEN. This client repair does not change runtime_drain_windows.go or establish safe successful-qualification shutdown.','Retired intent audit is main-process memory only; process-restart persistence remains outside this client repair scope.','After native host recovery, remount/current refresh is needed before the UI can request fresh original STATUS; no periodic auto-confirmation or replay is introduced.'],
 history=['No failing independent test invocation in this review.','Targeted deletion of reviewer-owned vite-qualification-cache was rejected by automatic approval review: blocked by policy. Cache retained, excluded from manifest, and no alternate deletion attempted.'],
 actual_model_calls=0,external_calls=0,public_tunnel_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,
 modifications='Only this new independent receipt directory was written. Candidate tracked clean and author frozen manifests unchanged. No Source/Main/Canon/contracts/old receipts were modified.'
)
write('independent-review.json',report)
(OUT/'README.md').write_text('''# Desktop managed qualification client repair-v2 独立审查

**ACCEPT — SOURCE_AND_FIXTURE_ONLY**。候选 `956225e98e17c1d9e15d4787fe4dd366a687d2e4`，累计8文件、修复增量5文件。本轮未发现阻断项。

原 W05-DMQ-CLIENT-001 与 002 均关闭：真实 TTL 过期且无 CONFIRM/未决命令时可以在会话切换后准备新请求，并保留旧标识；主机切换后当前摘要和页面撤销旧授权，原主机回来仍须重新 STATUS。两项有实际 Chromium DOM 复测、原私有帧及截图。

6501/6501 绑定检查（6435完整构建输入及最终源码/Git/模块/UI资产）、11/11 bound 管理边界、7/7 新独立因果用例、2/2 DOM、23/23 UI-v5回归通过。未将作者声称的12项替代本轮实际11项。

原拒绝报告和反例保持冻结；旧零模型 Core 耦合与缺资源 smoke 用原清单复核引用，没有重跑，也没有升级证据层级。新构建未独立重建；本轮没有启动 Core/模型或完整 Electron。正常安装、真实资格调用、成功后 UNKNOWN 账本安全退出仍未接受；SOURCE+FIXTURE 接受不等于生产或正式验收。

0 actual model / external / public tunnel，formal/parent +0。候选和作者清单未改。新 Vite 缓存定向删除被自动审批审查 `blocked by policy` 拒绝，保留并排除清单，没有改用其他方式删除。
''',encoding='utf-8')
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
    p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
write('main-canon-end-observation.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only observation; concurrent parent work is outside reviewer write scope.'))
excluded={'vite-qualification-cache':'Retained cache: deletion blocked by policy.','test-temp':'Temporary runtime state excluded from evidence package.'}
files=[]
for p in sorted(OUT.rglob('*')):
    rel=p.relative_to(OUT)
    if p.is_file() and rel.parts[0] not in excluded and p.name not in ['receipt_manifest.json','review-seal.json']:
        files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write('receipt_manifest.json',dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',candidate=CANDIDATE,model_calls=0,external_calls=0,excluded_retained_runtime_roots=excluded,files=files))
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='ACCEPT',acceptance_scope='SOURCE_AND_FIXTURE_ONLY',files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
write('review-seal.json',seal);print(json.dumps(seal))
