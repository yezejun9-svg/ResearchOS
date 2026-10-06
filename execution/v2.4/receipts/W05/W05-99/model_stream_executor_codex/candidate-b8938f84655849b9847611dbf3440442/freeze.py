import datetime, hashlib, json, re, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[6]
NS=HERE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,value): (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def counts(raw):
    return {'inclusive':{s:len(re.findall(r'^\s*--- '+s+r':',raw,re.M)) for s in ['PASS','FAIL','SKIP']},'top_level':{s:len(re.findall(r'^--- '+s+r':',raw,re.M)) for s in ['PASS','FAIL','SKIP']},'no_test_packages':[x for x in raw.splitlines() if '[no test files]' in x]}
source=json.loads((HERE/'source_manifest.json').read_text('utf8'))
for row in source['changed_owned_source']:
    assert sha(ROOT/row['path'])==row['after_sha256'],row['path']
final=[]
for name in ['closure-e4e653dccd104937898e4096a3669e4e','closure-90cf17c50dce436095c5fb16c3ac1bd5']:
    p=NS/name; result=json.loads((p/'result.json').read_text('utf8')); raw=(p/'test.stdout').read_text('utf8')
    assert result['exit']==0 and not result['source_drift'],result
    before=json.loads((p/'source_before.json').read_text('utf8'));after=json.loads((p/'source_after.json').read_text('utf8'));assert before==after
    for row in source['changed_owned_source']: assert before['repo:'+row['path']]==row['after_sha256']
    c=counts(raw); assert c['inclusive']['FAIL']==0 and c['inclusive']['SKIP']==0
    final.append({'directory':p.relative_to(ROOT).as_posix(),'result':result,'counts':c,'invocation_ref':ref(p/'test.invocation.json'),'stdout_ref':ref(p/'test.stdout'),'stderr_ref':ref(p/'test.stderr'),'source_before_ref':ref(p/'source_before.json'),'source_after_ref':ref(p/'source_after.json'),'go_list_invocation_ref':ref(p/'go-list.invocation.json'),'go_list_raw_ref':ref(p/'go-list.stdout'),'environment_ref':ref(p/'environment.json')})
protected=[]
for p in sorted((ROOT/'migrations/sqlite').glob('*.sql')):
    original=subprocess.check_output(['git','show','HEAD:'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
    protected.append(dict(ref(p),equals_composition_HEAD=hashlib.sha256(original).hexdigest()==sha(p)))
assert all(p['equals_composition_HEAD'] for p in protected)
save('protected_migrations.json',protected)
current=NS/'closure-eddbf315ec3242b4a2373a66a874e83f/test.stdout'; baseline=NS/'contract-baseline-6a68f8b335654dcbacd37996d3961182/stdout.raw'
a=json.loads(current.read_text('utf8'));b=json.loads(baseline.read_text('utf8'))
save('legacy_comparison.json',{'current_ref':ref(current),'baseline_ref':ref(baseline),'current_pass':a['assertions'],'baseline_pass':b['assertions'],'current_failures':a['failures'],'baseline_failures':b['failures'],'added_failure_ids':sorted({x['id'] for x in a['failures']}-{x['id'] for x in b['failures']}),'removed_failure_ids':sorted({x['id'] for x in b['failures']}-{x['id'] for x in a['failures']}),'same_pass_ids':a['assertion_ids']==b['assertion_ids'],'status':'BOTH_FAIL_NO_NEW_FAILURE_IDS_NOT_A_PASS'})
runs=[]
for p in sorted(NS.glob('*')):
    if not p.is_dir() or p==HERE: continue
    invs=list(p.glob('*invocation*.json'))
    if not invs: continue
    entry={'directory':p.relative_to(ROOT).as_posix(),'invocations':[ref(x) for x in invs]}
    stdout=next((x for x in [p/'test.stdout',p/'stdout.raw'] if x.exists()),None)
    if stdout: entry.update(stdout_ref=ref(stdout),counts=counts(stdout.read_text('utf8',errors='replace')))
    runs.append(entry)
save('failure_origins.json',{'canonical_failure_counters_modified':False,'all_original_raw_preserved':True,'actual_runs':runs,'origins':[
 {'id':'initial-bridge-void-return','directory':'compile-b315653fbe5045adb44f335ef0036de7','actual_exit':1,'resolution':'Corrected return from void bridge wait function; original compiler raw retained.'},
 {'id':'actual-final-proof-artifact-fields','directories':['test-53a6e07436494837878a09393994fdce','test-233b5d63f16643669875d24cbf6f4aa8'],'actual_exit':1,'resolution':'Real settled CLI hung because final verifier read hash/size rather than authoritative content_hash/byte_size. Fixed real field contract; preserved actual closed DB and independent raw snapshot; legacy real CLI subsequently passed.'},
 {'id':'restore-append-only-count','directory':'test-816107ae9be74b74a43d50f1e2eb4bce','actual_exit':1,'resolution':'Fixture initially counted all historical UNKNOWN facts; corrected assertion to latest logical effect, retaining original restoration append history.'},
 {'id':'test-principal-type','directory':'test-91bd423b3c9f4104a0d3fa55696e1f69','actual_exit':1,'resolution':'Fixed new test Principal argument type.'},
 {'id':'missing-explicit-go-environment','directories':['closure-1149758719e74686ae882339bdae2b01','closure-fee33d53be604a30b5731e46d5bf5b5c'],'actual_exit':1,'resolution':'Immutable harness v4 supplies exact pinned RESEARCHOS_GO; first zero-assertion CLI contract is not PASS.'},
 {'id':'legacy-cli-contract-29','directory':'closure-eddbf315ec3242b4a2373a66a874e83f','actual_exit':1,'resolution':'OPEN baseline mismatch. Same-input actual HEAD overlay has exact same 66 pass and29 fail IDs. No old fixture/assertion/CLI protocol changed.'},
 {'id':'legacy-W17-upgrade','directories':['closure-0f4d4b8337894935888042450559b7a1','baseline-regression-88e14e7ccd7e405990c2bd9f02584d73','upgrade-cli-baseline-5c982bcc43124ae5a0f8d07f2cd22d65'],'actual_exit':1,'resolution':'OPEN existing failures reproduced with all stream Go changes removed: missing runtime_dispatches on ActiveRecovery; missing next_v24_sessions.sql in historical CLI fixture.'},
 {'id':'legacy-linux-platform','directory':'cross-platform-007766b81f3b41fd8991d0d707960edf','actual_exit':1,'resolution':'OPEN existing platform compilation issues; baseline overlay reproduces identical Hash/windows/evolution symbols. No Linux runtime PASS claimed.'},
 {'id':'cancel-abort-idle-race','directory':'closure-f4e6c4794fac41f5b8446039d1a54cc1','actual_exit':1,'resolution':'Actual SDK clear+idle could precede abort_observed; old Go idle handler killed worker early. Fixed same-binding durable two-fact join; deterministic both-order/foreign identity controls plus actual SDK cancellation pass. JS frozen source unchanged.'}
]})
proofs={
'T01':'Pure quarantine CRLF/multiline/UTF8/JSON escaping/bounds/EOF and JS mixed zero-text/tool/thinking controls; final domain and independent JS20 raw.',
'T02':'Actual provider flush A..40 only released by SDK private observation, committed SQLite public delta, sealed prefix and compiled CLI arrival. Monotonic watermarks and observed_at in MODEL_STREAM_CAUSAL rows.',
'T03':'Real compiled CLI/private Host/native pipe/API; six new fixture cases including35,000-byte pipelined terminal and exact accepted original bytes. Existing replay tests remain passing.',
'T04':'Actual FOLLOW_UP/STEER SDK consumption in same worker plus canonical original SDK/effect verifier; 201-message immutable history, incomplete prefix, stale CAS and atomic seal rollback.',
'T05':'Bridge strict binding/sequences/digests/numbers/duplicates/limits/init;40 observations retain ordinary ACK; terminal cannot overtake earlier raw pull.',
'T06':'Same-binding abort/idle two-order deterministic controls; original actual SDK cancel plus actual CLI prefix cancel, UNKNOWN and original ACKNOWLEDGED preserved; no claim of final idempotency receipt.',
'T07':'Actual interrupted-prefix closed SQLite → actual encrypted backup/restore and8 forged-evidence controls; actual prefix seal failure rolls back delta and leaves UNKNOWN/no END; existing real child-process checkpoint crash recovery passes.',
'T08':'Synthetic secret wire/decoded boundaries plus actual SDK split-secret quarantine; no secret fragment in worker/public/durable evidence; thinking/tool-only remain non-public via independent JS controls.',
'T09':'Final full CLI and focused relevant runtime/client/backup/model/session suites pass0skip. Complete broad raw retains unrelated resource skips, missing harness Go first failures, known legacy29 andW17/Linux baseline failures.'}
fixtures=[]
for run in final:
    folder=ROOT/run['directory']/'actual-fixtures'
    if folder.exists(): fixtures += [ref(p) for p in sorted(folder.rglob('*')) if p.is_file()]
save('handoff.json',{'schema':'researchos.model-stream.source-candidate.v1','status':'IMPLEMENTED_PENDING_INDEPENDENT_SOURCE_REVIEW','actor':'codex:/root/sources_parent_impl','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_ref':ref(HERE/'source_manifest.json'),'owned_changed_source_count':len(source['changed_owned_source']),'authorized_but_unchanged':['internal/domain/runtime_effect_wire_windows.go'],'delegated_js_source_count':2,'final_runs':final,'actual_fixture_artifacts':fixtures,'failure_origins_ref':ref(HERE/'failure_origins.json'),'legacy_comparison_ref':ref(HERE/'legacy_comparison.json'),'protected_migrations_ref':ref(HERE/'protected_migrations.json'),'coverage':proofs,'remaining_gates':[
'No LIVE model/provider or formal W05/A04 acceptance; all new network ports are explicit local FIXTURE.',
'Original client_protocol.go ACKNOWLEDGED→final UPDATE conflicts with unconditional idempotency_immutable trigger. This change closes SDK abort/idle facts only; original UNKNOWN/CANCEL stays unresolved. Root reported this independent existing open gate; no protected source/SQL changed.',
'Legacy CLI29 failures and historical W17 ActiveRecovery/CLI plus Linux platform errors remain actual baseline failures; no suite-wide green claim.',
'Six resource/subprocess-gated skips and missing explicit Go failures in first broad run remain original evidence. Final relevant selectors are separately complete0skip; unrelated W16/current-resource lanes are not certified.',
'Restore test preserves actual interrupted observations and fences current execution; it never resumes an old worker stream or upgrades FIXTURE to LIVE.'
],'formal_acceptance_delta':0,'external_provider_calls':0})
files=[p for p in sorted(NS.rglob('*')) if p.is_file() and p != HERE/'manifest.json']
save('manifest.json',{'schema':'researchos.model-stream.receipt-manifest.v1','self_excluded':True,'files':[ref(p) for p in files]})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'manifest':ref(HERE/'manifest.json'),'final_runs':[(x['directory'],x['counts']) for x in final]},ensure_ascii=False))
