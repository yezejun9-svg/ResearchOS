"""Pure-value NF4 registrar and authority delta controls; no actual authority."""
import ast,copy,hashlib,json,types
from datetime import datetime,timedelta,timezone
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4'
NF=N.parent.parent/'full_w09_main_native_producer_source_codex/fullw09-20261010-04'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def mod(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
checks=[]
def check(n,b):assert b,n;checks.append(n)
def reject(n,fn):
 try:fn()
 except (ValueError,KeyError):checks.append(n);return
 raise AssertionError(n)
core=mod(N/'adoption_core.source.py');caller=mod(N/'register_w09_adoption.source.py');rt=mod(NF/'full_w09_runtime.source.py')
pins=doc(N/'input-pins.json')['refs'];choice=doc(NF/'source.choice.json');contract=doc(NF/'root-calling-contract.json')
def synthetic(name):return dict(path=str(N/('CONTROL_ONLY_'+name)),sha256='0'*64,bytes=0)
for key in ('NR_hdf','NR_mf','NR_decision'):pins[key]=synthetic(key)
raw4=[(V/(k+'.json')).read_bytes() for k in ('checkpoint','path_ownership','step_state','commands')]
current4=[core.pin_raw(V/(k+'.json'),b) for k,b in zip(('checkpoint','path_ownership','step_state','commands'),raw4)]
cp,ow,ss,cm=[json.loads(b) for b in raw4]
moment=datetime.now(timezone.utc);until=moment+timedelta(minutes=55)
request=dict(kind='NATIVE_SCOPES',generation=core.GENERATION,before_canonical_refs=current4,
 created_utc=moment.isoformat(),pending_ref=synthetic('pending'),
 reviewed_source_audit_refs={'producer-author':synthetic('author-audit'),'producer-review':synthetic('review-audit')},
 native_leases={k:dict(lease_id=hashlib.md5(('CONTROL_ONLY_'+k).encode()).hexdigest(),lease_issued_at=moment.isoformat(),lease_expires_at=until.isoformat()) for k in core.SELECTORS})
scopes=core.make_native_scopes(request,pins,choice,contract)
scope_refs={k:synthetic('scope-'+k) for k in core.SELECTORS}
own=dict(hdf=synthetic('registrar-HDF'),decision=synthetic('registrar-decision'))
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by=core.ROOT,counter_reset=False,registered_in_current_canon=False,
 current_canonical_refs=current4,source_cutoff_original_failure_ordinal=cp['work_in_progress']['root_next_failure_ordinal_live']-1,
 next_original_failure_ordinal=cp['work_in_progress']['root_next_failure_ordinal_live'],pending=[])
args=(cp,ow,request,scope_refs,scopes,pending,current4,own,synthetic('prior-profile-commit'))
ca,oa,cops,oops=core.canonical_changes(*args)
check('four-new-generation-scopes',len(scopes)==4 and ca['work_in_progress']['w09_native_producer_scope_generations'][core.GENERATION]==scope_refs)
check('old-scope-map-exact',ca['work_in_progress']['w09_native_producer_scopes']==cp['work_in_progress']['w09_native_producer_scopes'])
check('old-workers-exact',ca['workers'][:len(cp['workers'])]==cp['workers'] and len(ca['workers'])==len(cp['workers'])+4)
oldsub=ow['card_path_bindings']['W09-99']['subtasks'];newsub=oa['card_path_bindings']['W09-99']['subtasks']
check('old-owners-exact',all(newsub[k]==v for k,v in oldsub.items()) and len(newsub)==len(oldsub)+4)
check('old-failures-exact',ca['failure_counters']==cp['failure_counters'])
check('no-profile-reregistration',ca['work_in_progress']['w09_profile_adoption_registration']==cp['work_in_progress']['w09_profile_adoption_registration'])
check('complete-CP-byte-inverse',core.encoded(core.inverse_operations(ca,cops))==raw4[0])
check('complete-OW-byte-inverse',core.encoded(core.inverse_operations(oa,oops))==raw4[1])
check('scopes-no-Main-Canon-grant',all(not s['Source_mutation'] and not s['checkpoint_write'] and not s['ownership_write'] and not s['formal_acceptance'] for s in scopes.values()))
check('one-list-one-test-per-scope',all(s['maximum_go_list_runs']==s['maximum_go_test_runs']==1 for s in scopes.values()))
def modified(which,fn):
 values=list(args);values[which]=copy.deepcopy(values[which]);fn(values[which]);return lambda:core.canonical_changes(*values)
