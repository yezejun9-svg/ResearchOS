"""Root closes four observed consumed scopes, preserving every old counter."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys,types
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99';S=Path(__file__).resolve().parent
REG=W/'w09_nf6_root_registration_root/e38d72def3e1427cb9ef0b49dc130ba1'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
GEN='fullw09-20261010-06';SELECTORS=('W09-G01','W09-G02','A06','C19')
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def checked(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref
    return doc(ref['path'])
def module(p,name):
    m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def save(name,value):
    p=O/name;raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
assert len(sys.argv)==7
bundle_ref=dict(path=sys.argv[1],sha256=sys.argv[2],bytes=int(sys.argv[3]))
pending_input_ref=dict(path=sys.argv[4],sha256=sys.argv[5],bytes=int(sys.argv[6]))
bundle=checked(bundle_ref);pending=checked(pending_input_ref);stop=pending['next_original_failure_ordinal']
O=S/('cp384-nf6-consumed-closure-live'+str(stop));assert not O.exists()
current=doc(REG/'native.canonical-vector.json')['refs'];assert [pin(x['path']) for x in current]==current
assert current[0]['sha256']=='56f48380c4ce188162e10109f0353b154525bf669f8bd25a0693886439b86a0e' and current[1]['sha256']=='2e58a528c7edfb410cf9ca0b1665bcb577a479f3eaa36d613e30f0f061d7f3d3'
assert pin(CORE)['sha256']=='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'
assert pin(GUARD)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
assert pin(TP)['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
assert bundle['schema']=='researchos.w09-nf6-four-actual-review-input.v1' and set(bundle)=={'schema','source_review_ref','groups'} and set(bundle['groups'])==set(SELECTORS)
inputs=[bundle_ref,pending_input_ref,pin(CORE),pin(GUARD),pin(TP),pin(REG/'native.canonical-vector.json'),bundle['source_review_ref'],*current[2:]]
closed_runs={}
for key in SELECTORS:
    group=bundle['groups'][key]
    assert set(group)=={'prepare_ref','producer_closed_ref','prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'}
    inputs.extend(group.values());p=checked(group['prepare_ref']);c=checked(group['producer_closed_ref'])
    assert p['stage']=='prepare' and p['status']=='PREPARED_ALL_GUARDS_CLOSED' and p['all_guards_closed'] and p['all_owned_jobs_closed'] and not p['cleanup_errors']
    assert c['schema']=='researchos.w09-four-selector-stage-closed.v2' and c['stage']=='run'
    assert c['all_guards_closed'] and c['all_owned_jobs_closed'] and c['all_cleanup_receipts_saved'] and not c['cleanup_errors']
    assert c['status']=='MAIN_SELECTOR_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW' and c['error'] is None and c['summary']['native_test_exit']==0
    assert len(c['invocation_observations'])==2 and all(x['verified'] and x['job_closed'] for x in c['invocation_observations'])
    for name in ('prepare_completed_Root_capture_ref','run_completed_Root_capture_ref'):
        h=checked(group[name]);assert h['issued_by']=='codex:/root' and h['root_thread_id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
        assert h['actual_outer_exit']==h['actual_python_exit']==0 and h['process_completion_observed'] is True and h['actual_exec_session_id'] is None
        assert pin(h['original_capture_ref']['path'])==h['original_capture_ref'];inputs.append(h['original_capture_ref'])
    for ref in c['invocation_refs']:
        inv=checked(ref);assert inv['actual_outer_exit']==0 and inv['original_error'] is None
        inputs.append(ref)
    inputs.append(c['native_packet_ref'])
    for item in c['guard_cleanups']:
        gr=checked(item['ref']);assert gr['closed'] and gr['retained_handles_count']==0 and not gr['errors'];inputs.append(item['ref'])
    request=checked(c['request_ref']);scope=checked(request['scope_ref'])
    assert scope['generation']==GEN and scope['selector_key']==key and scope['run_id']==c['summary']['run_id']
    inputs.extend([c['request_ref'],request['scope_ref']])
    closed_runs[key]=dict(validation_closed_ref=group['producer_closed_ref'],prepare_ready_ref=group['prepare_ref'],actual_outer_exit=0,actual_python_exit=0,actual_Native_exit=0,actual_Go_exit=0,all_guards_closed=True,all_owned_jobs_closed=True,automatic_retry=False,formal_acceptance=False,**{k:v for k,v in group.items() if 'Root_capture' in k})
for row in pending['pending']:
    inputs.extend([row['origin_ref'],row['capture_binding_ref'],*row.get('source_fact_refs',[])])
inputs=list({x['path']:x for x in inputs}.values());assert not any(x['path'] in [y['path'] for y in current[:2]] for x in inputs)
O.mkdir();(O/'canonical-journal').mkdir()
g=module(GUARD,'root_nf6_close_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(inputs);core=module(CORE,'root_nf6_close_core');tp=module(TP,'root_nf6_close_tp')
    now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==383 and ow['revision']==187 and cp['work_in_progress']['root_next_failure_ordinal_live']==1185
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(d,ops,path,value):
            exists,before=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value)));core.put(d,path,value)
        merged,end=core.merge_pending(cp,pending,current);assert end==stop and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],stop)
        workers=copy.deepcopy(cp['workers'])
        for key,actual in closed_runs.items():
            matches=[x for x in workers if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_'+GEN+'_'+key];assert len(matches)==1
            worker=matches[0];ownerkey='full_w09_main_native_producer_'+GEN+'_'+key
            sub=copy.deepcopy(ow['card_path_bindings']['W09-99']['subtasks'][ownerkey])
            assert worker['scope_ref']==sub['scope_ref'] and worker['run_id']==sub['run_id'] and sub['generation']==GEN
            assert worker['state']==sub['state']=='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE'
            values=dict(state='CLOSED_ACTUAL_NATIVE_PENDING_FORMAL_MODE',closed_at=now,actual_closed=actual,one_shot_consumed=True,future_execution_permitted=False,formal_acceptance=False)
            worker.update(values);sub.update(values);change(o,oo,['card_path_bindings','W09-99','subtasks',ownerkey],sub)
        change(c,co,['workers'],workers)
        change(c,co,['work_in_progress','cp384_consumed_nf6_native_closure'],dict(native_closed=closed_runs,bundle_ref=bundle_ref,pending_ref=pending_input_ref,registered_through=stop-1,next_original_failure_ordinal=stop,formal_case_accepted_delta=0,parent_acceptance=False,counter_reset=False))
        for key,val in dict(revision=384,expected_previous_revision=383,updated_at=now,updated_by='codex:/root',note='Close four consumed actual NF6 Native scopes; append complete original diagnostics once. Formal acceptance remains unchanged.').items():change(c,co,[key],val)
        for key,val in dict(revision=188,updated_at=now,updated_by='codex:/root').items():change(o,oo,[key],val)
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        assert c['work_in_progress']['w09_native_producer_scope_generations']==cp['work_in_progress']['w09_native_producer_scope_generations']
        save('complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    result_ref=save('closure.committed.root.json',dict(result,formal_acceptance=False,registered_through=stop-1,next_original_failure_ordinal=stop,counter_reset=False))
finally:
    closed=g.close();guard_ref=save('source-guard.closed.root.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
assert all(pin(x['path'])==x for x in current[2:])
print(json.dumps(dict(closure_ref=result_ref,source_guard_closed_ref=guard_ref,after_canonical_refs=[pin(V/p) for p in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],registered_through=stop-1,next_original_failure_ordinal=stop,formal_acceptance=False),ensure_ascii=False))
