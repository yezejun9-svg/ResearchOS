"""Register only a separate Root Main C19 native owner; preserve historical acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import types
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
BASE=B/'checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009/register_cp368.source.py'
BASE_REF=dict(path=str(BASE),sha256='05079c1be355bd7a55bafaa840b278a0030a681b8aef23cb592ff269b3775d03',bytes=15197)
def require(v,msg):
    if not v:raise ValueError(msg)
raw=BASE.read_bytes();require(hashlib.sha256(raw).hexdigest()==BASE_REF['sha256'] and len(raw)==BASE_REF['bytes'],'TRUSTED_BASE_HELPERS')
base=types.ModuleType('cp369_base');base.__file__=str(BASE);sys.modules[base.__name__]=base;exec(compile(raw,str(BASE),'exec'),base.__dict__)
pin,read,load,pair,encoded,module=base.pin,base.read,base.load,base.pair,base.encoded,base.module
CANON=base.CANON
BEFORE=[('51c038a8f6de8415f66dfd0122241989591dd7ba0dad4adf0560e2bf6d7f52ac',4347568),('07b0aeea2b6bb84acde4982be576f7a7cbb22e04a76e5c89216ae3e43231048d',202735),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
KEY='c19_main_root_native_producer';SLICE='C19_MAIN_ROOT_NATIVE_PRODUCER';ACTOR='codex:/root';STATE='ROOT_REGISTERED_PENDING_MAIN_C19_NATIVE'
def save(name,obj):
    require(Path(name).name==name,'LOCAL_RECEIPT_ONLY')
    with (N/name).open('xb') as f:f.write(encoded(obj));f.flush();os.fsync(f.fileno())
    return pin(N/name)
def validate_live(live):
    require(type(live) is dict and set(live)=={'schema','issued_by','created_utc','source_cutoff','next_original_failure_ordinal','pending'},'LIVE_EXACT_FIELDS')
    require(live['schema']=='researchos.root-postseal-live-diagnostic-context.v1' and live['issued_by']==ACTOR and type(live['created_utc']) is str and live['created_utc'],'ROOT_LIVE')
    require(live['source_cutoff']=={'highest_ordinal':965,'next_failure_ordinal':966},'EXACT_SOURCE_CUTOFF')
    next_live=live['next_original_failure_ordinal'];require(type(next_live) is int and next_live>=966 and type(live['pending']) is list,'NO_RESET')
    require([v['ordinal'] for v in live['pending']]==list(range(966,next_live)),'EXACT_POSTCUT_ORIGINALS')
    for v in live['pending']:
        require(type(v['ordinal']) is int and set(v)=={'ordinal','origin_ref','description'} and type(v['description']) is str,'TYPED_PENDING');read(v['origin_ref'])
def scope_bindings(facts):
    s=load(facts['scope_ref']);contract=load(facts['calling_contract_ref']);choice=load(s['choice_ref'])
    require(set(s)==set(contract['scope_required_fields']) and s['schema']==contract['root_scope_schema'] and s['status']==contract['root_scope_status'],'EXACT_NATIVE_SCOPE_SCHEMA')
    require(s['issued_by']==s['executor']==ACTOR,'ROOT_EXPLICIT_SCOPE')
    for k in ('formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry'):require(s[k] is False,'NO_'+k)
    for k in ('formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes'):require(type(s[k]) is int and s[k]==0,'ZERO_'+k)
    for k in ('maximum_go_test_runs','maximum_go_list_runs'):require(type(s[k]) is int and s[k]==1,'SINGLE_'+k)
    for k,n in (('list_timeout_seconds',240),('producer_timeout_seconds',420),('inner_Go_timeout_seconds',180)):require(type(s[k]) is int and s[k]==n,'TIMEOUT_'+k)
    for k in ('source_root','run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids','source21','main_seven_after_refs'):require(s[k]==choice[k],'EXACT_CHOICE_'+k)
    require({k:s[k] for k in contract['bound_source_refs']}==contract['bound_source_refs'],'EXACT_ALL_RUNTIME_CALLERS')
    h,_=pair(s['source_handoff_ref'],s['source_manifest_ref']);rh,refs=pair(s['source_review_handoff_ref'],s['source_review_manifest_ref']);d=load(s['source_review_decision_ref'])
    require(h['actor_id']=='codex:/root/command_queue_impl' and rh['source_decision_ref']==s['source_review_decision_ref'] and s['source_review_decision_ref'] in refs,'EXACT_PRODUCER_SOURCE_AND_REVIEW')
    require(d['schema']=='researchos.w09-main-c19-producer-independent-source-decision.v1' and d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SINGLE_MAIN_C19_PRODUCER' and d['actor_role']=='INDEPENDENT_NON_AUTHOR' and d['actor_id']==rh['actor_id'] and d['actor_id'] not in (ACTOR,h['actor_id']),'REAL_NONAUTHOR_SOURCE_ACCEPTED')
    for k in ('source_handoff_ref','source_manifest_ref','prepare_caller_ref','producer_caller_ref','launcher_ref','runtime_ref','choice_ref','compiler_blueprint_ref','run_id','output_root','source21'):require(d[k]==s[k],'SOURCE_REVIEW_FULL_BINDING_'+k)
    require(d['calling_contract_ref']==facts['calling_contract_ref'] and d['actual_executed'] is False and type(d['formal_case_accepted_delta']) is int and d['formal_case_accepted_delta']==0,'SOURCE_REVIEW_NOT_ACTUAL')
    ah,arefs=pair(s['adoption_review_handoff_ref'],s['adoption_review_manifest_ref']);ad=load(s['adoption_review_decision_ref']);outcome=load(s['adoption_outcome_ref'])
    require(ah['actual_decision_ref']==s['adoption_review_decision_ref'] and s['adoption_review_decision_ref'] in arefs,'ADOPTION_REVIEW_MEMBER')
    require(ad['schema']=='researchos.w09-main-c19-independent-adoption-decision.v1' and ad['decision']=='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED' and ad['actor_role']=='INDEPENDENT_NON_AUTHOR' and ad['actor_id']==ah['actor_id'] and ad['actor_id'] not in (ACTOR,h['actor_id']),'NONAUTHOR_ACTUAL_ADOPTION')
    require(ad['adoption_outcome_ref']==s['adoption_outcome_ref'] and ad['source_handoff_ref']==choice['adoption_source_handoff_ref'] and ad['source_manifest_ref']==choice['adoption_source_manifest_ref'] and ad['final_target_refs']==s['main_seven_after_refs'] and ad['source21']==s['source21'],'CURRENT_ADOPTION_FULL_BINDING')
    require(ad['all_handles_closed'] is True and ad['formal_acceptance'] is False and type(ad['formal_case_accepted_delta']) is int and ad['formal_case_accepted_delta']==0,'ADOPTION_CLOSED_NONFORMAL')
    require(outcome['status']=='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' and outcome['transaction']['status']=='SEVEN_SOURCE_TARGETS_COMMITTED' and outcome['final_target_refs']==s['main_seven_after_refs'],'ACTUAL_MAIN_SOURCE_CURRENT')
    for ref in s['main_seven_after_refs']+s['source21']:read(ref)
    owner=dict(owner=ACTOR,current_source_writer=None,state=STATE,scope_ref=facts['scope_ref'],source_handoff_ref=s['source_handoff_ref'],source_manifest_ref=s['source_manifest_ref'],source_review_handoff_ref=s['source_review_handoff_ref'],source_review_manifest_ref=s['source_review_manifest_ref'],adoption_outcome_ref=s['adoption_outcome_ref'],adoption_review_handoff_ref=s['adoption_review_handoff_ref'],source_root=s['source_root'],run_id=s['run_id'],receipt_root=s['receipt_root'],scratch_root=s['scratch_root'],output_root=s['output_root'],formal_case_accepted_delta=0,parent_acceptance=False)
    worker=dict(step_id='W09-99',slice_id=SLICE,owner=ACTOR,state=STATE,scope_ref=facts['scope_ref'],source_handoff_ref=s['source_handoff_ref'],source_review_handoff_ref=s['source_review_handoff_ref'],adoption_outcome_ref=s['adoption_outcome_ref'],run_id=s['run_id'])
    require(set(owner)==set(contract['owner_fields']) and set(worker)==set(contract['worker_fields']) and owner==facts['owner'] and worker==facts['worker'],'EXACT_OWNER_WORKER_FIELDS')
    return s,owner,worker
def transform(c,o,facts,fr,old_c,old_o,live):
    validate_live(live);s,owner,worker=scope_bindings(facts)
    require(c==old_c and o==old_o and c['revision']==368 and o['revision']==172,'CURRENT_BEFORE_PAIR')
    require(c['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and c['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb','PROJECT_HEAD')
    require(len(c['failure_counters'])==950 and c['work_in_progress']['construction_active_parents']==['W05','W09'],'OLD950_AND_TWO_PARENTS')
    require(o['active_integrator']['id']==ACTOR and o['shared_integrator']=='qoder-desktop:/root/platform_owner' and o['card_path_bindings']['W09-99']['owner']==ACTOR,'ROOT_GOVERNANCE')
    require(KEY not in o['card_path_bindings']['W09-99']['subtasks'] and not any(v.get('slice_id')==SLICE for v in c['workers']),'NEW_UNIQUE_NATIVE_OWNER')
    require([v['ordinal'] for v in facts['diagnostics']]==list(range(953,966)),'EXACT13_ORIGINALS')
    seen={v.get('origin_key') for v in c['failure_counters']}
    for v in facts['diagnostics']:
        ref=v['origin_ref'];read(ref);require(type(v['ordinal']) is int,'ORDINAL_INT')
        for k in ('actual_outer_exit','actual_python_exit','actual_native_exit'):require(v[k] is None or type(v[k]) is int,'OBSERVED_EXIT_OR_NULL')
        key=hashlib.sha256((ref['sha256']+'#'+str(v['ordinal'])).encode()).hexdigest();require(key not in seen,'UNIQUE_ORIGINAL_ONCE');seen.add(key)
        c['failure_counters'].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=v['ordinal'],immutable_origin_ref=ref,actual_outer_exit=v['actual_outer_exit'],actual_python_exit=v['actual_python_exit'],actual_native_exit=v['actual_native_exit'],diagnostic=v['description'],origin_selector=v['origin_selector'],exit_qualification=v['exit_qualification']),counted_once=True,counter_reset=False,automatic_retry=False))
    c['workers'].append(worker);o['card_path_bindings']['W09-99']['subtasks'][KEY]=owner
    w=c['work_in_progress'];require('mu_sdk_r369' not in w,'UNIQUE_WIP');w['mu_sdk_r369']=dict(scope_ref=facts['scope_ref'],facts_ref=fr,Source_status='INDEPENDENT_SOURCE_ACCEPTED',Main_C19_native_status=STATE,W05_actual_development_closed_ref=facts['W05_actual_closed_ref'],W05_qualification='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',registered_failure_count=963,highest_registered_ordinal_at_cutoff=965,next_failure_ordinal_at_cutoff=966,root_next_failure_ordinal_live=live['next_original_failure_ordinal'],later_diagnostics_observed_after_cutoff=copy.deepcopy(live['pending']),formal_case_accepted_delta=0,parent_acceptance=False)
    w['root_next_failure_ordinal_live']=live['next_original_failure_ordinal'];w['later_diagnostics_observed_after_cutoff']=copy.deepcopy(live['pending'])
    c.update(expected_previous_revision=368,revision=369,updated_at=facts['created_utc'],updated_by=ACTOR,note=facts['checkpoint_note']);o.update(revision=173,updated_at=facts['created_utc'],updated_by=ACTOR)
    inverse_c=copy.deepcopy(c)
    for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'):inverse_c[k]=copy.deepcopy(old_c[k])
    inverse_o=copy.deepcopy(o);del inverse_o['card_path_bindings']['W09-99']['subtasks'][KEY]
    for k in ('revision','updated_at','updated_by'):inverse_o[k]=old_o[k]
    require(inverse_c==old_c and inverse_o==old_o,'COMPLETE_CANONICAL_INVERSE');require(c['failure_counters'][:950]==old_c['failure_counters'] and len(c['failure_counters'])==963,'OLD950_PRESERVED')
    return c,o
def execute(mode,fr,lr):
    require(mode in ('check','activate'),'MODE');facts=load(fr);live=load(lr);validate_live(live)
    require(facts['schema']=='researchos.root-cp369-native-registration-facts.v1' and facts['formal_acceptance'] is False,'FACTS_SCHEMA')
    cr=[dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size) for p,(sha,size) in zip(CANON,BEFORE)];require(cr==facts['canonical_refs'],'EXACT_FOUR_BEFORE')
    raws=[read(r) for r in cr];old_c,old_o=[json.loads(r) for r in raws[:2]]
    gp=dict(path=str(base.GP),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404);tp=dict(path=str(base.TP),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877)
    require(pin(sys.executable)['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','LOCKED_PYTHON')
    gm=module(gp);tm=module(tp)
    refs=[fr,lr,BASE_REF,pin(__file__),pin(sys.executable),gp,tp,*cr[2:],facts['scope_ref'],facts['calling_contract_ref'],facts['W05_actual_closed_ref']]
    for p in facts['pairs']:
        _,items=pair(p['handoff_ref'],p['manifest_ref']);refs.extend(items)
    refs+=facts['input_refs']+[v['origin_ref'] for v in facts['diagnostics']]+[v['origin_ref'] for v in live['pending']]
    for m in tuple(sys.modules.values()):
        for k in ('__file__','__cached__'):
            p=getattr(m,k,None)
            if p and Path(p).is_file():refs.append(pin(p))
    unique={}
    for ref in refs:
        read(ref);key=ref['path'].casefold();require(key not in unique or unique[key]==ref,'SAME_UNIQUE_PIN');unique[key]=ref
    require(not any(str(p).casefold() in unique for p in CANON[:2]),'CANON_PAIR_NOT_SOURCE_GUARD_LOCKED')
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
    try:
        proposed=transform(copy.deepcopy(old_c),copy.deepcopy(old_o),facts,fr,old_c,old_o,live)
        if mode=='activate':transaction=tm.update_pair(cr[:2],lambda c,o:transform(c,o,facts,fr,old_c,old_o,live),N,'activate');require([p.read_bytes() for p in CANON[2:]]==raws[2:],'SS_COMMANDS_UNCHANGED')
        else:transaction=None;require([p.read_bytes() for p in CANON]==raws,'NO_SOURCE_CANON_WRITES')
    finally:
        cleanup=guard.close();save('source_guard.cleanup.'+mode+'.json',cleanup);require(cleanup['closed'] is True and cleanup['errors']==[] and cleanup['retained_handles_count']==0,'SOURCE_GUARD_CLOSED')
    proof=dict(mode=mode,transaction=transaction,complete_inverse=True,old950_preserved=True,new_ordinals=list(range(953,966)),registered_count=963,highest_cutoff=965,next_cutoff=966,live_next=live['next_original_failure_ordinal'],all_handles_closed=True,formal_case_accepted_delta=0,parent_acceptance=False,Native_executed=False,proposed_refs=[dict(path=str(p),sha256=hashlib.sha256(encoded(v)).hexdigest(),bytes=len(encoded(v))) for p,v in zip(CANON,proposed)])
    return save('canonical_pair.'+mode+'.json',proof)
def main():
    require(len(sys.argv)==7,'MODE FACTS_SHA FACTS_BYTES LIVE_PATH LIVE_SHA LIVE_BYTES')
    fr=dict(path=str((N/'checkpoint.execution.facts.json').resolve(strict=True)),sha256=sys.argv[2],bytes=int(sys.argv[3]));lr=dict(path=sys.argv[4],sha256=sys.argv[5],bytes=int(sys.argv[6]))
    print(json.dumps(execute(sys.argv[1],fr,lr),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
