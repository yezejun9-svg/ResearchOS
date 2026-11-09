"""New Mainv2 pure controls. Virtual Root/reviewer documents are never persisted."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
B=R/'execution/v2.4/receipts/W05/W05-99'
N=Path(__file__).resolve().parent
OLD=W/'main_c19_source_registry_integration_codex/mainc19-1a11f84'
CP=B/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
checks=[]

def check(label,value):
    assert value,label
    checks.append(dict(name=label,passed=True))

def rawpin(path,raw):return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def pin(path):
    path=Path(path).resolve(strict=True)
    return rawpin(path,path.read_bytes())
def load(path):return json.loads(Path(path).read_bytes())
def save(name,value):
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(N/name)
def module(path):
    m=types.ModuleType('pure_'+Path(path).stem);m.__file__=str(path)
    exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__)
    return m
def extracted(path,names,namespace):
    tree=ast.parse(Path(path).read_bytes())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    check('extract_exact_'+','.join(sorted(names)),{n.name for n in nodes}==set(names))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)

def run():
    main=module(N/'adopt_main_c19.source.py')
    change=load(N/'change-set.json');oldchange=load(OLD/'change-set.json')
    contract=load(N/'root-calling-contract.json')
    original=(OLD/'adopt_main_c19.source.py').read_bytes();proposed=(N/'adopt_main_c19.source.py').read_bytes()
    inv=load(N/'caller.complete-byte-inverse.json')
    check('whole_caller_before_exact',base64.b64decode(inv['whole_before_base64'])==original)
    check('whole_caller_after_exact',base64.b64decode(inv['whole_after_base64'])==proposed)
    restored=proposed
    for row in reversed(inv['spans']):
        check('inverse_span_'+str(row['after_start']),restored[row['after_start']:row['after_end']]==base64.b64decode(row['after_base64']))
        restored=restored[:row['after_start']]+base64.b64decode(row['before_base64'])+restored[row['after_end']:]
    check('caller_complete_byte_inverse',restored==original)
    for row in load(N/'metadata.complete-byte-inverse.json')['files']:
        b=base64.b64decode(row['inverse']['whole_before_base64']);a=base64.b64decode(row['inverse']['whole_after_base64'])
        check('metadata_original_'+row['name'],b==(OLD/row['name']).read_bytes())
        check('metadata_proposed_'+row['name'],a==(N/row['name']).read_bytes())
        for span in reversed(row['inverse']['spans']):
            a=a[:span['after_start']]+base64.b64decode(span['before_base64'])+a[span['after_end']:]
        check('metadata_inverse_'+row['name'],a==b)
    oldtree=ast.parse(original);newtree=ast.parse(proposed)
    def normalized(tree):
        tree=copy.deepcopy(tree)
        tree.body=[n for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name=='validate_scope')
                   and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='N' for t in n.targets))]
        return ast.dump(tree,include_attributes=False)
    check('all_other_caller_AST_identical',normalized(oldtree)==normalized(newtree))
    check('exact_new_caller_N',main.N==N and main.OUT==N/'actual-adoption')
    before,after,refs=main.validate_change_set(change)
    check('full_real_validate_change_set',len(before)==len(after)==7)
    check('seven_target_refs_identical',all(a['after_target_ref']==b['after_target_ref'] for a,b in zip(change['targets'],oldchange['targets'])))
    for i,row in enumerate(change['targets']):
        check('unchanged_target_bytes_'+str(i),after[i]==Path(oldchange['targets'][i]['after_source_ref']['path']).read_bytes())
        if i in main.EXISTING:
            check('before_archive_exact_'+str(i),before[i]==(OLD/f'before.{i}.raw').read_bytes()==(N/f'before.{i}.raw').read_bytes())
            check('before_archive_local_'+str(i),row['before_archive_ref']['path']==str(N/f'before.{i}.raw'))
            check('Main_still_before_'+str(i),pin(row['target'])==row['before_ref'])
        else:check('Main_still_absent_'+str(i),not Path(row['target']).exists())
    check('commands_complete_inverse_unchanged',(N/'commands.complete-byte-inverse.json').read_bytes()==(OLD/'commands.complete-byte-inverse.json').read_bytes())
    check('six_original_Source_refs_unchanged',[x['after_source_ref'] for x in change['targets'][:6]]==[x['after_source_ref'] for x in oldchange['targets'][:6]])
    check('21_applicability_contract_unchanged',change['source21']==oldchange['source21'])
    check('caller_ref_rebound',contract['caller_ref']==pin(N/'adopt_main_c19.source.py'))
    check('change_ref_rebound',contract['change_set_ref']==pin(N/'change-set.json'))
    check('contract_journal_rebound',contract['runtime_journal_root']==contract['owner_exact_field_bindings']['journal_root']==str(main.OUT))
    check('contract_argv_rebound',contract['future_argv'][6]==str(N/'adopt_main_c19.source.py'))
    check('contract_strict_counts',contract['scope_strict_integer_zero_fields']==['formal_case_accepted_delta','new_Go_SQL_API_model_calls'])
    flags=contract['scope_boolean_false_fields'];counts=contract['scope_strict_integer_zero_fields']
    registration=dict(json=json,copy=copy,hashlib=hashlib,TARGETS=[str(p) for p in main.TARGETS],KEY='c19_main_source_registry_adoption',SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
    extracted(CP/'register_cp367.v2.source.py',{'require','facts_scope','validate_live_context','transform'},registration)
    real_facts=load(CP/'checkpoint.execution.facts.json')
    original_scope=json.loads(main.read_ref(real_facts['scope_ref']))
    oldcp=load(main.CANON[0]);oldow=load(main.CANON[1])
    check('actual_Canon_still_366_170',oldcp['revision']==366 and oldow['revision']==170)
    realread=main.read_ref

    def cross(mutate_scope=None,mutate_decision=None,mutate_registered=None,legacy=False):
        memory={}
        def put(path,value):
            raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();ref=rawpin(path,raw);memory[str(path)]=raw;return ref
        def read(ref):
            raw=memory.get(ref['path'])
            if raw is None:return realread(ref)
            assert rawpin(ref['path'],raw)==ref
            return raw
        source_members=[pin(p) for p in N.iterdir() if p.is_file()]
        sm=put(N/'MF.json',dict(schema='SYNTHETIC_NEVER_WRITTEN_SOURCE_MF',members=source_members))
        sh=put(N/'HDF.json',dict(schema='SYNTHETIC_NEVER_WRITTEN_SOURCE_HDF',manifest_ref=sm,actor_id=main.AUTHOR,
            caller_ref=pin(N/'adopt_main_c19.source.py'),change_set_ref=pin(N/'change-set.json')))
        decision=dict(schema=contract['source_review_decision_schema'],decision=contract['source_review_decision_value'],
            actor_role='INDEPENDENT_NON_AUTHOR',actor_id='SYNTHETIC_INDEPENDENT_REVIEWER_NOT_ACTUAL',source_handoff_ref=sh,source_manifest_ref=sm,
            caller_ref=contract['caller_ref'],change_set_ref=contract['change_set_ref'],exact_targets=contract['exact_targets'],
            formal_case_accepted_delta=0,actual_adoption_executed=False)
        if mutate_decision:mutate_decision(decision)
        qr=N/'SYNTHETIC_NEVER_WRITTEN_REVIEW'
        dr=put(qr/'decision.json',decision)
        qm=put(qr/'MF.json',dict(members=[dr]))
        qh=put(qr/'HDF.json',dict(manifest_ref=qm,actor_id=decision['actor_id'],source_decision_ref=dr))
        scope=copy.deepcopy(original_scope)
        scope.update(caller_ref=contract['caller_ref'],change_set_ref=contract['change_set_ref'],source_handoff_ref=sh,source_manifest_ref=sm,
            source_review_handoff_ref=qh,source_review_manifest_ref=qm,source_review_decision_ref=dr,journal_root=str(main.OUT),
            new_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0)
        if mutate_scope:mutate_scope(scope)
        sr=put(N/'SYNTHETIC_NEVER_WRITTEN_ROOT_SCOPE.json',scope)
        facts=copy.deepcopy(real_facts)
        facts.update(scope_ref=sr,calling_contract_ref=pin(N/'root-calling-contract.json'))
        facts['reviews']=[dict(handoff_ref=sh,manifest_ref=sm),dict(handoff_ref=qh,manifest_ref=qm),
            dict(handoff_ref=scope['component_review_handoff_ref'],manifest_ref=scope['component_review_manifest_ref'])]
        registration['load']=lambda ref:json.loads(read(ref));registration['read']=read
        registration_result=main_result=None;reg_error=main_error=None
        try:registration_result=registration['facts_scope'](facts)
        except (ValueError,KeyError,TypeError) as exc:reg_error=str(exc)
        # Full Main gate is evaluated independently for invalid scope controls.
        bindings={'EXACT_ROOT_REGISTRATION_SCOPE_REF':sr,'EXACT_ORDERED_SEVEN_ABSOLUTE_TARGETS':contract['exact_targets'],
            'THIS_SOURCE_HDF_REF':sh,'THIS_SOURCE_MF_REF':sm,'FUTURE_SOURCE_INDEPENDENT_HDF_REF':qh,'FUTURE_SOURCE_INDEPENDENT_MF_REF':qm}
        def resolve(v):return copy.deepcopy(bindings.get(v,v)) if isinstance(v,str) else copy.deepcopy(v)
        owner={k:resolve(v) for k,v in contract['owner_exact_field_bindings'].items()}
        worker={k:resolve(v) for k,v in contract['checkpoint_worker_exact_field_bindings'].items()}
        if registration_result is not None:
            assert registration_result==(scope,owner,worker)
            live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by='codex:/root',created_utc='SYNTHETIC_SOURCE_CONTROL_ONLY',
                source_cutoff=dict(highest_ordinal=facts['highest_observed_ordinal'],next_failure_ordinal=facts['next_failure_ordinal']),
                next_original_failure_ordinal=facts['next_failure_ordinal'],pending=[])
            fr=put(N/'SYNTHETIC_NEVER_WRITTEN_FACTS.json',facts)
            cp,ow=registration['transform'](copy.deepcopy(oldcp),copy.deepcopy(oldow),facts,fr,oldcp,oldow,owner,worker,'SYNTHETIC_SOURCE_CONTROL_ONLY',live)
        else:
            cp=copy.deepcopy(oldcp);ow=copy.deepcopy(oldow);cp['revision']=367;ow['revision']=171
            cp['workers'].append(worker);ow['card_path_bindings']['W09-99']['subtasks'][registration['KEY']]=owner
        if mutate_registered:mutate_registered(cp,ow)
        cr=put(main.CANON[0],cp);ore=put(main.CANON[1],ow)
        vector=dict(schema=contract['vector_schema'],checkpoint_revision=367,ownership_revision=171,
            refs=[cr,ore,pin(main.CANON[2]),change['targets'][6]['before_ref']])
        vr=put(N/'SYNTHETIC_NEVER_WRITTEN_VECTOR.json',vector)
        main.read_ref=read
        gate=main.validate_scope
        if legacy:
            ns=dict(main.__dict__);extracted(OLD/'adopt_main_c19.source.py',{'validate_scope'},ns);gate=ns['validate_scope']
        try:
            main_result=gate(scope,sr,change,contract['change_set_ref'],contract['caller_ref'],sh,sm,source_members,vr)
        except (ValueError,KeyError,TypeError) as exc:main_error=str(exc)
        finally:main.read_ref=realread
        return dict(registration=registration_result is not None,Main=main_result is not None,
            registration_error=reg_error,Main_error=main_error,virtual_docs=len(memory))

    result=cross();check('full_facts_scope_transform_Main_validate_scope_same_integer_zero',result['registration'] and result['Main'])
    check('both_scope_counts_are_exact_integer_zero',all(type(original_scope[k]) is int and original_scope[k]==0 for k in counts))
    legacy=cross(legacy=True)
    check('original_P1_reproduced_without_execution',legacy['registration'] and not legacy['Main'] and legacy['Main_error']=='ROOT_SOURCE_ONLY_BOUNDARY')
    variants=[('False',False),('True',True),('zero_float',0.0),('negative_zero_float',-0.0),('positive_int',1),('negative_int',-1),('string_zero','0'),('null',None)]
    for field in counts:
        for label,value in variants:
            result=cross(lambda s,f=field,v=value:s.update({f:v}))
            check('cross_reject_'+field+'_'+label,not result['registration'] and not result['Main'])
        result=cross(lambda s,f=field:s.pop(f))
        check('cross_reject_missing_'+field,not result['registration'] and not result['Main'])
    for field in flags:
        for label,value in [('True',True),('int_zero',0),('float_zero',0.0),('null',None)]:
            result=cross(lambda s,f=field,v=value:s.update({f:v}))
            check('cross_reject_boolean_'+field+'_'+label,not result['registration'] and not result['Main'])
    for field in ('caller_ref','change_set_ref','journal_root','exact_targets'):
        def corrupt(scope,field=field):scope[field]='SYNTHETIC_FOREIGN'
        result=cross(corrupt);check('cross_reject_binding_'+field,not result['registration'] and not result['Main'])
    for actor in ('codex:/root','codex:/root/command_queue_impl'):
        result=cross(mutate_decision=lambda d,a=actor:d.update(actor_id=a))
        check('cross_reject_self_review_'+actor,not result['registration'] and not result['Main'])
    result=cross(mutate_registered=lambda cp,ow:ow['card_path_bindings']['W09-99']['subtasks'][registration['KEY']].update(scope_ref={'path':'FOREIGN'}))
    check('Main_reject_changed_registered_owner',result['registration'] and not result['Main'])
    result=cross(mutate_registered=lambda cp,ow:cp['workers'].append(copy.deepcopy(cp['workers'][-1])))
    check('Main_reject_duplicate_registered_worker',result['registration'] and not result['Main'])
    check('no_actual_adoption_directory',not (N/'actual-adoption').exists())
    check('no_virtual_review_files_written',not (N/'SYNTHETIC_NEVER_WRITTEN_REVIEW').exists())
    return dict(schema='researchos.main-c19-v2-pure-cross-caller-controls.v1',status='PASS',check_count=len(checks),checks=checks,
        old_471_historical_only=True,original_P1_reproduced=True,registration_functions=['facts_scope','validate_live_context','transform'],
        Main_function='validate_scope',all_future_authority_documents_in_memory_only=True,virtual_Root_or_reviewer_files_written=0,
        actual_registration=False,actual_adoption=False,actual_dispatcher=False,product_Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0)

def main():
    inputs=load(N/'source-input-pins.original.json')['refs']
    allrefs={r['path'].casefold():r for r in inputs}
    for p in N.iterdir():
        if p.is_file():allrefs[str(p).casefold()]=pin(p)
    gp=load(N/'change-set.json')['guard_ref'];gm=module(gp['path'])
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    result=None
    try:
        guard.acquire(list(allrefs.values()))
        result=run()
        for ref in inputs:assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close();cleanup_ref=save('source-controls.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
    result.update(original_inputs_unchanged=len(inputs),guard_cleanup_ref=cleanup_ref)
    save('source-controls.json',result)
    print(json.dumps(dict(status=result['status'],new_v2_checks=result['check_count'],original_inputs_unchanged=len(inputs),actual_adoption=False)))

if __name__=='__main__':main()