reject('reject-old-live-worker',modified(0,lambda c:next(x for x in c['workers'] if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_W09-G01').update(state='LIVE')))
reject('reject-old-unclosed-job',modified(1,lambda o:o['card_path_bindings']['W09-99']['subtasks']['full_w09_main_native_producer_W09-G02']['actual_closed'].update(all_owned_jobs_closed=False)))
reject('reject-reused-generation',modified(0,lambda c:c['work_in_progress'].update(w09_native_producer_scope_generations={core.GENERATION:scope_refs})))
reject('reject-request-other-generation',modified(2,lambda q:q.update(generation='old')))
reject('reject-scope-other-generation',modified(4,lambda s:s['C19'].update(generation='old')))
reject('reject-old-run-id',modified(4,lambda s:s['C19'].update(run_id=next(x['run_id'] for x in cp['workers'] if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_W09-G01'))))
reject('reject-counter-reset',modified(5,lambda p:p.update(counter_reset=True)))
reject('reject-noncontiguous-counter',modified(5,lambda p:p.update(next_original_failure_ordinal=p['next_original_failure_ordinal']+1)))
q=copy.deepcopy(request);q['native_leases']['C19']=copy.deepcopy(q['native_leases']['A06'])
reject('reject-shared-selector-lease',lambda:core.make_native_scopes(q,pins,choice,contract))
# Validate actual NF4 authority function against synthetic guarded input maps.
# No documents below are saved as Root Scope, request, audit, or registration.
href,mref=ref(NF/'HDF.json'),ref(NF/'MF.json');contractref=ref(NF/'root-calling-contract.json')
for key in core.SELECTORS:
 c=rt.choice(key);sr=scope_refs[key];scope=scopes[key]
 vr=synthetic('canonical-vector');qr=synthetic('request-'+key)
 q=dict(schema=contract['request_schema'],issued_by=core.ROOT,selector=key,scope_ref=sr,canonical_vector_ref=vr,
 calling_contract_ref=contractref,scope_audit_ref=synthetic('scope-audit'))
 vector=dict(schema='researchos.w09-four-selector-native-canonical-vector.v1',checkpoint_revision=ca['revision'],ownership_revision=oa['revision'],refs=current4)
 reviewer='codex:/root/control_only_independent_peer'
 decision=dict(schema=contract['review_schema'],decision=contract['review_decision'],actor_role='INDEPENDENT_NON_AUTHOR',
 actor_id=reviewer,source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=contractref,
 **contract['bound_source_refs'],selectors=choice['selectors'],source21=c['source21'],actual_executed=False,formal_case_accepted_delta=0)
 review=dict(source_decision_ref=pins['NR_decision'],actor_id=reviewer)
 documents={qr['path']:q,sr['path']:scope,vr['path']:vector,contractref['path']:contract,pins['NR_decision']['path']:decision,
 current4[0]['path']:ca,current4[1]['path']:oa,current4[2]['path']:ss,current4[3]['path']:cm,
 contract['bound_source_refs']['choice_ref']['path']:choice}
 rt.read_ref=lambda r:core.encoded(documents.get(r['path'],{}))
 rt.pin=lambda p:ref(Path(p))
 rt.package_refs=lambda:(href,mref,[])
 rt.pair=lambda h,m:(review,[pins['NR_decision']])
 rt.actual_audit=lambda *a:[]
 rt.unique=lambda refs:refs
 rt.validate_authority(qr,c)
 check('NF4-authority-owner-worker-'+key,True)
 bad=copy.deepcopy(c);bad['generation']='old'
 reject('NF4-reject-old-generation-'+key,lambda:rt.validate_authority(qr,bad))
 bad=copy.deepcopy(c);bad['scratch_root']=str(R/'.local'/'wrong')
 reject('NF4-reject-old-scratch-'+key,lambda:rt.validate_authority(qr,bad))
# Exact Source inverse and absence of any Main mutation entrypoint.
delta=doc(N/'source-delta.json')
for row in delta['source_deltas']:
 text=(N/row['file']).read_bytes().decode('utf-8')
 for e in reversed(row['inverse_edits']):
  assert text[e['new_start']:e['new_end']]==e['after']
  text=text[:e['new_start']]+e['before']+text[e['new_end']:]
 check('exact-source-inverse-'+row['file'],text.encode('utf-8')==Path(row['base_ref']['path']).read_bytes())
check('no-Main-adoption-entrypoint',not hasattr(caller,'apply_profile') and not hasattr(caller,'profile_outputs'))
check('no-old-three-gate-bypass',not any(op['path']==['work_in_progress','w09_native_producer_scopes'] for op in cops))
check('dynamic-current4-only',request['before_canonical_refs']==current4)
put(N/'delta-controls.json',dict(schema='researchos.w09-nf4-registration-delta-controls.v1',status='PASS',passed=len(checks),failed=0,
 checks=checks,current4_observed_for_pure_controls=current4,synthetic_Source_only=True,
 synthetic_scopes_requests_audits_not_published=True,actual_Root_authority=False,actual_TP_calls=0,
 actual_Main_writes=0,actual_Canon_writes=0,actual_Native_runs=0,actual_Go_runs=0,old_controls_rerun=False))
print(json.dumps(dict(status='NF4_REGISTRATION_DELTA_PASS',passed=len(checks),report_ref=ref(N/'delta-controls.json')),ensure_ascii=False))

