"""Close consumed Native registrations and append exact diagnostic originals once."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, re, sys, types

R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
O=N/'cp377-native-closure-live1135'
LIVE_NEXT=int(sys.argv[1])
assert LIVE_NEXT>=1134
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
CORE=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02/adoption_core.source.py'

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (O/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(O/name)
def module(path,name):
    m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def documents(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from documents(x)
    elif isinstance(v,list):
        for x in v:yield from documents(x)
    elif isinstance(v,str):
        try:v=json.loads(v)
        except ValueError:return
        yield from documents(v)

current=[pin(R/'execution/v2.4'/x) for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
assert current[0]['sha256']=='f34a75bc2d85c64e079cbdff4e54eeb0483514279dbe54a0ae9a242212a6b267'
assert current[1]['sha256']=='8571ee5f91adeacb683e197307628fb300e62c7ff1472b48b9e3468c89569cbd'
assert pin(TP)['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
assert pin(CORE)['sha256']=='d2b20cb91ad5f771684048c0009f1880bf63f10c37c8d6fec4c41f1f8b4ef95e'
assert pin(GUARD)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
full=W/'full_w09_actual_native_independent_review_codex/actual-three-20261010-01'
ready=W/'w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01'
leaf=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-02'
pc=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-01'
bridge1=W/'w09_formal_root_bridge_source_codex/bridge-20261010-01'
bridge2=W/'w09_formal_root_bridge_source_codex/bridge-20261010-02'
sources={}
for i in [1117,1118]:
    sources[i]=(ready/f'original-{i}.raw.jsonl',ready/f'original-{i}.binding.json',None)
for i in [1122,1126,1128,1130]:
    sources[i]=(full/f'original-{i}.raw.jsonl',full/f'original-{i}.binding.json',None)
for i,call in [(1119,'call_dzKGLo3o5J9tLMClDfRF9Nzc'),(1120,'call_vtcjZTdLU5pmnzEomwDrNjqe')]:
    sources[i]=(leaf/f'actual-author-host-final/{call}.raw.jsonl',leaf/f'actual-author-host-final/{call}.binding.json',None)
host=json.loads((N/'native.current-three.actual-root-hosts.cp376.json').read_bytes())
for i,name in [(1121,'G02-final-original1121'),(1125,'A06-final-original1125')]:
    x=next(x for x in host['entries'] if x['name']==name)
    sources[i]=(Path(x['raw_ref']['path']),Path(x['binding_ref']['path']),None)
captures=json.loads((bridge1/'original-tool-captures.json').read_bytes())['captures']
for i in [1123,1124,1127,1129]:
    j=next(j for j,x in enumerate(captures) if x.get('original_ordinal')==i)
    sources[i]=(Path(captures[j]['original_capture_ref']['path']),bridge1/'original-tool-captures.json',j)
sources[1131]=(N/'original1131.actual-host.raw.jsonl',N/'original1131.actual-host.binding.json',None)
base='actual-source-host-diagnostics/call_2b7469a7a34244a0a4f9ef4c41f91006'
sources[1132]=(pc/(base+'.raw.jsonl'),pc/(base+'.binding.json'),None)
sources[1133]=(bridge2/'original-1133.raw.jsonl',bridge2/'original-1133.binding.json',None)
assert sorted(sources)==list(range(1117,1134))
descriptions={
1117:'Readonly reviewer rg query guessed absent cmd directory; product calls were not made.',
1118:'Readonly reviewer indexed absent W09-99 state row; successful prerequisite read preserved.',
1119:'Source author guessed an absent review namespace; leaf02 absence prefix was preserved.',
1120:'Source original-capture substring selector was nonunique; existing successful Source controls preserved.',
1121:'Actual G02 Go exit1: legacy fixture applied only migrations1 and7; real migration inventory rejected its gap.',
1122:'Readonly independent reviewer reused one-shot SourceReadGuard; successful original prefix retained and guard closed.',
1123:'Source author GetContent guessed absent parent AGENTS.md; original stderr preserved.',
1124:'Source author rg guessed absent spec/v2.4; actual wrapper exit0, component exit unobserved NULL.',
1125:'Actual A06 Go exit1: same gapped legacy migration fixture; all actual jobs and guards closed.',
1126:'Readonly review buffer omitted a held prepare guard; actual ten-check prefix preserved.',
1127:'Source author AST.Dict.values was called as a method; no product execution occurred.',
1128:'Readonly reviewer assumed nine successful checks instead of actual ten; original retained.',
1129:'Source audit OpenText was denied sharing; actual wrapper exit0, component exits NULL, Root audit handles untouched.',
1130:'Readonly reviewer compared sorted report test roster with chronological event order; actual Native failure retained.',
1131:'Root readonly shape query called .get on the actual failure_counters list; no mutation or product call.',
1132:'Source caller control rejected real four-field historical review MF using a strict three-key ref gate; original2PASS and closed guard retained.',
1133:'Source author rg received a literal wildcard path and Win32 error123 after successful exact directory listing.'}
fixed_fields=['actual_outer_exit','actual_python_exit','actual_native_exit','actual_Go_exit',
              'actual_SQLite_exit','actual_dispatcher_exit','actual_model_exit']
closed_runs={}
nf=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
for selector,runid,actual in [('W09-G01','4fd62ca511684dc39d62c5571d8ddaf5',0),
('W09-G02','28aa266121d24ad2988d578df02d23a4',1),('A06','ba9a185f551c4d4caf123da7eafb4245',1)]:
    p=nf/('actual-'+selector+'-'+runid)/'producer/validation.closed.json'
    v=json.loads(p.read_bytes())
    assert v['all_guards_closed'] and v['all_owned_jobs_closed'] and not v['cleanup_errors']
    closed_runs[selector]=dict(validation_closed_ref=pin(p),actual_outer_exit=actual,
        actual_python_exit=actual,actual_Go_exit=actual,run_id=runid,
        current_source_qualification=False,historical_independent_qualification=actual==0,
        original_failure_ordinal={'W09-G02':1121,'A06':1125}.get(selector),
        all_guards_closed=True,all_owned_jobs_closed=True,automatic_retry=False)
review_hdf=pin(full/'HDF.json')
assert review_hdf['sha256']=='8736edead7afeab47341b2f8e484c469e4c24aa86c31244f03109afc96152233'
adoption_ref=pin(N/'legacy-fixture-Main-adoption-20261010-01/adoption.closed.json')
assert adoption_ref['sha256']=='b5e6b7236691409bce4fe4dae79849b4ccf46f2906f05feda11dc65764e1dbc7'
target_ref=pin(R/'internal/domain/retrieval_test.go')
assert target_ref['sha256']=='1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141'
inputs=[pin(GUARD),pin(TP),pin(CORE),current[2],current[3],review_hdf,pin(full/'MF.json'),
        adoption_ref,target_ref,pin(N/'w09.current-three-native-review.actual-audit.root.json'),
        pin(N/'w09.legacy-fixture-Main-adoption.actual-audit.root.json')]
for raw,src,selector in sources.values():inputs.extend([pin(raw),pin(src)])
inputs.extend(x['validation_closed_ref'] for x in closed_runs.values())
inputs=list({x['path']:x for x in inputs}.values())
O.mkdir(exist_ok=False);(O/'canonical-journal').mkdir()
g=module(GUARD,'root_cp377_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
pending=None; result=None; closed=None; now=datetime.now(timezone.utc).isoformat()
try:
    g.acquire(inputs)
    rows=[]
    for ordinal,(raw_path,source_path,source_selector) in sorted(sources.items()):
        raw_ref=pin(raw_path);source_ref=pin(source_path);src=json.loads(source_path.read_bytes())
        if source_selector is not None:src=src['captures'][source_selector]
        assert src.get('original_raw_ref',src.get('original_capture_ref'))==raw_ref
        lines=raw_path.read_bytes().splitlines(keepends=True)
        assert len(lines)==3 and all(line.endswith(b'\n') for line in lines)
        offsets=src['source_line_offsets'];assert len(offsets)==3
        with Path(src['source_audit_path']).open('rb') as f:
            for offset,line in zip(offsets,lines):f.seek(offset);assert f.readline()==line
        events=[json.loads(line) for line in lines]
        call=events[1]['payload'];ret=events[2]['payload']
        assert call['call_id']==ret['call_id']
        observations=[x for x in documents(ret.get('output')) if 'chunk_id' in x and 'exit_code' in x]
        expected_chunk=src.get('actual_chunk_id',src.get('original_chunk_id',src.get('chunk_id')))
        if expected_chunk is not None:observations=[x for x in observations if x['chunk_id']==expected_chunk]
        assert len(observations)==1,(ordinal,'ACTUAL_ONE_HOST_RESULT',len(observations))
        obs=observations[0]
        marks=re.findall(r'(?m)^(?:ROOT_[A-Z_]*PYTHON_EXIT|Python_exit|ROOT_PYTHON_EXIT)=(-?\d+)\s*$',obs.get('output',''))
        python_exit=int(marks[0]) if len(marks)==1 else None
        values={x:None for x in fixed_fields}
        values.update(actual_outer_exit=obs['exit_code'],actual_python_exit=python_exit)
        if ordinal in (1121,1125):
            assert obs['exit_code']==python_exit==1
            values['actual_Go_exit']=1
        if ordinal in (1124,1129):assert values['actual_outer_exit']==0 and python_exit is None
        binding=save(f'original{ordinal}.standard-binding.root.json',dict(
            schema='researchos.root-diagnostic-standard-binding.v1',issued_by='codex:/root',
            original_ordinal=ordinal,origin_ref=raw_ref,origin_selector='$',
            original_source_binding_ref=source_ref,
            original_source_binding_selector='$' if source_selector is None else '$.captures['+str(source_selector)+']',
            source_audit_path=src['source_audit_path'],source_line_offsets=offsets,
            original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
            original_call_id=call['call_id'],actual_chunk_id=obs['chunk_id'],
            **values,description=descriptions[ordinal],counter_reset=False,automatic_retry=False,
            original_Source_bytes_unchanged=True))
        rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector='$',
            capture_binding_ref=binding,description=descriptions[ordinal],
            capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',**values))
    pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',
        counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,
        source_cutoff_original_failure_ordinal=1116,next_original_failure_ordinal=1134,pending=rows)
    pending_ref=save('pending-diagnostics.cp376-to377.through1133.root.json',pending)
    core=module(CORE,'root_cp377_merge_core');tp=module(TP,'root_cp377_transaction')
    def transform(cp,ow):
        assert cp['revision']==376 and ow['revision']==180
        assert cp['work_in_progress']['root_next_failure_ordinal_live']==1117
        assert ow['active_integrator']['id']=='codex:/root'
        assert ow['card_path_bindings']['W09-99']['owner']=='codex:/root'
        merged,stop=core.merge_pending(cp,pending,current)
        assert stop==1134 and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(doc,ops,path,value):
            exists,before=core.value_at(doc,path)
            ops.append(dict(path=path,before_exists=exists,before=copy.deepcopy(before),after=copy.deepcopy(value)))
            core.put(doc,path,copy.deepcopy(value))
        change(c,co,['failure_counters'],merged)
        change(c,co,['work_in_progress','root_next_failure_ordinal_live'],stop)
        workers=copy.deepcopy(cp['workers'])
        for selector,status in [('W09-G01','CLOSED_QUALIFIED_HISTORICAL_SOURCE_CHANGED'),
            ('W09-G02','CLOSED_ACTUAL_NATIVE_FAILED'),('A06','CLOSED_ACTUAL_NATIVE_FAILED')]:
            matching=[x for x in workers if x.get('slice_id')=='FULL_W09_MAIN_NATIVE_PRODUCER_'+selector]
            assert len(matching)==1 and matching[0]['run_id']==closed_runs[selector]['run_id']
            matching[0].update(state=status,closed_at=now,actual_closed=closed_runs[selector],
                independent_review_handoff_ref=review_hdf,current_source_revalidation_required=True)
            key='full_w09_main_native_producer_'+selector
            old=ow['card_path_bindings']['W09-99']['subtasks'][key]
            assert old['run_id']==closed_runs[selector]['run_id']
            sub=copy.deepcopy(old);sub.update(state=status,closed_at=now,
                actual_closed=closed_runs[selector],independent_review_handoff_ref=review_hdf,
                one_shot_consumed=True,current_source_revalidation_required=True,
                future_execution_permitted=False)
            change(o,oo,['card_path_bindings','W09-99','subtasks',key],sub)
        change(c,co,['workers'],workers)
        facts=dict(status='THREE_NATIVE_CLOSED_CURRENT_SOURCE_REVALIDATION_REQUIRED',
            registered_original_diagnostics=list(range(1117,1134)),registered_next_ordinal=1134,
            observed_later_original_diagnostics=list(range(1134,LIVE_NEXT)),observed_next_original_ordinal=LIVE_NEXT,
            pending_ref=pending_ref,native_closed=closed_runs,independent_review_handoff_ref=review_hdf,
            real_peer_Final_capture_ref=pin(N/'w09.current-three-native-review.actual-audit.root.json'),
            Main_fixture_adoption_ref=adoption_ref,current_Main_fixture_ref=target_ref,
            old_C19_and_three_Native_retained_historically=True,new_Native_selectors_required=['W09-G01','W09-G02','A06','C19'],
            six_current_CM40_consumers_required=True,formal_case_accepted_delta=0,
            parent_acceptance=False,counter_reset=False)
        change(c,co,['work_in_progress','w09_cp377_native_closed'],facts)
        for k,v in dict(revision=377,expected_previous_revision=376,updated_at=now,updated_by='codex:/root',
            note='Root closed three consumed Native registrations and preserved original1117..1133 once; current Source evidence revalidation pending.').items():
            change(c,co,[k],v)
        for k,v in dict(revision=181,updated_at=now,updated_by='codex:/root').items():change(o,oo,[k],v)
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        save('exact-changes-and-inverse.json',dict(checkpoint_operations=co,ownership_operations=oo,
            complete_structural_inverse=True,all_prior_failure_rows_byte_values_preserved=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    save('canonical-closure.committed.json',dict(result,registered_original_ordinals=list(range(1117,1134)),
        next_registered_ordinal=1134,live_next_observed_ordinal=LIVE_NEXT,
        three_old_native_registrations_closed=True,formal_case_accepted_delta=0,
        step_state_and_commands_unchanged=True,counter_reset=False))
finally:
    closed=g.close();guard_ref=save('source-guard.closed.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
assert all(pin(x['path'])==x for x in current[2:])
print(json.dumps(dict(**result,source_guard_closed_ref=guard_ref,
    registered_count=17,registered_through_original_ordinal=1133,
    next_registered_ordinal=1134,live_next_observed_ordinal=LIVE_NEXT,
    all_guards_closed=True,formal_acceptance=False,counter_reset=False),ensure_ascii=False))
