import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp543'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute()else R/p;a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes']
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp543.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==542 and ow['revision']==328 and len(cp['failure_counters'])==2141
prior=read(N/'continuation-cp542/RESUME.current.json')
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only')
baseline=read(N/'React-Main-integration-baseline.json')
assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==baseline['dirty_paths']
for x in baseline['protected_source']+baseline['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:verify(x)
for name in ['046-boot6-v5-independent-static-verify','047-boot6-v6-owned-env-verify']:assert read(N/(name+'.recipe.result.json'))['native_exit']==0
static=read(N/'C57-boot6-v5-independent-static-root-verification.json');v6=read(N/'C57-boot6-v6-root-verification.json')
for x in static['verified_refs']+v6['verified_refs']:verify(x)
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'root-tool-parser-diagnostics.json',{'schema':'researchos.root-tool-parser-diagnostics.v1','events':[{'id':'read-only-source-parse-01','tool':'functions.exec','error':'SyntaxError: Invalid or unexpected token','operation':'Read bounded openNativeAccess/setTargetDescriptor/native test source','dispatched_native_command':False,'native_exit':None,'resolution':'Corrected syntax; tool chunk22e9f3 exit0 read succeeded'},{'id':'read-only-source-parse-02','tool':'functions.exec','error':'SyntaxError: Invalid or unexpected token','operation':'Read denyDescriptor/write-owner references','dispatched_native_command':False,'native_exit':None,'resolution':'Corrected syntax; tool chunk030d50 exit0 read succeeded'}],'no_product_mutation':True})
new(O/'C57-transaction-lifetime-observation.json',{'status':'SOURCE_RACE_CONFIRMED_AUTHOR_FIX_AND_TEST_REPORTED_PENDING_FINAL_VERIFICATION','finding':'BeginTx(ctx) auto-rollback can win done CAS so explicit Rollback returns ErrTxDone before underlying driver rollback returns; closing native hold at that point is early','root_source_observation':'Current ApplyHistoricalQualification and PlanHistoricalQualification in parent mutable source; root asked concrete canceled/commiterror lifecycle checks','author_response':'Confirmed actual race, changed Plan+Apply lifecycle to context.WithoutCancel(ctx), statement/q.Check originalctx, ctx.Err before preflight/commit; common finishHistoricalQualificationTx synchronously waits driver rollback then closeshold','author_reported_test':'Controlled blocked-driver cancellation and commit-error fixtures hold native file against rename until actual driver return then permit rename; native0 reported','evidence_limit':'Final raw test/recipe and candidate hash not yet Root-verified; do not claim independent closure','formal_increment':0})
new(O/'C57-current-progress-unaccepted.json',{'at':now,'boot6_static_review':ref(N/'C57-boot6-v5-independent-static-root-verification.json'),'boot6_static_status':'NEEDS_WORK_THREE_P1; original-owner restoration eligibility, individual record ACL/identity/read path, disabled-but-enableable token groups','boot6_v6_author_failures':ref(N/'C57-boot6-v6-root-verification.json'),'boot6_v6_status':'Three owned-environment suites native1, each2ACLskips+childsentinelSkip+1failure; exact API AccessDenied stage unresolved, not inferred to privilege alone','boot6_source_status':'Author now repairing original6 only, immutablev5/v6 retained, newfreeze pending','parent_source_status':'Original51 remains parent;042-049 owned-env narrow tests reported0 before new transaction-lifetime fix; only affected domain/integration paths require rerun','transaction_fix':ref(O/'C57-transaction-lifetime-observation.json'),'combined57_status':'NOT_FROZEN_NO_COMMIT_NO_PHASE2_ACCEPTANCE','cleanup_exception':v6['auto_review_cleanup'],'unrelated_old_cleanup_policy':'Older qualification-failure-b-r3 tmp denial still stands; no retry/bypass','formal_increment':0})
records=[]
for x in static['findings']:records.append({'origin_key':'20261025|independent|'+x['id'],'attempts':1,'status':'SOURCE_FINDING_OPEN','detail':x,'evidence_ref':ref(N/'C57-boot6-v5-independent-static-root-verification.json'),'counter_reset':False})
for x in v6['native_failed_records']:records.append({'origin_key':'20261025|boot6-author-v6|'+x['event'],'attempts':1,'status':'NATIVE_FAILURE_PRESERVED','detail':x,'evidence_ref':ref(N/'C57-boot6-v6-root-verification.json'),'counter_reset':False})
records.append({'origin_key':'20261025|boot6-v6-cleanup-auto-review','attempts':2,'status':'AUTO_REVIEW_REJECTED_NO_NATIVE_EXECUTION','detail':v6['auto_review_cleanup'],'native_exit':None,'evidence_ref':ref(N/'C57-boot6-v6-root-verification.json'),'counter_reset':False})
records.append({'origin_key':'20261025|C57-async-rollback-native-hold-race','attempts':1,'status':'SOURCE_RACE_FIX_REPORTED_PENDING_VERIFICATION','evidence_ref':ref(O/'C57-transaction-lifetime-observation.json'),'counter_reset':False})
for i in [1,2]:records.append({'origin_key':'20261025|root-cp542-tool-parser-'+str(i),'attempts':1,'status':'TOOL_PARSE_REJECTED_BEFORE_NATIVE_DISPATCH','native_exit':None,'evidence_ref':ref(O/'root-tool-parser-diagnostics.json'),'counter_reset':False})
assert len(records)==12
assert not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
new(O/'new-records-ledger.json',{'distinct_mixed_records':12,'records':records,'same_v5_scope_deviation_not_double_counted':'20261025|c57-author-fixture-environment-scope','product_failure_count':False,'parent_author_ledger':'PENDING_FINAL_FROZEN_IMPORT_NOT_ZERO'})
before=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2141]==before and len(cp['failure_counters'])==2153
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v121',at=now,checkpoint_revision=543,ownership_revision=329,failure_records_preserved=2153,C57_boot6_independent_static_verified_ref=ref(N/'C57-boot6-v5-independent-static-root-verification.json'),C57_boot6_v6_root_verification_ref=ref(N/'C57-boot6-v6-root-verification.json'),C57_unaccepted_progress_ref=ref(O/'C57-current-progress-unaccepted.json'),C57_transaction_lifetime_observation_ref=ref(O/'C57-transaction-lifetime-observation.json'))
resume['next_command']='Continue two existing C57 source owners: parent51 transaction lifetime fix and meaningful canceled/commiterror native tests, boot6 threeP1 fixes and exact native AccessDenied diagnosis under owned fixture environment. Preserve immutablev5/v6 and all failures; blocked cleanup file must not be deleted by another route. New6 freeze + affected integration tests then combined57 exact commit/tree/40pins/author ledger; Root phase2 amendment before independent acceptance. MainReact7d remains, originaldata untouched, formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=543,expected_previous_revision=542,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp543=rr,C57_boot6_independent_static_verified_ref=ref(N/'C57-boot6-v5-independent-static-root-verification.json'),C57_boot6_v6_root_verification_ref=ref(N/'C57-boot6-v6-root-verification.json'))
cp['evidence_index'].append({'kind':'C57_INDEPENDENT_THREE_P1_AND_OWNED_FIXTURE_FAILURES_REGISTERED_TRANSACTION_FIX_PENDING','ref':rr,'formal_increment':0})
ow.update(revision=329,expected_previous_revision=328,updated_at=now,updated_by='codex:/root')
ow['special_paths']['C57_boot6_source'].update(state='IMPLEMENTING_THREE_INDEPENDENT_P1_FIXES_AND_NATIVE_FAILURE_DIAGNOSIS',evidence_ref=ref(N/'C57-boot6-v5-independent-static-root-verification.json'))
ow['special_paths']['C57_maintenance_source'].update(state='IMPLEMENTING_EXCLUSIVE51_TRANSACTION_LIFETIME_FIX_PENDING_BOOT6_FREEZE')
ow['special_paths']['C57_independent_review'].update(state='PHASE1_STATIC_NEEDS_WORK_THREE_P1_WAITING_NEW_FREEZE_NO_CANDIDATE_TESTS',evidence_ref=ref(N/'C57-boot6-v5-independent-static-root-verification.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as f:f.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode())
swap(hp,raw[hp],('# Current verified continuation CP543'+chr(10)*2+'Read '+rr['path']+' first. MainReact7d dirty20/protected9/oldDist33/staged3 preserved. Boot6 static NEEDS_WORK3P1, owned-envv6 failures5native records verified; sourcefix and ACLfailure diagnosis active. Parent51 async rollback native-hold race fix/test reported, final binding pending. Combined57notfrozen, phase2notstarted. Cleanupdiagnostic file retained after blocked by policy; no bypass. Formal0/42/all22open, mixedrecords2153 plus pending parent ledger.'+chr(10)*2).encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':543,'ownership':329,'mixed_records':2153,'static_refs':static['verified_count'],'v6_refs':v6['verified_count'],'resume':rr},ensure_ascii=False))

