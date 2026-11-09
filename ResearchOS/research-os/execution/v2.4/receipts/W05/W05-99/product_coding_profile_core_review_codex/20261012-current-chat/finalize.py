from pathlib import Path
import hashlib,json,subprocess,datetime,re
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-product-coding-profile-core-20261012'
AUTHOR=OUT.parents[1]/'product_coding_profile_core_codex/20261012-current-chat'
CANDIDATE='860a8935c8fffe4a1671eafa177e7fc5a053158a'
BASE='d3a0fcaf506f1a3dd88f3f5d0a46f7bc1f0b56c1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()==CANDIDATE
status=subprocess.check_output(['git','status','--porcelain'],cwd=WT);assert not status.strip()
(OUT/'candidate-tracked-status.txt').write_bytes(status)
assert sha(AUTHOR/'source-bundle-final.json')=='ab1dfa48850183a28a9a9220b5d8fdb565b2443379abba607e6b7bd05d052208'
b=read(AUTHOR/'source-bundle-final.json');binding=read(OUT/'input-verification.json')
assert binding['checks']==binding['passed']==186 and not binding['failures']
for row in b['source']['source_files']:
 assert sha(WT/row['path'])==row['sha256']==sha(OUT/'source'/row['path'])
for row in b['receipts']:assert sha(AUTHOR/row['path'])==row['sha256']
pathrows=[]
for pointer,value,expected in [('/worktree',b['worktree'],WT),('/source/worktree',b['source']['worktree'],WT)]+[(f'/builds/{i}/path',r['path'],ROOT/'.local/builds/product-coding-profile-core-20261012'/Path(r['path']).name) for i,r in enumerate(b['builds'])]:
 p=Path(value);assert p.exists() and p.samefile(expected)
 pathrows.append(dict(json_pointer=pointer,decoded_path=value,exists=True,samefile_expected=True,expected_path=str(expected),first_directory_codepoints=[ord(c) for c in value[3:6]]))
