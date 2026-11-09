"""Close consumed registrations and append the complete original diagnostic suffix."""
from pathlib import Path
from datetime import datetime, timezone
import copy,hashlib,json,os,re,sys,types
R=Path('D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4';W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99';S=Path(__file__).resolve().parent
O=S/'cp380-native-public-closure-live1162'
CORE=W/'w09_nf4_root_registration_source_codex/register-20261010-02/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    p=O/name;raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
def module(p,name):
    m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def documents(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from documents(x)
    elif isinstance(v,list):
        for x in v:yield from documents(x)
    elif isinstance(v,str):
        try:x=json.loads(v)
        except ValueError:return
        yield from documents(x)
current=[pin(V/p) for p in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='75e0edf1897655f93be4331fad91fe453ff49f1465f63e0ca730ba8a7f477c08'
assert current[1]['sha256']=='4a1bd8d0cf3ba4efd7b60072797f4b07f4a48d76d3358c65160967a9f95fe938'
assert pin(CORE)['sha256']=='05cc0bf92d94372ebfcdb19322b2b90fb93aab27e288331413710d1d89d41e1d'
assert pin(TP)['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
assert pin(GUARD)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
draft=W/'pending_diagnostic_inputs_source_codex/pending1149-1153-20261010-01/pending-diagnostic-inputs.draft.json'
rows=copy.deepcopy(doc(draft)['pending'])
extra={
1154:(B/'schema21_public_runtime_independent_review_codex/review-runtime-public21-20261010-01/original-1154.binding.json','Foreign contract path spelling was compared as dictionary equality before using the reviewed callee physical identity predicate.'),
1155:(W/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01/original1155.binding.json','Reviewer preparation read partial selector rather than merged common and selector choice; guard not acquired.'),
1156:(S/'original1156.actual-root.binding.json','C19 real Native exit0; outer evidence validation refused reversed exact argv and selected test order. No automatic retry.'),
1157:(S/'original1157.actual-root.binding.json','Root readonly compound query exited1 after an absent guessed Source binding filename; Python and product exits were unobserved.'),
1158:(W/'nf5_c19_main_order_independent_review_codex/review-20261010-01/original-1158.binding.json','Source reviewer guessed an absent producer namespace; actual rg path error2, no guard or product call.'),
1159:(W/'nf5_c19_main_order_independent_review_codex/review-20261010-01/original-1159.binding.json','Root supplied a nonexistent executor_sources path; actual readonly Get-Content failure retained, no product call.'),
1160:(S/'original1160.actual-root.binding.json','Root bundle assembly guessed prepare.ready.json inside producer rather than its actual parent; failed before bundle publication.'),
1161:(Path(sys.argv[1]),'Reviewer input group names disagreed with the supplied explicit bundle contract; failed before guard acquisition.')}
O.mkdir(exist_ok=False);(O/'canonical-journal').mkdir()
for ordinal,(path,description) in extra.items():
    src=doc(path);rr=src.get('original_raw_ref',src.get('original_capture_ref'));assert rr and pin(rr['path'])==rr
    lines=Path(rr['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
    assert [hashlib.sha256(x).hexdigest() for x in lines]==src['original_line_sha256']
    with Path(src['source_audit_path']).open('rb') as f:
        for offset,line in zip(src['source_line_offsets'],lines):f.seek(offset);assert f.readline()==line
    ev=[json.loads(x) for x in lines];assert ev[1]['payload']['call_id']==ev[2]['payload']['call_id']
    chunk=src.get('actual_chunk_id',src.get('actual_host_chunk_id'))
    obs=[x for x in documents(ev[2]['payload'].get('output')) if x.get('chunk_id')==chunk and 'exit_code' in x];assert len(obs)==1
    marks=re.findall(r'(?m)^(?:ROOT_[A-Z_]*PYTHON_EXIT|Python_exit|ROOT_PYTHON_EXIT)=(-?\d+)\s*$',obs[0]['output'])
    py=int(marks[0]) if len(marks)==1 else src.get('actual_python_exit',src.get('actual_Python_exit'))
    assert obs[0]['exit_code']==1 and (py is None or py==1)
    values=dict(actual_outer_exit=1,actual_python_exit=py,actual_native_exit=0 if ordinal==1156 else None,actual_Go_exit=0 if ordinal==1156 else None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
    binding=save('original'+str(ordinal)+'.standard-binding.root.json',dict(schema='researchos.root-diagnostic-standard-binding.v1',issued_by='codex:/root',original_ordinal=ordinal,origin_ref=rr,origin_selector='$',original_source_binding_ref=pin(path),actual_chunk_id=chunk,source_audit_path=src['source_audit_path'],source_line_offsets=src['source_line_offsets'],original_line_sha256=src['original_line_sha256'],**values,counter_reset=False,automatic_retry=False))
    rows.append(dict(ordinal=ordinal,origin_ref=rr,origin_selector='$',capture_binding_ref=binding,description=description,source_fact_refs=[pin(path),rr],capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',**values))
assert [x['ordinal'] for x in rows]==list(range(1149,1162))
bundle=doc(S/'nf5-four-closed-actual-input.root.json');closed_runs={};inputs=[pin(CORE),pin(TP),pin(GUARD),pin(draft),*current[2:]]
for key,group in bundle['groups'].items():
    v=doc(group['producer_closed_ref']['path']);assert v['all_guards_closed'] and v['all_owned_jobs_closed'] and not v['cleanup_errors']
    assert v['status']==('FAILED_NO_AUTOMATIC_RETRY' if key=='C19' else 'VALIDATED_NATIVE_PENDING_MODE_REVIEW') or (key!='C19' and v['summary']['native_test_exit']==0)
    closed_runs[key]=dict(validation_closed_ref=group['producer_closed_ref'],actual_outer_exit=1 if key=='C19' else 0,actual_python_exit=1 if key=='C19' else 0,actual_Native_exit=0,actual_Go_exit=0,all_guards_closed=True,all_owned_jobs_closed=True,automatic_retry=False,formal_acceptance=False,**{k:r for k,r in group.items() if 'Root_capture' in k})
    inputs.extend(group.values())
public_return=B/'integration_codex/public21-caller-9690cc6324834ded8781ce8a2233fa82/caller-return.root.json'
p=doc(public_return);assert p['caller_error'] is None and not p['Root_failure_assignment_required'] and p['source_guard_cleanup']['closed'] and p['source_guard_cleanup']['retained_handles_count']==0
assert p['runner_returned_state']['status']=='PUBLIC21_BOOTSTRAP_OBSERVED_PENDING_INDEPENDENT_REVIEW'
assert len(p['runner_returned_state']['calls'])==1 and p['runner_returned_state']['calls'][0]['actual_exit']==0
inputs.extend([pin(public_return),pin(S/'w09.public21-bootstrap-completed.actual-audit.root.json')])
for row in rows:inputs.extend([row['origin_ref'],row['capture_binding_ref'],*row.get('source_fact_refs',[])])
inputs=list({x['path']:x for x in inputs}.values());assert not any(x['path'] in [y['path'] for y in current[:2]] for x in inputs)
g=module(GUARD,'cp380_actual_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(inputs);core=module(CORE,'cp380_merge_core');tp=module(TP,'cp380_transaction')
    pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1148,next_original_failure_ordinal=1162,pending=rows)
    pending_ref=save('pending-diagnostics.through1161.root.json',pending);now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==379 and ow['revision']==183 and cp['work_in_progress']['root_next_failure_ordinal_live']==1149
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(d,ops,path,value):
            exists,before=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value)));core.put(d,path,value)
        merged,stop=core.merge_pending(cp,pending,current);assert stop==1162
        change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],stop)
        workers=copy.deepcopy(cp['workers']);generation='fullw09-20261010-05'
        for key,actual in closed_runs.items():
            sel='W09-'+key if key in ('G01','G02') else key
            subset=[x for x in workers if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_'+generation+'_'+sel];assert len(subset)==1
            status='CLOSED_ACTUAL_NATIVE_FAILED_EVIDENCE' if key=='C19' else 'CLOSED_ACTUAL_NATIVE_PENDING_FORMAL_MODE'
            values=dict(state=status,closed_at=now,actual_closed=actual,one_shot_consumed=True,future_execution_permitted=False,formal_acceptance=False)
            subset[0].update(values);ownerkey='full_w09_main_native_producer_'+generation+'_'+sel
            sub=copy.deepcopy(ow['card_path_bindings']['W09-99']['subtasks'][ownerkey]);assert sub['run_id']==subset[0]['run_id'];sub.update(values)
            change(o,oo,['card_path_bindings','W09-99','subtasks',ownerkey],sub)
        public_slice='PUBLIC21_BOOTSTRAP_ONLY:9690cc6324834ded8781ce8a2233fa82';matches=[x for x in workers if x.get('slice_id')==public_slice];assert len(matches)==1
        values=dict(state='CLOSED_ACTUAL_BOOTSTRAP_PENDING_INDEPENDENT_REVIEW',closed_at=now,one_shot_consumed=True,future_execution_permitted=False,actual_return_ref=pin(public_return),actual_root_capture_ref=pin(S/'w09.public21-bootstrap-completed.actual-audit.root.json'),formal_acceptance=False)
        matches[0].update(values);key='schema21_public_bootstrap_9690cc6324834ded8781ce8a2233fa82';sub=copy.deepcopy(ow['card_path_bindings']['W05-99']['subtasks'][key]);sub.update(values)
        change(o,oo,['card_path_bindings','W05-99','subtasks',key],sub);change(c,co,['workers'],workers)
        change(c,co,['work_in_progress','cp380_consumed_registration_closure'],dict(native_closed=closed_runs,public21_actual_return_ref=pin(public_return),pending_ref=pending_ref,registered_through=1161,next_original_failure_ordinal=1162,formal_case_accepted_delta=0,parent_acceptance=False,counter_reset=False))
        for k,v in dict(revision=380,expected_previous_revision=379,updated_at=now,updated_by='codex:/root',note='Close four consumed NF5 Native registrations and successful public21 bootstrap; retain C19 evidence refusal and append actual diagnostics1149..1161 once.').items():change(c,co,[k],v)
        for k,v in dict(revision=184,updated_at=now,updated_by='codex:/root').items():change(o,oo,[k],v)
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        assert c['work_in_progress']['w09_native_producer_scope_generations']==cp['work_in_progress']['w09_native_producer_scope_generations']
        save('complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close');result_ref=save('closure.committed.root.json',dict(result,formal_acceptance=False,registered_through=1161,next_original_failure_ordinal=1162,counter_reset=False))
finally:
    closed=g.close();guard_ref=save('source-guard.closed.root.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
assert all(pin(x['path'])==x for x in current[2:])
print(json.dumps(dict(closure_ref=result_ref,source_guard_closed_ref=guard_ref,after_canonical_refs=[pin(V/p) for p in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],registered_through=1161,next_original_failure_ordinal=1162,formal_acceptance=False),ensure_ascii=False))
