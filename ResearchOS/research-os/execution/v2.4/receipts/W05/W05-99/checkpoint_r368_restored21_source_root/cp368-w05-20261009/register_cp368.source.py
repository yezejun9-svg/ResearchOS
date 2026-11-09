"""Root-only CP368 W05 bounded development authorization; no product acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
CANON=[R/'execution/v2.4'/f'{s}.json' for s in ('checkpoint','path_ownership','step_state','commands')]
BEFORE=[('5783d88c6f8841e32cc328e1fe1332162fad8ffdcf8125fecdb491a46a198a0f',4336749),('d307def27771aba3e07351e553ad562003bbf57bb885bf0efb650ea7c721239c',200160),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
GP=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
KEY='restored21_v3_root_development'
SLICE='RESTORED21_V3_BOUNDED_DEVELOPMENT'
ACTOR='codex:/root'
STATE='ROOT_REGISTERED_PENDING_RESTORED21_V3_DEVELOPMENT'

def require(ok,label):
    if not ok:raise ValueError(label)
def encoded(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    require(len(raw)<=256*1024*1024,'PIN_CAP')
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'EXACT_REF')
    require(type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) and type(ref['bytes']) is int and 0<=ref['bytes']<=256*1024*1024,'TYPED_REF')
    p=Path(ref['path']);require(p.is_absolute() and str(p.resolve(strict=True))==ref['path'],'CANONICAL_REF_PATH')
    raw=p.read_bytes();require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'REF_DRIFT')
    return raw
def load(ref):return json.loads(read(ref))
def normalized(ref):return dict(path=str(Path(ref['path']).resolve(strict=True)),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
def save(name,obj):
    require(Path(name).name==name,'LOCAL_RECEIPT_NAME')
    p=N/name
    with p.open('xb') as f:f.write(encoded(obj));f.flush();os.fsync(f.fileno())
    return pin(p)
def module(ref):
    m=types.ModuleType('cp368_'+Path(ref['path']).stem);m.__file__=ref['path'];sys.modules[m.__name__]=m
    exec(compile(read(ref),ref['path'],'exec'),m.__dict__);return m
def pair(href,mref):
    h=load(href);m=load(mref);require(h['manifest_ref']==mref,'PAIR_BINDING')
    members=m['members'];members=list(members.values()) if type(members) is dict else members
    refs=[href,mref]
    for v in members:
        ref=dict(path=str(Path(v['path']).resolve(strict=True)),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']);read(ref);refs.append(ref)
    return h,refs
def scope_bindings(facts):
    scope=load(facts['scope_ref']);h=load(scope['source_handoff_ref']);review=load(scope['source_review_handoff_ref']);contract=load(scope['contract_ref'])
    require(scope['schema']=='researchos.root-restored21-v3-development-scope.v1' and scope['status']=='ROOT_AUTHORIZED_SINGLE_BOUNDED_RESTORED21_DEVELOPMENT_RUN','SCOPE_SCHEMA')
    require(scope['issued_by']==scope['executor']==ACTOR,'ROOT_SCOPE')
    require(h['manifest_ref']==scope['source_manifest_ref'] and h['contract_ref']==scope['contract_ref'],'SOURCE_BINDING')
    require(review['manifest_ref']==scope['source_review_manifest_ref'] and review['status']=='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY','NONSELF_SOURCE_ACCEPTED')
    guidance=load(scope['root_execution_guidance_ref'])
    require(guidance['source_handoff_ref']==scope['source_handoff_ref'] and guidance['source_manifest_ref']==scope['source_manifest_ref'],'REVIEW_FULL_SOURCE_BINDING')
    for k in ('worktree','environment','isolation_output','validation_output'):
        require(scope[k]==contract[k]==guidance[k],'FIXED_PATH_'+k)
    require(scope['exact_source_roster_ref']==normalized(contract['exact_source_roster']),'ROSTER_BINDING')
    for field,name in (('prepare_caller_ref','prepare_root_actual.py'),('validator_ref','validate_root_actual.py')):
        require(scope[field]==pin(Path(scope['source_handoff_ref']['path']).parent/name),'EXACT_CALLER_'+field)
    require(scope['maximum_unique_tests']==13 and type(scope['maximum_unique_tests']) is int and scope['maximum_actual_attempts']==1 and type(scope['maximum_actual_attempts']) is int,'BOUNDED_ONCE')
    require(scope['qualification_ceiling']=='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN','PARTIAL_CEILING')
    for k in ('formal_dispatcher','formal_acceptance','Main_adoption','production_DB_writes','external_model_calls','automatic_retry','parent_acceptance'):
        require(scope[k] is False,'SCOPE_NO_'+k)
    require(type(scope['formal_case_accepted_delta']) is int and scope['formal_case_accepted_delta']==0,'NO_FORMAL_DELTA')
    ad=load(facts['adoption_review_decision_ref']);ah=load(facts['adoption_review_handoff_ref']);outcome=load(facts['adoption_outcome_ref'])
    require(ah['manifest_ref']==facts['adoption_review_manifest_ref'] and ah['actual_decision_ref']==facts['adoption_review_decision_ref'] and ah['actor_id']==ad['actor_id'],'ACTUAL_ADOPTION_REVIEW_BINDING')
    require(ad['schema']=='researchos.w09-main-c19-independent-adoption-decision.v1' and ad['decision']=='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED' and ad['actor_role']=='INDEPENDENT_NON_AUTHOR' and ad['actor_id'] not in (ACTOR,'codex:/root/command_queue_impl'),'ACTUAL_ADOPTION_NONAUTHOR')
    require(ad['adoption_outcome_ref']==facts['adoption_outcome_ref'] and ad['final_target_refs']==outcome['final_target_refs'] and ad['all_handles_closed'] is True and ad['formal_acceptance'] is False and type(ad['formal_case_accepted_delta']) is int and ad['formal_case_accepted_delta']==0,'ACTUAL_ADOPTION_CLOSED')
    require(outcome['status']=='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' and outcome['transaction']['status']=='SEVEN_SOURCE_TARGETS_COMMITTED','ACTUAL_SOURCE_ADOPTED')
    for ref in ad['source21']+ad['final_target_refs']:read(ref)
    owner={k:copy.deepcopy(scope[k]) for k in ('source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','worktree','environment','isolation_output','validation_output')}
    owner.update(owner=ACTOR,current_source_writer=None,state=STATE,scope_ref=facts['scope_ref'],formal_case_accepted_delta=0,parent_acceptance=False)
    worker=dict(step_id='W05-99',slice_id=SLICE,owner=ACTOR,state=STATE,scope_ref=facts['scope_ref'],source_handoff_ref=scope['source_handoff_ref'],source_review_handoff_ref=scope['source_review_handoff_ref'],worktree=scope['worktree'])
    require(facts['owner']==owner and facts['worker']==worker,'EXACT_OWNER_WORKER')
    return scope,owner,worker
def validate_live(live):
    require(type(live) is dict and set(live)=={'schema','issued_by','created_utc','source_cutoff','next_original_failure_ordinal','pending'},'LIVE_FIELDS')
    require(live['schema']=='researchos.root-postseal-live-diagnostic-context.v1' and live['issued_by']==ACTOR and type(live['created_utc']) is str and live['created_utc'],'ROOT_LIVE')
    require(live['source_cutoff']=={'highest_ordinal':952,'next_failure_ordinal':953},'SOURCE_CUTOFF')
    require(type(live['next_original_failure_ordinal']) is int and live['next_original_failure_ordinal']>=953 and type(live['pending']) is list,'LIVE_NOT_RESET')
    require([v['ordinal'] for v in live['pending']]==list(range(953,live['next_original_failure_ordinal'])),'EXACT_LATER_ORIGINALS')
    for v in live['pending']:
        require(set(v)=={'ordinal','origin_ref','description'} and type(v['ordinal']) is int and type(v['description']) is str,'PENDING_TYPED_ROW');read(v['origin_ref'])
def transform(c,o,facts,fr,old_c,old_o,live):
    validate_live(live);scope,owner,worker=scope_bindings(facts)
    require(c==old_c and o==old_o and c['revision']==367 and o['revision']==171,'EXACT_CURRENT_PAIR')
    require(c['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and c['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb','PROJECT_HEAD')
    require(len(c['failure_counters'])==949 and c['work_in_progress']['construction_active_parents']==['W05','W09'],'COUNTS_AND_TWO_PARENTS')
    require(o['active_integrator']['id']==ACTOR and o['shared_integrator']=='qoder-desktop:/root/platform_owner' and o['card_path_bindings']['W05-99']['owner']==scope['historical_W05_parent_owner'],'PRESERVE_W05_PARENT_OWNER')
    require(KEY not in o['card_path_bindings']['W05-99']['subtasks'] and not any(v.get('slice_id')==SLICE for v in c['workers']),'NEW_UNIQUE_SUBTASK')
    item=facts['diagnostic'];require(item['ordinal']==952 and item['actual_outer_exit']==1 and item['actual_python_exit'] is None and item['actual_native_exit'] is None,'ORIGINAL952_EXITS')
    ref=item['origin_ref'];read(ref);key=hashlib.sha256((ref['sha256']+'#952').encode()).hexdigest()
    require(key not in {v.get('origin_key') for v in c['failure_counters']},'ONCE_ORIGINAL_KEY')
    c['failure_counters'].append(dict(origin_key=key,evidence_ref=ref,original_payload=dict(observed_ordinal=952,immutable_origin_ref=ref,actual_outer_exit=1,actual_python_exit=None,actual_native_exit=None,diagnostic=item['description'],origin_selector=item['origin_selector'],exit_qualification=item['exit_qualification']),counted_once=True,counter_reset=False,automatic_retry=False))
    c['workers'].append(worker);o['card_path_bindings']['W05-99']['subtasks'][KEY]=owner
    require('mu_sdk_r368' not in c['work_in_progress'],'UNIQUE_WIP')
    c['work_in_progress']['mu_sdk_r368']=dict(scope_ref=facts['scope_ref'],facts_ref=fr,Main7_source_adopted=True,Main7_actual_review_handoff_ref=facts['adoption_review_handoff_ref'],Main7_actual_review_manifest_ref=facts['adoption_review_manifest_ref'],adoption_outcome_ref=facts['adoption_outcome_ref'],W05_actual_status=STATE,W05_qualification_ceiling=scope['qualification_ceiling'],W09_Main_native_status='SOURCE_REJECTED_PENDING_CLEANUP_REPAIR_NO_ACTUAL',registered_failure_count=950,highest_registered_ordinal_at_cutoff=952,next_failure_ordinal_at_cutoff=953,root_next_failure_ordinal_live=live['next_original_failure_ordinal'],later_diagnostics_observed_after_cutoff=copy.deepcopy(live['pending']),formal_case_accepted_delta=0,parent_acceptance=False)
    c.update(expected_previous_revision=367,revision=368,updated_at=facts['created_utc'],updated_by=ACTOR,note=facts['checkpoint_note'])
    o.update(revision=172,updated_at=facts['created_utc'],updated_by=ACTOR)
    inverse_c=copy.deepcopy(c);inverse_c['failure_counters']=copy.deepcopy(old_c['failure_counters']);inverse_c['workers']=copy.deepcopy(old_c['workers']);del inverse_c['work_in_progress']['mu_sdk_r368']
    for k in ('expected_previous_revision','revision','updated_at','updated_by','note'):inverse_c[k]=old_c[k]
    inverse_o=copy.deepcopy(o);del inverse_o['card_path_bindings']['W05-99']['subtasks'][KEY]
    for k in ('revision','updated_at','updated_by'):inverse_o[k]=old_o[k]
    require(inverse_c==old_c and inverse_o==old_o,'COMPLETE_CANONICAL_INVERSE')
    require(c['failure_counters'][:949]==old_c['failure_counters'] and len(c['failure_counters'])==950,'OLD949_PRESERVED')
    return c,o
def execute(mode,fr,live_ref):
    require(mode in ('check','activate'),'MODE');facts=load(fr);live=load(live_ref);validate_live(live)
    require(facts['schema']=='researchos.root-cp368-w05-development-registration-facts.v1' and facts['formal_acceptance'] is False,'FACTS_SCHEMA')
    refs_c=[dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size) for p,(sha,size) in zip(CANON,BEFORE)]
    require(facts['canonical_refs']==refs_c,'EXACT_FOUR_CURRENT')
    raw=[read(v) for v in refs_c];old_c,old_o=[json.loads(v) for v in raw[:2]]
    gp=dict(path=str(GP.resolve(strict=True)),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
    tp=dict(path=str(TP.resolve(strict=True)),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=6877)
    require(pin(sys.executable)['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','PINNED_PYTHON')
    gm=module(gp);tm=module(tp)
    refs=[fr,live_ref,pin(__file__),pin(sys.executable),gp,tp,*refs_c[2:],facts['scope_ref'],facts['diagnostic']['origin_ref'],facts['adoption_outcome_ref']]
    for p in facts['pairs']:
        _,held=pair(p['handoff_ref'],p['manifest_ref']);refs.extend(held)
    refs.extend(facts['input_refs']);refs.extend(v['origin_ref'] for v in live['pending'])
    for m in tuple(sys.modules.values()):
        for name in ('__file__','__cached__'):
            p=getattr(m,name,None)
            if p and Path(p).is_file():refs.append(pin(p))
    unique={}
    for ref in refs:
        read(ref);key=ref['path'].casefold();require(key not in unique or unique[key]==ref,'UNIQUE_INPUT');unique[key]=ref
    require(not any(str(p).casefold() in unique for p in CANON[:2]),'CANON_PAIR_EXCLUSIVELY_OWNED_BY_TRANSACTION_ONLY')
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);cleanup=None;guard.acquire(list(unique.values()))
    try:
        require(guard.get_buffer(fr['path'])==read(fr),'HELD_FACTS')
        proposed=transform(copy.deepcopy(old_c),copy.deepcopy(old_o),facts,fr,old_c,old_o,live)
        if mode=='check':
            transaction=None
            require([p.read_bytes() for p in CANON]==raw,'SOURCE_STAGE_NO_CANON_WRITES')
        else:
            transaction=tm.update_pair(refs_c[:2],lambda c,o:transform(c,o,facts,fr,old_c,old_o,live),N,'activate')
            require([p.read_bytes() for p in CANON[2:]]==raw[2:],'SS_COMMANDS_UNCHANGED')
    finally:
        cleanup=guard.close();save('source_guard.cleanup.'+mode+'.json',cleanup)
        require(cleanup['closed'] is True and cleanup['errors']==[] and cleanup['retained_handles_count']==0,'GUARD_CLOSED')
    proof=dict(mode=mode,transaction=transaction,canonical_refs=refs_c,proposed_refs=[dict(path=str(p),sha256=hashlib.sha256(encoded(v)).hexdigest(),bytes=len(encoded(v))) for p,v in zip(CANON,proposed)],old949_preserved=True,complete_semantic_inverse=True,new_original_ordinals=[952],registered_count=950,cutoff_next=953,live_next=live['next_original_failure_ordinal'],all_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0,Main_native_executed=False)
    return save('canonical_pair.'+mode+'.json',proof)
def main():
    require(len(sys.argv)==7,'MODE FACTS_SHA FACTS_BYTES LIVE_PATH LIVE_SHA LIVE_BYTES')
    fr=dict(path=str((N/'checkpoint.execution.facts.json').resolve(strict=True)),sha256=sys.argv[2],bytes=int(sys.argv[3]));lr=dict(path=sys.argv[4],sha256=sys.argv[5],bytes=int(sys.argv[6]))
    print(json.dumps(execute(sys.argv[1],fr,lr),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
