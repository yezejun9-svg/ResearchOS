"""Pure Source controls, using in-memory failure adapters only."""
import ast
import base64
import copy
import hashlib
import itertools
import json
import sys
import types
from pathlib import Path

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
checks=[]

def check(name,value,detail=None):
    assert value,name
    checks.append(dict(name=name,passed=True,detail=detail))

def pin(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))

def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())

def extracted(tree,names,namespace):
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    check('ast_exact_functions_'+','.join(sorted(names)),{n.name for n in nodes}==set(names))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure-extracted-source>','exec'),namespace)

class MemoryOwned:
    def __init__(self,before,after,fail_open=None,fail_write=None,fail_after_create=None,rollback_failure=None):
        self.files={i:b for i,b in enumerate(before) if b is not None};self.handles={}
        self.created=[];self.delete_marked=[];self.operations=[];self.before=before;self.after=after
        self.fail_open=fail_open;self.fail_write=fail_write;self.fail_after_create=fail_after_create
        self.rollback_failure=rollback_failure;self.triggered=False
    def open(self,i,new):
        assert i in range(7) and i not in self.handles
        if self.fail_open==i:raise OSError('SYNTHETIC_OPEN_FAILURE')
        if new:
            if i in self.files:raise FileExistsError('SYNTHETIC_NEW_TARGET_ALREADY_EXISTS')
            self.files[i]=b'';self.created.append(i)
        else:assert i in self.files
        self.handles[i]=i+1;self.operations.append(('open',i,new))
        if self.fail_after_create==i:raise OSError('SYNTHETIC_FINAL_PATH_FAILURE_AFTER_CREATE')
    def read_raw(self,i):assert i in self.handles;return self.files[i]
    def write_raw(self,i,raw):
        assert i in self.handles
        if raw==self.after[i]:assert len(self.handles)==7
        self.operations.append(('write',i,hashlib.sha256(raw).hexdigest()))
        if i==self.fail_write and raw==self.after[i] and not self.triggered:
            self.triggered=True;self.files[i]=raw[:max(1,len(raw)//2)]
            raise OSError('SYNTHETIC_PARTIAL_WRITE_FAILURE')
        if i==self.rollback_failure and raw==self.before[i]:raise OSError('SYNTHETIC_ROLLBACK_DEVICE_FAILURE')
        self.files[i]=raw
    def delete_created(self,i):
        assert i in (3,4,5) and i in self.created and i in self.handles
        self.delete_marked.append(i);self.operations.append(('delete_on_close',i))
    def close(self):
        for i in self.delete_marked:self.files.pop(i,None)
        self.handles.clear()

def run_checks():
    source=(N/'adopt_main_c19.source.py').read_bytes();tree=ast.parse(source)
    compile(tree,str(N/'adopt_main_c19.source.py'),'exec')
    builder=ast.parse((N/'prepare_source.py').read_bytes());compile(builder,'prepare_source.py','exec')
    check('python_source_parse_compile_only',True)
    change=json.loads((N/'change-set.json').read_bytes())
    original=(N/'before.6.raw').read_bytes();proposed=(N/'commands.proposed.json').read_bytes()
    before_doc=json.loads(original);after_doc=json.loads(proposed)
    keys=('test.research.fixture','test.retrieval')
    env6=[f'RESEARCHOS_W09_{a}_{b}' for a in ('NATIVE_REPORT','TOOL_RUN','MODE_DECISION') for b in ('REF','SHA256')]
    ns=dict(json=json,copy=copy,base64=base64,KEYS=keys,ENV6=env6)
    extracted(builder,{'replace_registry'},ns)
    generated,inverse=ns['replace_registry'](original)
    check('registry_exact_reproducible_bytes',generated==proposed)
    check('registry_full_inverse_base64',base64.b64decode(inverse['whole_original_base64'])==original)
    check('registry_exact_unchanged_top_level',set(before_doc)==set(after_doc) and all(
          before_doc[k]==after_doc[k] for k in before_doc if k!='commands'))
    check('registry_exact_same_command_keys',set(before_doc['commands'])==set(after_doc['commands']))
    check('registry_no_revision_change',before_doc.get('revision')==after_doc.get('revision'))
    for key in before_doc['commands']:
        if key not in keys:check('registry_other_entry_unchanged_'+key,before_doc['commands'][key]==after_doc['commands'][key])
    for key in keys:
        old=before_doc['commands'][key];new=after_doc['commands'][key]
        mutable={'executable_tool','argv','allowed_env','selectors','tool_env'}
        check('entry_only_explicit_fields_'+key,set(old)==set(new) and all(old[k]==new[k] for k in old if k not in mutable))
        check('no_global_required_env_'+key,new['required_env']==old['required_env']==[])
        check('exact_added_env6_'+key,new['allowed_env']==old['allowed_env']+env6 and len(set(new['allowed_env']))==len(new['allowed_env']))
        check('locked_python_router_argv_no_I_'+key,new['executable_tool']=='python' and new['argv']==['-B','-X','utf8','ops/ci/w09_formal_router.py',key] and '-I' not in new['argv'])
        check('old_check_selectors_unchanged_'+key,new['selectors']['check_id']==old['selectors']['check_id'])
        check('C19_only_case_selector_'+key,new['selectors']['case_id']==['C19'])
        check('task_selectors_only_W09_append_'+key,new['selectors']['task_id']==old['selectors']['task_id']+([] if 'W09' in old['selectors']['task_id'] else ['W09']))
        check('tool_env_preserved_or_locked_go_'+key,new['tool_env']==({'RESEARCHOS_GO':'go'} if key=='test.research.fixture' else old['tool_env']))
        restored=copy.deepcopy(new)
        for field in mutable:restored[field]=copy.deepcopy(old[field])
        check('whole_entry_semantic_inverse_'+key,restored==old)
    routes={('test.research.fixture','W08','W08-01',''),('test.research.fixture','W08','W08-02',''),
            ('test.retrieval','W09','W09-01',''),('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19')}
    router_path=Path(change['targets'][4]['after_source_ref']['path'])
    router_tree=ast.parse(router_path.read_bytes());constants={}
    for node in router_tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('NATIVE','PRESERVED'):
            constants[node.targets[0].id]=ast.literal_eval(node.value)
    for key,task,ck,case in itertools.product(keys,('W08','W09','W17',''),('','W08-01','W08-02','W09-01','W09-G01'),('','C19','A06')):
        entry=after_doc['commands'][key];sel=dict(task_id=task,check_id=ck,case_id=case)
        admitted=all(not value or value in entry['selectors'].get(name,[]) for name,value in sel.items())
        route=(key,task,ck,case)
        accepted=admitted and (route in constants['NATIVE'] or route in constants['PRESERVED'])
        check('route_truth_'+repr(route),accepted==(route in routes))
    main=next(n for n in router_tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    preserved=next(n for n in main.body if isinstance(n,ast.If) and ast.unparse(n.test)=='route in PRESERVED')
    preserved_text=ast.unparse(preserved)
    check('preserved_streams_and_exit_static','sys.stderr.buffer.write(child.stderr)' in preserved_text
          and 'sys.stdout.buffer.write(child.stdout)' in preserved_text and 'return child.returncode' in preserved_text)
    check('preserved_W08_locked_go_static',"argv = [go, 'run', './tests/research/check']" in preserved_text)
    check('preserved_W0901_original_argv_static',"argv = [sys.executable, '-X', 'utf8', str(ROOT / 'tests/evidence/check/main.py')]" in preserved_text)
    before=[];after=[]
    for i,row in enumerate(change['targets']):
        check('target_exact_'+str(i),row['target']==str((R/row['relative']).resolve()))
        source_ref=row['after_source_ref'];check('sealed_source_pin_'+str(i),pin(source_ref['path'])==source_ref)
        after.append(Path(source_ref['path']).read_bytes())
        if row['before_ref'] is None:
            check('absent_before_'+str(i),not Path(row['target']).exists());before.append(None)
        else:
            check('existing_before_pin_'+str(i),pin(row['target'])==row['before_ref'])
            b=Path(row['before_archive_ref']['path']).read_bytes();before.append(b)
            check('full_before_archive_'+str(i),hashlib.sha256(b).hexdigest()==row['before_ref']['sha256'] and len(b)==row['before_ref']['bytes'])
    report=json.loads(Path(change['source21_report_ref']['path']).read_bytes())
    check('original_source21_report_pin',pin(change['source21_report_ref']['path'])==change['source21_report_ref'])
    check('exact_Source21_roster',set(report['version_manifest']['source_sha256'])=={x['path'] for x in change['source21']} and len(change['source21'])==21)
    for row in change['source21']:
        ref=row.get('current_ref',row.get('desired_ref'))
        check('Source21_applicability_'+row['path'],pin(ref['path'])==ref and 'sha256:'+ref['sha256']==report['version_manifest']['source_sha256'][row['path']])
    check('source15_current_exact',sum(x['disposition']=='CURRENT_MAIN_ALREADY_EXACT' for x in change['source21'])==15)
    pure=dict(base64=base64,hashlib=hashlib,TARGETS=tuple(Path(x['target']) for x in change['targets']),EXISTING=(0,1,2,6),NEW=(3,4,5))
    extracted(tree,{'require','digest','raw_pin','transaction'},pure)
    def trial(label,owned,fail_record=None):
        events={}
        def record(name,value):
            if name==fail_record:raise OSError('SYNTHETIC_JOURNAL_FAILURE')
            assert name not in events;events[name]=value
        result=pure['transaction'](owned,before,after,record);owned.close()
        check('transaction_only_seven_targets_'+label,all(op[1] in range(7) for op in owned.operations))
        return result,events,owned.files
    result,events,files=trial('success',MemoryOwned(before,after))
    check('transaction_success',result['status']=='SEVEN_SOURCE_TARGETS_COMMITTED' and files==dict(enumerate(after)))
    check('transaction_durable_complete_inverse',events['intent.json']['before_base64']==[None if b is None else base64.b64encode(b).decode() for b in before]
          and events['intent.json']['after_base64']==[base64.b64encode(b).decode() for b in after])
    expected_before={i:b for i,b in enumerate(before) if b is not None}
    for i in range(7):
        result,events,files=trial('partial_write_'+str(i),MemoryOwned(before,after,fail_write=i))
        check('partial_write_complete_rollback_'+str(i),result['status']=='FAILED_ROLLED_BACK' and files==expected_before)
        check('failure_retains_complete_intent_'+str(i),'intent.json' in events and 'failed.json' in events)
    for i in (0,1,2,6,3,4,5):
        result,events,files=trial('open_'+str(i),MemoryOwned(before,after,fail_open=i))
        check('open_failure_preserves_all_'+str(i),result['status']=='FAILED_ROLLED_BACK' and files==expected_before)
    for i in (3,4,5):
        result,events,files=trial('post_create_'+str(i),MemoryOwned(before,after,fail_after_create=i))
        check('post_create_failure_removes_only_created_'+str(i),result['status']=='FAILED_ROLLED_BACK' and files==expected_before)
    result,events,files=trial('commit_journal_failure',MemoryOwned(before,after),fail_record='committed.json')
    check('commit_journal_failure_complete_rollback',result['status']=='FAILED_ROLLED_BACK' and files==expected_before)
    for i in (0,1,2,6):
        fake=MemoryOwned(before,after);fake.files[i]=b'SYNTHETIC_FOREIGN_BEFORE'
        wanted=dict(fake.files);result,events,files=trial('foreign_'+str(i),fake)
        check('foreign_before_not_overwritten_'+str(i),files==wanted and not result['written_indices'])
    for i in (3,4,5):
        fake=MemoryOwned(before,after);fake.files[i]=b'SYNTHETIC_FOREIGN_NEW_PATH'
        wanted=dict(fake.files);result,events,files=trial('foreign_new_'+str(i),fake)
        check('foreign_new_not_overwritten_or_deleted_'+str(i),files==wanted and not result['written_indices'])
    result,events,files=trial('rollback_device_failure',MemoryOwned(before,after,fail_write=1,rollback_failure=0))
    check('rollback_failure_honest_reconciliation',result['status']=='FAILED_ROLLBACK_REQUIRES_ROOT_RECONCILIATION' and bool(result['rollback_errors']))
    fake=MemoryOwned(before,after)
    try:pure['transaction'](fake,before,after,lambda *_:(_ for _ in ()).throw(OSError('SYNTHETIC_INTENT_FAILURE')))
    except OSError:check('intent_failure_precedes_any_business_mutation',not fake.handles and fake.files==expected_before)
    else:raise AssertionError('intent failure not propagated')
    text=source.decode()
    imports={n.names[0].name for n in tree.body if isinstance(n,ast.Import)}
    check('no_product_or_process_or_network_import',not imports&{'subprocess','sqlite3','socket','requests','shutil'})
    check('no_product_subprocess_or_exec_command_calls',all(not isinstance(n,ast.Call) or ast.unparse(n.func) not in
        {'os.system','os.popen','subprocess.run','subprocess.Popen'} for n in ast.walk(tree)))
    check('target_index_only_owned_create_static','p=exact_path(TARGETS[i],absent=new)' in text and '1 if new else 3' in text)
    check('mandatory_share0_static','0x80000000|0x40000000|0x00010000,0,None' in text)
    check('parent_directory_delete_denial_static','0x80,0x1|0x2,None,3,0x02000000,None' in text)
    check('rollback_delete_only_created_handle_static',"i in NEW and i in self.created and i in self.handles" in text)
    check('no_business_path_unlink_rename_replace',all(not isinstance(n,ast.Call) or
          not isinstance(n.func,ast.Attribute) or n.func.attr not in {'unlink','rename','replace','rmdir'}
          for n in ast.walk(tree)))
    check('CP_OW_SS_held_not_written_static',"*vector['refs'][:3]" in text and "Path(ref['path']) not in TARGETS" in text)
    check('runtime_no_current_review_placeholder',"ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS" in text
          and 'researchos.w09-main-c19-component-adoption-prerequisite.v1' not in text)
    check('future_Source_independent_explicit_gate',"SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION" in text
          and "d['actor_id'] not in (AUTHOR,ROOT_ACTOR)" in text)
    check('future_canonical_explicit_successor_gate',"vector['checkpoint_revision']>366" in text
          and "vector['ownership_revision']>170" in text)
    # Future authorization examples exist only in memory and are explicitly
    # synthetic controls. They are never written as Root or reviewer receipts.
    canon=tuple(R/'execution/v2.4'/f'{n}.json' for n in ('checkpoint','path_ownership','step_state','commands'))
    targets=tuple(Path(x['target']) for x in change['targets'])
    def fake_ref(name):return dict(path=str(N/name),sha256='0'*64,bytes=0)
    href=fake_ref('HDF.json');mref=fake_ref('MF.json');selfref=pin(N/'adopt_main_c19.source.py');change_ref=pin(N/'change-set.json')
    sref=fake_ref('SYNTHETIC_NEVER_WRITTEN_ROOT_SCOPE');vref=fake_ref('SYNTHETIC_NEVER_WRITTEN_VECTOR')
    sh=fake_ref('SYNTHETIC_SOURCE_REVIEW_HDF');sm=fake_ref('SYNTHETIC_SOURCE_REVIEW_MF');dr=fake_ref('SYNTHETIC_SOURCE_DECISION')
    ch=change['component_actual_review_handoff_ref'];cm=change['component_actual_review_manifest_ref']
    consumer_h=json.loads(Path(ch['path']).read_bytes())
    scope=dict(schema='researchos.root-w09-main-c19-adoption-scope.v1',status='ROOT_AUTHORIZED_SEVEN_TARGET_SOURCE_ADOPTION_ONLY',
        issued_by='codex:/root',executor='codex:/root',caller_ref=selfref,change_set_ref=change_ref,
        source_handoff_ref=href,source_manifest_ref=mref,exact_targets=[str(p) for p in targets],
        journal_root=str(N/'actual-adoption'),formal_case_accepted_delta=0,formal_dispatcher=False,
        formal_acceptance=False,producer_rerun=False,copy_native_packet=False,new_Go_SQL_API_model_calls=False,
        checkpoint_write=False,ownership_write=False,step_state_write=False,
        consumer_closed_ref=change['original_consumer_closed_ref'],source_review_handoff_ref=sh,
        source_review_manifest_ref=sm,source_review_decision_ref=dr,component_review_handoff_ref=ch,component_review_manifest_ref=cm)
    d=dict(schema='researchos.w09-main-c19-independent-source-decision.v1',
        decision='SOURCE_ACCEPTED_FOR_ROOT_SEVEN_TARGET_ADOPTION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='SYNTHETIC_INDEPENDENT_REVIEWER',
        source_handoff_ref=href,source_manifest_ref=mref,caller_ref=selfref,change_set_ref=change_ref,
        exact_targets=scope['exact_targets'],formal_case_accepted_delta=0,actual_adoption_executed=False)
    owner=dict(owner='codex:/root',current_source_writer=None,scope_ref=sref,exact_targets=scope['exact_targets'],
        state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',source_handoff_ref=href,source_manifest_ref=mref,
        source_review_handoff_ref=sh,source_review_manifest_ref=sm,component_review_handoff_ref=ch,component_review_manifest_ref=cm,
        journal_root=scope['journal_root'],formal_case_accepted_delta=0,formal_dispatcher=False,parent_acceptance=False)
    worker=dict(step_id='W09-99',slice_id='C19_MAIN_SOURCE_REGISTRY_ADOPTION',owner='codex:/root',
        state='ROOT_REGISTERED_PENDING_SOURCE_ADOPTION',scope_ref=sref,exact_targets=scope['exact_targets'],
        source_review_handoff_ref=sh,component_review_handoff_ref=ch)
    refs=[fake_ref('SYNTHETIC_'+p.name) for p in canon]
    for ref,p in zip(refs,canon):ref['path']=str(p)
    refs[3]=change['targets'][6]['before_ref']
    vector=dict(schema='researchos.w09-main-c19-adoption-canonical-vector.v1',checkpoint_revision=367,ownership_revision=171,refs=refs)
    cp=dict(revision=367,project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',workers=[worker])
    ow=dict(revision=171,shared_integrator='qoder-desktop:/root/platform_owner',active_integrator=dict(id='codex:/root'),
            card_path_bindings={'W09-99':dict(owner='codex:/root',subtasks=dict(c19_main_source_registry_adoption=owner))})
    base=dict(scope=scope,decision=d,vector=vector,cp=cp,ow=ow,consumer=consumer_h)
    gate=dict(json=json,Path=Path,R=R,N=N,OUT=N/'actual-adoption',TARGETS=targets,CANON=canon,
              ROOT_ACTOR='codex:/root',AUTHOR='codex:/root/command_queue_impl')
    extracted(tree,{'require','validate_scope'},gate)
    def gate_trial(data):
        docs={vref['path']:data['vector'],dr['path']:data['decision'],refs[0]['path']:data['cp'],refs[1]['path']:data['ow'],
              refs[2]['path']:{},refs[3]['path']:before_doc}
        gate['read_ref']=lambda ref:json.dumps(docs[ref['path']]).encode()
        gate['manifest_refs']=lambda h,m: (
            (dict(actor_id=data['decision']['actor_id'],source_decision_ref=dr),[sh,sm,dr]) if h==sh else (data['consumer'],[ch,cm]))
        return gate['validate_scope'](data['scope'],sref,change,change_ref,selfref,href,mref,[selfref,change_ref],vref)
    gate_trial(copy.deepcopy(base));check('future_exact_367_171_in_memory_gate',True)
    later=copy.deepcopy(base);later['vector']['checkpoint_revision']=369;later['vector']['ownership_revision']=173
    later['cp']['revision']=369;later['ow']['revision']=173
    gate_trial(later);check('future_explicit_369_173_not_hardcoded_pair',True)
    mutations={
      'same_author':lambda x:x['decision'].update(actor_id='codex:/root/command_queue_impl'),
      'root_self_review':lambda x:x['decision'].update(actor_id='codex:/root'),
      'pending_source_review':lambda x:x['decision'].update(decision='PENDING'),
      'foreign_change_set':lambda x:x['scope'].update(change_set_ref=fake_ref('FOREIGN')),
      'eighth_target':lambda x:x['scope']['exact_targets'].append(str(R/'FOREIGN')),
      'different_journal':lambda x:x['scope'].update(journal_root=str(R/'FOREIGN')),
      'scope_vector_cycle':lambda x:x['scope'].update(canonical_vector_ref=vref),
      'producer_rerun':lambda x:x['scope'].update(producer_rerun=True),
      'formal_upgrade':lambda x:x['scope'].update(formal_case_accepted_delta=1),
      'CP_write':lambda x:x['scope'].update(checkpoint_write=True),
      'old_CP366':lambda x:x['vector'].update(checkpoint_revision=366),
      'old_OW170':lambda x:x['vector'].update(ownership_revision=170),
      'CP_type_bool':lambda x:x['vector'].update(checkpoint_revision=True),
      'OW_type_bool':lambda x:x['vector'].update(ownership_revision=True),
      'CP_mismatch':lambda x:x['cp'].update(revision=368),
      'wrong_shared_owner':lambda x:x['ow'].update(shared_integrator='FOREIGN'),
      'wrong_active_integrator':lambda x:x['ow']['active_integrator'].update(id='FOREIGN'),
      'duplicate_worker':lambda x:x['cp']['workers'].append(copy.deepcopy(x['cp']['workers'][0])),
      'worker_scope_mismatch':lambda x:x['cp']['workers'][0].update(scope_ref=fake_ref('FOREIGN')),
      'owner_extra_authority':lambda x:x['ow']['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption'].update(arbitrary_paths=True),
      'old_v6_component_decision':lambda x:x['consumer'].update(decision='ACTUAL_NATIVE_FIXTURE_QUALIFIED_CURRENT_V7_REPLAY_PASS'),
      'component_unclosed':lambda x:x['consumer'].update(all_guards_closed=False),
      'component_wrong_closed_ref':lambda x:x['consumer'].update(consumer_closed_ref=fake_ref('FOREIGN')),
      'component_formal_claim':lambda x:x['consumer'].update(CURRENT_formal_status_created=True),
    }
    for label,mutate in mutations.items():
        data=copy.deepcopy(base);mutate(data)
        try:gate_trial(data)
        except (ValueError,KeyError):check('scope_negative_'+label,True)
        else:raise AssertionError('scope negative accepted '+label)
    check('source_package_has_no_actual_output',not (N/'actual-adoption').exists())
    check('caller_source_no_os_crash_atomic_claim','crash_atomic=False' in text and 'process_loss_requires_root_reconciliation=True' in text)
    refs=json.loads((N/'source-input-pins.original.json').read_bytes())['refs']
    for ref in refs:check('unchanged_input_'+ref['path'],pin(ref['path'])==ref)
    return dict(schema='researchos.w09-main-c19-source-controls.v1',status='PASS',check_count=len(checks),checks=checks,
        real_product_calls=0,actual_adoption=False,actual_Win32_transaction=False,
        pure_in_memory_fault_injection=True,original_inputs_unchanged=len(refs),formal_case_accepted_delta=0)

if __name__=='__main__':
    result=run_checks();save('source-controls.json',result)
    print(json.dumps(dict(status=result['status'],checks=result['check_count'],input_count=result['original_inputs_unchanged'],actual_adoption=False)))
