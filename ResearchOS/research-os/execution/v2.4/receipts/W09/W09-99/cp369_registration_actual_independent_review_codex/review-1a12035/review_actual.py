from pathlib import Path
import base64,copy,hashlib,json,re,sys,types
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
N=W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
S=W/'cp369_native_source_independent_review_codex/review-1a11fff';O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];refs={};raws={}
def ck(n,v,d=None):checks.append(dict(name=n,passed=bool(v),detail=d))
def pinraw(p,b):return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def pin(p):return pinraw(p,p.read_bytes())
def read(r):
    if not(type(r)==dict and set(r)=={'path','sha256','bytes'} and type(r['path'])==str and type(r['sha256'])==str and re.fullmatch('[0-9a-f]{64}',r['sha256']) and type(r['bytes'])==int and r['bytes']>=0):raise ValueError('EXACT_TYPED_REF')
    p=Path(r['path']);b=p.read_bytes();ck('pin:'+str(p),pinraw(p,b)==r)
    k=str(p).casefold();ck('consistent_pin:'+str(p),k not in refs or refs[k]==r);refs[k]=r;raws[k]=b;return b
def obj(r):return json.loads(read(r))
def discovered(p):return obj(pin(p))
def save(name,data):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def diff(a,b,path=''):
    if type(a)!=type(b):return [path]
    if type(a)==dict:
        result=[]
        for k in set(a)|set(b):result+=([path+'/'+k] if k not in a or k not in b else diff(a[k],b[k],path+'/'+k))
        return sorted(result)
    if type(a)==list:return [] if a==b else [path]
    return [] if a==b else [path]
hr=dict(path=str(S/'HDF.json'),sha256='779084e1c14fa6aa69be4dcce689d7726781e884611388ebc71f655cc513e911',bytes=2544)
sh=obj(hr);smr=sh['manifest_ref'];sm=obj(smr);sd=obj(sh['source_decision_ref'])
ck('independent_Source_accepted',sh['status']==sd['decision']=='SOURCE_ACCEPTED_FOR_ROOT_CP369_MAIN_C19_REGISTRATION' and sd['actor_id']==ACTOR and sd['actor_role']=='INDEPENDENT_NON_AUTHOR' and sd['execution_grant'] is False)
for r in sm['members']:read(r)
source_inverse=obj(next(r for r in sm['members'] if Path(r['path']).name=='complete-canonical-byte-inverse.source.json'))
h=obj(sh['source_handoff_ref']);m=obj(sh['source_manifest_ref']);ck('Root_Source_manifest_binding',h['manifest_ref']==sh['source_manifest_ref'])
for r in m['members']:read(r)
facts=obj(h['facts_ref']);scope=obj(h['scope_ref']);contract=obj(facts['calling_contract_ref'])
proofref=dict(path=str(N/'canonical_pair.activate.json'),sha256='af5f3abdf92bb1d6a349ecc57e362d873ba660aa1e603745f840cc198b1fafe2',bytes=1588)
proof=obj(proofref);tx=Path(proof['transaction']['transaction_journal'])
intent=discovered(tx/'intent.json');committed=discovered(tx/'committed.json')
before=[read(r) for r in intent['before_refs']];after=[read(r) for r in intent['after_refs']]
actualrefs=[proof['transaction']['checkpoint_ref'],proof['transaction']['ownership_ref']]+facts['canonical_refs'][2:]
current=[read(r) for r in actualrefs];old=[json.loads(b) for b in before];new=[json.loads(b) for b in after];oc,oo=old;ac,ao=new
ck('actual_pair_exact_supplied',actualrefs[0]['sha256']=='dd997457f14314374ee4577fff6fd87317e05ad908f4c24d01ce302af72edeb7' and actualrefs[0]['bytes']==4370868 and actualrefs[1]['sha256']=='da777233cf369e433d4db61f75b579cfcd9a3b9f5092f6b7acafc7c3106cc5d2' and actualrefs[1]['bytes']==206009)
ck('transaction_before_pins',intent['expected_refs']==facts['canonical_refs'][:2] and all(pinraw(Path(r['path']),b)==r for r,b in zip(intent['expected_refs'],before)))
ck('committed_exact_pair',committed['after_refs']==actualrefs[:2]==proof['proposed_refs'] and committed['written_indices']==[0,1] and committed['both_verified_while_exclusively_held'] is True and intent['mandatory_share_mode']==0 and type(intent['mandatory_share_mode'])==int and intent['automatic_inverse'] is False)
ck('transaction_after_matches_current',current[:2]==after)
live_ref=dict(path=str(N/'live-context.postseal.actual.root.json'),sha256='d6ed04f0a8bc20a23d5b0f7cfbdc677cf1a4e3a7319c0c19f69b513bbe18e839',bytes=2447)
live=obj(live_ref)
ck('fresh_after_Source_seal',datetime.fromisoformat(live['created_utc'])>datetime.fromisoformat(sd['reviewed_at']))
ck('postseal_cutoff_pending',live['source_cutoff']=={'highest_ordinal':965,'next_failure_ordinal':966} and type(live['next_original_failure_ordinal'])==int and live['next_original_failure_ordinal']==970 and [x['ordinal'] for x in live['pending']]==[966,967,968,969])
for p in live['pending']:read(p['origin_ref'])
expected=[json.loads(base64.b64decode(x['whole_after_base64'])) for x in source_inverse['files']]
ck('source_before_complete_bytes',all(base64.b64decode(s['whole_before_base64'])==b and s['original_ref']==r for s,b,r in zip(source_inverse['files'],before,facts['canonical_refs'])))
sc,so=copy.deepcopy(expected)
actual_source_diff=diff(sc,ac)
for v in [sc['work_in_progress'],sc['work_in_progress']['mu_sdk_r369']]:
    v['root_next_failure_ordinal_live']=970;v['later_diagnostics_observed_after_cutoff']=copy.deepcopy(live['pending'])