literal=[]
def walk(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():walk(x,p+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,p+'/'+str(i))
 elif isinstance(v,str) and re.search(r'\\u[0-9a-fA-F]{4}',v):literal.append(p)
walk(b);assert not literal
write('bundle-path-audit.json',dict(author_bundle_sha256=sha(AUTHOR/'source-bundle-final.json'),direct_json_loads=True,normalization_applied=False,paths=pathrows,literal_unicode_escape_strings=literal,note='All original decoded pointers are valid. Chinese characters are actual Unicode codepoints, not literal backslash-u text. Earlier native() helper was a no-op for these fields.'))
counts=[]
for label,parents,subs in [('regression',37,104),('native',4,0),('additional',3,10)]:
 inv=read(OUT/(label+'.invocation.json'));assert inv['exit_code']==0
 events=[]
 for line in (OUT/(label+'.stdout')).read_bytes().splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 terminal=[x for x in events if x.get('Action') in ['pass','fail','skip']]
 assert terminal==read(OUT/(label+'.summary.json'))
 gotparents=sum(x.get('Action')=='pass' and 'Test' in x and '/' not in x['Test'] for x in terminal)
 gotsubs=sum(x.get('Action')=='pass' and '/' in x.get('Test','') for x in terminal)
 assert (gotparents,gotsubs)==(parents,subs) and all(x['Action']=='pass' for x in terminal)
 counts.append(dict(label=label,parent_passes=parents,subtest_passes=subs,failures=0,skips=0,exit_code=0))
history=[]
for name in ['additional-attempt1','additional-attempt2']:
 inv=read(OUT/name/'additional.invocation.json');assert inv['exit_code']!=0
 history.append(dict(path=name,exit_code=inv['exit_code'],preserved_files=sorted(p.name for p in (OUT/name).iterdir()),classification='REVIEWER_FIXTURE_FAILURE_NOT_CANDIDATE_DEFECT'))
write('test-results.json',dict(final_invocations=counts,parent_passes=44,subtest_passes=114,failures=0,skips=0,preserved_failed_attempts=history,actual_model_calls=0))
native=(OUT/'native.stdout').read_text(encoding='utf-8')
for marker in ['private_coding=true','qualification=1MODEL/0TOOL','normal_model=5','tools=4','UNKNOWN_null=6','private_SHUTDOWN=accepted','release=refused','ledgers=unchanged','generation=1','generation=2']:assert marker in native
report=dict(
 schema='researchos.product-coding-core-independent-review/1',decision='ACCEPT',acceptance_scope='SOURCE_AND_NATIVE_SYNTHETIC_FIXTURE_ONLY',blocking_findings=[],
 candidate=CANDIDATE,base=BASE,source_paths=24,registered_paths=30,author_source_bundle_sha256=sha(AUTHOR/'source-bundle-final.json'),
 input_validation='186/186 verified checks: six registered scope documents, 24 exact Git/worktree/source objects, unchanged author raw receipts and final binaries. All final raw Go results reconstructed independently; no skipped tests promoted to passes.',
 binary_validation=dict(control_sha256='5ff666d91891fc1005d4b619646342bea48f256ea070b5e94aa873a4a98ac543',runtime_verifier_sha256='0a0c4d78eabc8fdeb2f0a16a6e80d6c5c7aef8f3606f9b63d4ec85abddd8c0e8',vcs_revision=CANDIDATE,vcs_modified=False,independent_rebuild=False),
 pointer_validation='Original json.loads worktree/source.worktree/build paths directly exist and samefile expected locations. Unicode display concern was not a malformed pointer; no correction or normalization needed. See bundle-path-audit.json.',
 tests=counts,independent_total=dict(parent_passes=44,subtest_passes=114,failures=0,skips=0),
 native_evidence=[
  'Actual Host, inherited private management pipe, Mu AppContainer and independent verifier process with synthetic loopback SSE provider. Private coding PREPARE/CONFIRM installs new configuration bound to original selected session.',
  'Coding integration: one synthetic qualification MODEL and zero TOOL effects; normal turn uses five synthetic MODEL responses and four actual Host tools: read, edit, write and offline Go run_check. Actual fixture files changed, check receipt exit_code=0, children stopped, streams drained and cleanup complete.',
  'Two runs settled; six UNKNOWN/null cost rows remain unchanged. Private SHUTDOWN accepted while release remains refused. Original synthetic model-only and lost-reply cases also passed; ten total synthetic SSE responses across native integration cases, zero real model calls.',
  'Exact frozen control.exe launched through actual inherited management pipe for two generations with the same host identity and protocol-confirmed exit=0 (recorded child PIDs 59464 and 65892); no force kill.'
 ],
 additional_independent_evidence=[
  'Four freeze-time changes: selected-session writer epoch, workspace revision, owner authority revoked and genuine wall-clock confirmation expiry. All refused without installing a new coding model/profile.',
  'Six Desktop-exit proof gaps: streams not drained, cleanup incomplete, missing STARTED effect stage, foreign receipt epoch, foreign context bundle, and unavailable immutable-version store. All remain blocked and preserve ledger bytes. The final unavailable-store fixture renames its isolated test database table; it does not mutate immutable dispatch or evidence records.',
  'Persisted coding authorization cannot be silently downgraded to legacy model-only behavior by removing coding_authorization from the loaded profile.'
 ],
 source_review=[
  dict(area='PREPARE and CONFIRM',references=['internal/domain/client_runtime_coding_windows.go:172','internal/domain/client_runtime_coding_windows.go:280'],result='Exact read/write paths and check inventories bound to session/workspace/owner/epoch/current configuration; confirmation rechecks before and after external freeze; configuration CAS and new immutable authorization/profile/plan installation occur in one transaction.'),
  dict(area='Qualification and tool authority',references=['internal/domain/runtime_routes_windows.go:83','internal/domain/runtime_tools_windows.go:61','internal/domain/runtime_tools_windows.go:153'],result='Qualification provider route remains one MODEL call and tool effects are allowed only for mu_turn. Normal coding profile allows up to eight MODEL and 32 TOOL effects. Workspace authority checked during admission and again before physical tool effect; no implicit authority downgrade.'),
  dict(area='Offline Go checks and native receipts',references=['internal/host/runtime_check_windows.go:443','internal/host/runtime_check_windows.go:561'],result='Explicit frozen source/helper/embed/import inventories and toolchain/vendor constraints; isolated scratch staging, native Go sandbox check, empty EOF producer result remains an empty array, CreatedNs serialized as exact decimal string.'),
  dict(area='Safe Desktop shutdown',references=['internal/domain/runtime_drain_windows.go:54','internal/domain/runtime_drain_windows.go:132','internal/domain/runtime_drain_windows.go:176'],result='Desktop-only completed-local-unknown classifier requires terminal native proof, frozen dispatch/profile, complete matching effect history and original unlimited local budget chain. Original UNKNOWN/null ledger bytes remain unchanged; release continues using strict drain.'),
  dict(area='Zero launch holds',references=['internal/domain/budget_scopes.go'],result='Report/cancel release only authentic zero RESERVE launch holds with matching request/run/epoch receipt and native proof, append RELEASE idempotently and preserve MODEL budget rows.')
 ],
 limitations=[
  'Not integrated Main qualification or full Electron/normal-user first-use acceptance. Parent separately reproduced installed Electron image exceeding the pre-existing 128 MiB supervisor image cap; that supervisor repair is not included in these 24 files.',
  'No real local/cloud model invocation, protected holdout, paid endpoint, public tunnel or external service call. Synthetic SSE behavior does not qualify a real provider.',
  'The exact frozen author binaries and VCS metadata were checked and exercised, not independently rebuilt; this is not a complete reproducible-build claim.',
  'Native coding integration uses an in-process coordinator plus actual Host/Mu/verifier; the separate child-control lifecycle proves start/READY/shutdown. It does not claim a complete Electron-to-child-control coding journey.',
  'Only registered changed files and relevant regression/native/independent boundary suites were reviewed; whole-repository testing was not performed.',
  'The final unavailable-version-store negative test proves fail-closed on authoritative store unavailability, not a surgically removed immutable profile version. Earlier invalid attempts to mutate immutable records remain visible as reviewer-fixture failures.'
 ],
 history=history+[
  dict(classification='FIXTURE_REPAIR_DETAIL',detail='Attempt1 attempted immutable confirmation/observation/effect writes, removed only a mutable profile copy while the authoritative version remained, and called a route helper before installation. Attempt2 fixed those but still attempted immutable dispatch-manifest mutation for one case. Final fixture inserts malformed evidence before sealing, uses a fresh genuine-expiry request, reads the bound profile directly, and faults only its isolated version-store availability.'),
  dict(classification='CLEANUP_BLOCKED',detail='Scoped PowerShell recursive deletion of this review cache was rejected by automatic approval review: blocked by policy. Retained cache excluded from manifest; no alternate deletion method attempted.')
 ],
 actual_model_calls=0,external_calls=0,public_tunnel_calls=0,paid_calls=0,formal_acceptance_delta=0,parent_acceptance_delta=0,
 writes='Only this new independent review receipt directory was written. Virtual Go overlay added test code without modifying candidate files. Main/Canon/contracts/old receipts untouched; final candidate clean and author frozen bundle/receipts unchanged.'
)
write('independent-review.json',report)
(OUT/'README.md').write_text('''# Product coding Core 独立审查

**ACCEPT — SOURCE_AND_NATIVE_SYNTHETIC_FIXTURE_ONLY**。候选 `860a8935c8fffe4a1671eafa177e7fc5a053158a`，实际24文件、登记30路径；未发现阻断项。

186/186 源码、范围、原始证据和冻结二进制检查通过。独立运行44个父测试、114个子测试通过，无最终失败或跳过。包含原生 Host / Mu AppContainer / verifier、真实工具读改写及隔离 Go 检查；私有 shutdown 接受，release 仍拒绝，6条 UNKNOWN/null 账本原样保留。真实 control 子进程两代协议退出成功。

独立补充覆盖冻结期间 epoch/revision/Owner/真实TTL变化、6类退出证据缺口和禁止编码授权降级。两次 reviewer 夹具失败及当时源码、原始输出完整保留，没有改写历史。最终版本存储不可用测试只证明读取失败时闭锁，不冒充精确删除不可变 profile 的用例。

原始 bundle 的 json.loads 路径均直接存在并与目标 samefile；中文是实际 Unicode 字符，不是 literal backslash-u，未改冻结 bundle。

接受不包括完整 Electron 使用流程或真实模型资格。Electron 大镜像的原有 supervisor 128MiB 限制由主线程另行修复，未计入本候选24文件。本轮10个模型响应均为合成 SSE，真实模型/外部服务/付费/隧道调用为0，formal/parent +0。冻结二进制已核验并使用，未独立重建。

本轮缓存的定向删除被自动审批审查以 `blocked by policy` 拒绝，保留并排除证据清单；未改用其他删除方式。
''',encoding='utf-8')
canon={}
for name in ['current_spec.json','checkpoint.json','step_state.json','path_ownership.json','commands.json']:
 p=ROOT/'execution/v2.4'/name;canon[name]=dict(sha256=sha(p),facts={k:v for k,v in read(p).items() if k in ['revision','head','status','plan_sha256','spec_manifest_sha256','manifest_sha256']})
write('main-canon-end-observation.json',dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),canon=canon,note='Read-only observation; concurrent parent work is outside reviewer write scope.'))
excluded={'cache':'Reviewer-owned Go build/runtime cache retained because scoped deletion was blocked by policy; may contain generated private fixture runtime state.'}
files=[]
for p in sorted(OUT.rglob('*')):
 rel=p.relative_to(OUT)
 if p.is_file() and rel.parts[0] not in excluded and p.name not in ['receipt_manifest.json','review-seal.json']:
  files.append(dict(path=rel.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
write('receipt_manifest.json',dict(schema='researchos.independent-review-manifest/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='ACCEPT',acceptance_scope=report['acceptance_scope'],candidate=CANDIDATE,model_calls=0,external_calls=0,excluded_retained_runtime_roots=excluded,files=files))
for row in files:assert sha(OUT/row['path'])==row['sha256']
seal=dict(decision='ACCEPT',acceptance_scope=report['acceptance_scope'],files=len(files),decision_sha256=sha(OUT/'independent-review.json'),manifest_sha256=sha(OUT/'receipt_manifest.json'))
write('review-seal.json',seal);print(json.dumps(seal))