ck('actual_is_Source_plus_exact_fresh_pending',sc==ac and so==ao,actual_source_diff)
ck('only_four_postseal_leaves',set(actual_source_diff)=={'/work_in_progress/root_next_failure_ordinal_live','/work_in_progress/later_diagnostics_observed_after_cutoff','/work_in_progress/mu_sdk_r369/root_next_failure_ordinal_live','/work_in_progress/mu_sdk_r369/later_diagnostics_observed_after_cutoff'})
ck('CP369_OW173_revisions',ac['revision']==369 and ac['expected_previous_revision']==368 and ao['revision']==173 and oc['revision']==368 and oo['revision']==172)
ck('old950_exact_13_added',len(oc['failure_counters'])==950 and ac['failure_counters'][:950]==oc['failure_counters'] and len(ac['failure_counters'])==963)
ck('13_ordinal_origins_once',[r['original_payload']['observed_ordinal'] for r in ac['failure_counters'][950:]]==list(range(953,966)) and len({r['origin_key'] for r in ac['failure_counters'][950:]})==13)
for d,a in zip(facts['diagnostics'],ac['failure_counters'][950:]):
    read(d['origin_ref'])
    ck('diagnostic_fidelity:'+str(d['ordinal']),a['evidence_ref']==a['original_payload']['immutable_origin_ref']==d['origin_ref'] and all(a['original_payload'][k]==d[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit','origin_selector','exit_qualification']) and a['counted_once'] is True and a['counter_reset'] is False and a['automatic_retry'] is False)
ck('Root_two_parents',ac['work_in_progress']['construction_active_parents']==oc['work_in_progress']['construction_active_parents']==['W05','W09'] and ao['active_integrator']==oo['active_integrator'] and ao['active_integrator']['id']=='codex:/root' and ao['shared_integrator']==oo['shared_integrator'])
ck('W05_ownership_unchanged',ao['card_path_bindings']['W05-99']==oo['card_path_bindings']['W05-99'])
ck('W09_parent_owner_unchanged',ao['card_path_bindings']['W09-99']['owner']==oo['card_path_bindings']['W09-99']['owner'])
owner=facts['owner'];worker=facts['worker'];key=next(k for k,v in ao['card_path_bindings']['W09-99']['subtasks'].items() if v==owner)
ck('45scope17owner9worker',len(scope)==45 and len(owner)==17 and len(worker)==9 and set(scope)==set(contract['scope_required_fields']) and set(owner)==set(contract['owner_fields']) and set(worker)==set(contract['worker_fields']))
ck('exact_owner_and_single_worker',ao['card_path_bindings']['W09-99']['subtasks'][key]==owner and [w for w in ac['workers'] if w.get('slice_id')==worker['slice_id']]==[worker])
ic,io=copy.deepcopy(ac),copy.deepcopy(ao)
for k in ['failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note']:ic[k]=copy.deepcopy(oc[k])
del io['card_path_bindings']['W09-99']['subtasks'][key]
for k in ['revision','updated_at','updated_by']:io[k]=oo[k]
ck('complete_semantic_inverse',ic==oc and io==oo)
cdiff=diff(oc,ac);odiff=diff(oo,ao)
ck('exact_approved_diff',set(cdiff)<={'/failure_counters','/workers','/expected_previous_revision','/revision','/updated_at','/updated_by','/note','/work_in_progress/mu_sdk_r369','/work_in_progress/root_next_failure_ordinal_live','/work_in_progress/later_diagnostics_observed_after_cutoff'} and set(odiff)<={'/revision','/updated_at','/updated_by','/card_path_bindings/W09-99/subtasks/'+key},dict(CP=cdiff,OW=odiff))
dev=obj(facts['W05_actual_closed_ref']);dh=obj(facts['W05_actual_review_handoff_ref']);dm=obj(facts['W05_actual_review_manifest_ref']);dd=obj(dh['actual_decision_ref'])
ck('W05_dev13_partial_no_native',dev['pass_count']==13 and dev['status']=='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' and dev['native_qualification_accepted'] is False and dd['decision']=='ACTUAL_DEVELOPMENT_13_EVIDENCE_VERIFIED' and dd['qualification']=='COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' and dd['native_qualification_accepted'] is False and ac['work_in_progress']['mu_sdk_r369']['W05_qualification']==dev['status'])
for v in [ac['work_in_progress'],ac['work_in_progress']['mu_sdk_r369']]:
    ck('shared_live_exact',v['root_next_failure_ordinal_live']==970 and v['later_diagnostics_observed_after_cutoff']==live['pending'])
r369=ac['work_in_progress']['mu_sdk_r369']
ck('cutoff_count_and_no_acceptance',r369['registered_failure_count']==963 and r369['highest_registered_ordinal_at_cutoff']==965 and r369['next_failure_ordinal_at_cutoff']==966 and r369['formal_case_accepted_delta']==0 and r369['parent_acceptance'] is False)
ck('proof_admin_only',proof['mode']=='activate' and proof['complete_inverse'] is True and proof['old950_preserved'] is True and proof['new_ordinals']==list(range(953,966)) and proof['registered_count']==963 and proof['live_next']==970 and proof['all_handles_closed'] is True and proof['formal_case_accepted_delta']==0 and proof['parent_acceptance'] is False and proof['Native_executed'] is False)
regio=discovered(N/'registration.actual.original-tool-io.root.json');contextio=discovered(N/'postseal-context.original-tool-io.root.json');prepio=discovered(N/'source-preparation.original-tool-io.root.json')
ck('registration_original_exit0',regio['original_exec_command_result']['chunk_id']=='0cb7fa' and regio['original_exec_command_result']['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in regio['original_exec_command_result']['output'])
ck('registration_exact_facts_context_command',all(s in regio['original_exec_command_args']['cmd'] for s in ['activate',h['facts_ref']['sha256'],str(h['facts_ref']['bytes']),live_ref['path'],live_ref['sha256'],str(live_ref['bytes'])]))
source_guard=obj(sh['guard_cleanup_ref'])
ck('Source_independent_guards_closed',source_guard['closed'] is True and source_guard['verification']=='PASSED' and source_guard['retained_handles_count']==0 and source_guard['errors']==[])
for r in m['members']:
    if Path(r['path']).name=='source_guard.cleanup.check.json':
        ag=obj(r);ck('Source_author_guards_closed',ag['closed'] is True and ag['verification']=='PASSED' and ag['retained_handles_count']==0 and ag['errors']==[])
# Source21 remains frozen; runtime outputs from concurrent Native are outside this review.
for r in scope['source21']:read(r)
pins=obj(next(r for r in sm['members'] if Path(r['path']).name=='verified-input-pins.json'))
gp=next(r for r in pins if r['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')
gm=types.ModuleType('cp369_actual_review_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
held=list(refs.values())
try:
    guard.acquire(held)
    ck('all_finite_review_inputs_held_unchanged',all(guard.get_buffer(r['path'])==raws[str(Path(r['path'])).casefold()] for r in held))
finally:
    cleanup=guard.close();cleanupref=save('review-source-guard.cleanup.actual.json',cleanup)
ck('all_review_handles_closed',cleanup['closed'] is True and cleanup['verification']=='PASSED' and cleanup['errors']==[] and cleanup['retained_handles_count']==0)
inverse=save('complete-canonical-byte-inverse.actual.json',dict(complete_semantic_inverse=ic==oc and io==oo,applied=False,files=[dict(before_ref=r,after_ref=a,whole_before_base64=base64.b64encode(b).decode(),whole_after_base64=base64.b64encode(z).decode()) for r,a,b,z in zip(facts['canonical_refs'],actualrefs,before,after)],changed_paths=dict(CP=cdiff,OW=odiff),source_to_actual_delta_paths=actual_source_diff))
failed=[x for x in checks if not x['passed']];status='ACTUAL_CP369_OW173_REGISTRATION_VERIFIED' if not failed else 'REQUEST_CHANGES'
cr=save('checks.json',dict(count=len(checks),passed=sum(x['passed'] for x in checks),checks=checks));fr=save('findings.json',dict(blocking_findings=len(failed),findings=failed));save('verified-input-pins.json',list(refs.values()))
failure=pin(O/'failure-2f1e13.original-tool-io.json')
dr=save('actual-decision.json',dict(schema='researchos.root-cp369-independent-actual-registration-decision.v1',decision=status,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',scope='CP369_OW173_ADMINISTRATIVE_REGISTRATION_ONLY',source_review_handoff_ref=hr,source_review_manifest_ref=smr,activation_proof_ref=proofref,actual_canonical_refs=actualrefs,postseal_live_context_ref=live_ref,source_cutoff=live['source_cutoff'],registered_originals=list(range(953,966)),registered_failure_count=963,registration_live_next=970,registration_pending=[966,967,968,969],Root_live_next_reported_after_review_diagnostic=971,new_original_failures=[970],original_failure_970_ref=failure,complete_inverse_ref=inverse,scope_field_count=45,owner_field_count=17,worker_field_count=9,W05_qualification='COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',W05_development_tests=13,W05_native_qualification_accepted=False,Native_evidence_reviewed=False,Native_executed_by_reviewer=False,Canon_written_by_reviewer=False,Main_Source_written_by_reviewer=False,execution_grant=False,formal_case_accepted_delta=0,parent_acceptance=False,all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanupref,checks_ref=cr,findings_ref=fr,reviewed_at=datetime.now(timezone.utc).isoformat()))
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(status+'。本轮仅复核已完成的CP369/OW173行政登记，未调用writer、事务或Native入口。实际两份Canon与事务after逐字节相同；before逐字节绑定已审Source，旧950+新增953..965共13一次计数，完整inverse与变更白名单通过。实际与Source提案仅4个postseal live/pending叶不同，共享WIP与mu_sdk_r369皆live970/pending966..969；Root45Scope17Owner9Worker保留。W05为dev13 partial/NativeOPEN，Formal与Parent接受增量0。四份Canon与Main Source21核验，Source及本轮guard均关且0 retained。新970只读路径错误完整保留，Root后报live971，属于下次检查点，未写入冻结Canon。并行Native输出不在本轮审查范围。\n')
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mr=save('MF.json',dict(schema='researchos.root-cp369-independent-actual-registration-manifest.v1',members=members,source_review_handoff_ref=hr,activation_proof_ref=proofref))
hh=save('HDF.json',dict(schema='researchos.root-cp369-independent-actual-registration-handoff.v1',status=status,actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=mr,actual_decision_ref=dr,activation_proof_ref=proofref,actual_canonical_refs=actualrefs,checks=len(checks),blocking_findings=len(failed),held_inputs=len(held),all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],guard_cleanup_ref=cleanupref,Native_evidence_reviewed=False,Native_executed_by_reviewer=False,Canon_written_by_reviewer=False,execution_grant=False,formal_case_accepted_delta=0,parent_acceptance=False,new_original_failures=[970],original_failure_970_ref=failure,STOP=True,FINAL=True))
for r in members+[mr,hh]:
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
print(json.dumps(dict(status=status,checks=len(checks),blocking_findings=len(failed),findings=failed,HDF=hh,MF=mr,decision=dr,held_inputs=len(held)),ensure_ascii=False),flush=True)

