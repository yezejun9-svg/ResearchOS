"""Finite Source preparation. Never calls a Root stage, SQL or child process."""
import ast, copy, hashlib, json, sys, types
from datetime import datetime, timezone, timedelta
from pathlib import Path
N=Path(__file__).resolve().parent
B=N.parents[1]
R=Path('D:/作品集/ResearchOS/research-os')
AUTHOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(p)
def load(p,name):
    m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
    caller_path=N/'public21_root.source.py';tree=ast.parse(caller_path.read_text(encoding='utf-8'))
    compile(tree,str(caller_path),'exec');caller=load(caller_path,'public21_source_controls')
    oc3=Path(caller.OC3_REF['path']);guard_ref=caller.base().GUARD_REF
    guard_module=load(guard_ref['path'],'public21_source_guard')
    leaf=caller.LEAF_REFS;leaf_hdf=doc(leaf['hdf']['path']);leaf_contract=doc(leaf['contract_ref']['path'])
    oc3_hdf=doc(oc3.parent/'HDF.json')
    review_base=B/'schema21_public_bootstrap_source_independent_review_codex/review-public21-20261010-01'
    prior_review={k:pin(review_base/file) for k,file in (('hdf','HDF.json'),('mf','MF.json'),('decision','source-decision.json'))}
    prior_mf=doc(prior_review['mf']['path']);prior_decision=doc(prior_review['decision']['path'])
    programme=doc(caller.PROGRAMME_REF['path'])
    basis=[pin(caller_path),pin(__file__),caller.OC3_REF,pin(oc3.parent/'HDF.json'),pin(oc3.parent/'MF.json'),oc3_hdf['contract_ref'],oc3_hdf['source_inputs_ref'],guard_ref,caller.base().TP_REF,leaf_contract['owned_job'],leaf_contract['locked_python_ref'],caller.PROGRAMME_REF,*leaf.values(),leaf_hdf['input_manifest_ref'],*prior_review.values(),*programme['review_refs']]
    unique={caller.canonical(x['path']):x for x in basis};basis=list(unique.values())
    held=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    results=[];error=None;cleanup=None
    def check(label,condition):
        results.append(dict(id=label,passed=bool(condition),kind='SYNTHETIC_SOURCE_CONTROL_NOT_FORMAL'))
    def rejects(label,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,json.JSONDecodeError):check(label,True)
        else:check(label,False)
    try:
        held.acquire(basis)
        check('syntax-and-inert-import',not any(x in sys.modules for x in ('sqlite3','_sqlite3')))
        check('exact-v2-leaf-source-pins',all(caller.same_ref(pin(x['path']),x) for x in leaf.values()))
        check('actual-review-shape-hdf-member',any(caller.same_ref(prior_review['hdf'],x) for x in prior_mf['members']))
        check('actual-review-shape-decision-member',any(caller.same_ref(prior_review['decision'],x) for x in prior_mf['members']))
        check('prior-review-reject-not-runtime-authority',prior_decision['source_acceptance'] is False and prior_decision['decision']=='REQUEST_CHANGES_SOURCE_ONLY')
        cid='1'*32;parent=B/'integration_codex'
        case=dict(case_id=cid,output_root=str(parent/('schema21-public-'+cid)))
        q=dict(schema='researchos.root-public21-registration-request.v1',issued_by=caller.ROOT,root_thread_id=caller.ROOT_THREAD,scope_key=caller.SCOPE_KEY,formal_acceptance=False,caller_receipt_root=str(parent/('public21-caller-'+cid)),registration_root=str(parent/('public21-registration-'+cid)))
        identity=caller.request_identity(q,case)
        check('distinct-case-scope-key',identity['slice_id']=='PUBLIC21_BOOTSTRAP_ONLY:'+cid and identity['key']=='schema21_public_bootstrap_'+cid)
        for label,mutation in [('borrowed-old21',{'old21_build_scope_ref':{}}),('borrowed-main23',{'Main23_scope_ref':{}}),('borrowed-public22',{'public371_registration_ref':{}}),('unknown-root-actor',{'issued_by':'codex:/root/fake'}),('wrong-root-thread',{'root_thread_id':'wrong'}),('wrong-scope-key',{'scope_key':'OLD21_BUILD'})]:
            bad=dict(q,**mutation);rejects(label,lambda bad=bad:caller.request_identity(bad,case))
        for label,bad in [('extra-case-field',dict(case,grant=True)),('bad-case-id',dict(case,case_id='1'*31)),('wrong-case-root',dict(case,output_root=str(parent/('old21-build-'+cid))))]:rejects(label,lambda bad=bad:caller.request_identity(q,bad))
        peer='codex:/root/example_non_author';value=dict(schema='synthetic-only',refs=[])
        raw=json.dumps(value);envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/example_non_author\nPayload:\n'
        check('whole-peer-json',caller.decode_peer_body(raw,peer)==value)
        check('anchored-final-peer-json',caller.decode_peer_body(envelope+raw,peer)==value)
        for label,text in [('wrong-final-sender',envelope.replace('/root/example_non_author','/root/fake')+raw),('extra-final-prefix','prefix\n'+envelope+raw),('trailing-json',raw+' {}'),('duplicate-key','{"a":1,"a":2}'),('nonfinite-json','{"a":NaN}')]:rejects(label,lambda text=text:caller.decode_peer_body(text,peer))
        for actor in (caller.ROOT,AUTHOR,'client_authored','codex:/wrong/peer'):rejects('no-peer-authority-'+actor,lambda actor=actor:caller.validate_peer_delivery({},[],actor,'SOURCE_REVIEW_WITNESS'))
        now=datetime.now(timezone.utc);created=(now-timedelta(seconds=1)).isoformat();expires=(now+timedelta(seconds=300)).isoformat()
        caller.finite_lease(created,expires,180);check('finite-child-budget-positive',True)
        for label,start,end,minimum in [('expired-lease',created,(now-timedelta(seconds=1)).isoformat(),0),('insufficient-child-budget',created,(now+timedelta(seconds=60)).isoformat(),180),('unbounded-lease',created,(now+timedelta(seconds=2000)).isoformat(),0),('future-created-lease',(now+timedelta(seconds=30)).isoformat(),expires,0)]:rejects(label,lambda start=start,end=end,minimum=minimum:caller.finite_lease(start,end,minimum))
        cp=dict(revision=376,workers=[dict(slice_id='HISTORICAL_BUILD')],failure_counters=[],work_in_progress=dict(root_next_failure_ordinal_live=1121,later_diagnostics_observed_after_cutoff=[],fresh_old21_root_scope_ref={'historical':True}),protected='unchanged')
        ow=dict(revision=180,card_path_bindings={'W05-99':{'subtasks':{'historical_build':{'unchanged':True}}}},protected='unchanged')
        def ref(name):return dict(path=str(N/name),sha256='a'*64,bytes=1)
        s,o,w,f=[ref(x) for x in ('synthetic-scope','synthetic-owner','synthetic-worker','synthetic-facts')]
        owner=dict(scope_ref=s,selected_worker_id=caller.ROOT);worker=dict(scope_ref=s,selected_owner_ref=o,worker_id=caller.ROOT)
        pending=dict(next_original_failure_ordinal=1121,pending=[])
        before=copy.deepcopy((cp,ow));after=caller.projection(cp,ow,s,o,w,f,owner,worker,pending,created,identity)
        check('pure-projection-inputs-unchanged',(cp,ow)==before)
        check('new-pointer-preserves-old21',after[0]['work_in_progress']['public21_bootstrap_root_scope_ref']==s and after[0]['work_in_progress']['fresh_old21_root_scope_ref']=={'historical':True})
        check('new-worker-owner-old-paths-preserved',len(after[0]['workers'])==2 and after[1]['card_path_bindings']['W05-99']['subtasks']['historical_build']=={'unchanged':True} and identity['key'] in after[1]['card_path_bindings']['W05-99']['subtasks'])
        check('new-dynamic-cas-and-counter',after[0]['revision']==377 and after[1]['revision']==181 and after[0]['work_in_progress']['root_next_failure_ordinal_live']==1121)
        for next_ordinal in (1120,True,-1,'1121'):rejects('no-counter-backwards-'+str(next_ordinal),lambda next_ordinal=next_ordinal:caller.projection(cp,ow,s,o,w,f,owner,worker,dict(pending,next_original_failure_ordinal=next_ordinal),created,identity))
        live=caller.LiveScope({},None,{}, {}, {})
        rejects('released-scope-refused-before-reading',live.receipt_context)
        funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        calls=lambda n:[x for x in ast.walk(n) if isinstance(x,ast.Call)]
        attr=lambda node,name:[x for x in calls(node) if isinstance(x.func,ast.Attribute) and x.func.attr==name]
        check('one-leaf-entry-in-execute',len(attr(funcs['execute'],'run_registered_case'))==1 and sum(len(attr(n,'run_registered_case')) for n in funcs.values())==1)
        check('tp-only-activation-future',len(attr(funcs['register'],'update_pair'))==1 and not attr(funcs['projection'],'update_pair'))
        check('all-five-live-capability-methods',{'require_registered','require_resources','qualified_old21_programmes','require_phase','receipt_context'}<={n.name for n in funcs['LiveScope'].body if isinstance(n,ast.FunctionDef)})
        check('case-return-reconciliation-present','FULL_LEAF_PERSISTED_RETURN_RECONCILIATION' in caller_path.read_text(encoding='utf-8'))
        check('known-return-preserved-before-persistence','state=leaf.run_registered_case' in caller_path.read_text(encoding='utf-8') and 'runner_returned_state=state' in caller_path.read_text(encoding='utf-8'))
        original_tree=ast.parse(oc3.read_text(encoding='utf-8'));names={'own_review','runtime_review_chain','projection','validate_root_capture'}
        original=[copy.deepcopy(n) for n in original_tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        changed=[]
        class Map(ast.NodeTransformer):
            def visit_Constant(self,node):
                if type(node.value) is str and node.value in caller.LITERAL_MAP:changed.append(dict(kind='Constant',before=node.value,after=caller.LITERAL_MAP[node.value]));node.value=caller.LITERAL_MAP[node.value]
                return node
            def visit_keyword(self,node):
                if node.arg in ('fresh_old21_root_scope_ref','fresh_old21_registration_facts_ref'):changed.append(dict(kind='keyword',before=node.arg,after=caller.LITERAL_MAP[node.arg]));node.arg=caller.LITERAL_MAP[node.arg]
                return self.generic_visit(node)
        specialized=ast.fix_missing_locations(Map().visit(ast.Module(body=copy.deepcopy(original),type_ignores=[])))
        compile(specialized,'Source-only-effective-OC3','exec')
        reverse={v:k for k,v in caller.LITERAL_MAP.items()}
        class Inverse(ast.NodeTransformer):
            def visit_Constant(self,node):
                if type(node.value) is str and node.value in reverse:node.value=reverse[node.value]
                return node
            def visit_keyword(self,node):
                if node.arg in ('public21_bootstrap_root_scope_ref','public21_bootstrap_registration_facts_ref'):node.arg=reverse[node.arg]
                return self.generic_visit(node)
        restored=Inverse().visit(copy.deepcopy(specialized));check('exact-specialization-AST-inverse',ast.dump(restored,include_attributes=False)==ast.dump(ast.Module(body=original,type_ignores=[]),include_attributes=False))
        effective=ast.unparse(specialized)+'\n'
        with (N/'effective-OC3-functions.source.txt').open('xb') as out:out.write(effective.encode('utf-8'))
        inverse_ref=save('specialization-exact-inverse.json',dict(source_ref=caller.OC3_REF,functions=sorted(names),literal_map=caller.LITERAL_MAP,changes=changed,AST_full_inverse=True,original_bytes_unchanged=caller.same_ref(pin(oc3),caller.OC3_REF),effective_ref=pin(N/'effective-OC3-functions.source.txt'),Root_branch_called=False))
    except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
    finally:
        cleanup=held.close();guard_closed_ref=save('source-controls.guard.closed.json',dict(closure=cleanup,held_refs=basis,Source_only=True,Native_SQL_Go_TP_model_calls=0))
    closed=cleanup.get('closed') is True and cleanup.get('retained_handles_count')==0 and not cleanup.get('errors')
    controls_ref=save('source-controls.json',dict(schema='researchos.public21-caller-source-controls.v1',controls=results,count=len(results),passed=sum(x['passed'] for x in results),failed=[x['id'] for x in results if not x['passed']],error=error,guard_closed_ref=guard_closed_ref,guard_closed=closed,Root_stages_executed=[],Go_Native_SQL_TP_model_calls=0,synthetic_only=True,formal_acceptance=False,execution_grant=False))
    if error or not closed or any(not x['passed'] for x in results):raise RuntimeError('SOURCE_CONTROL_FAILURE_SEE_CLOSED_RECEIPT')
    inputs_ref=save('source-inputs.json',dict(schema='researchos.public21-root-caller-source-inputs.v1',source_author=AUTHOR,author_thread=THREAD,references=basis,oc3_source_ref=caller.OC3_REF,oc3_source_HDF_ref=pin(oc3.parent/'HDF.json'),oc3_source_MF_ref=pin(oc3.parent/'MF.json'),runner_source_refs=leaf,runner_prior_request_changes_review_refs=prior_review,programme_ref=caller.PROGRAMME_REF,programme_actual_review_refs=programme['review_refs'],SourceGuard=guard_closed_ref,live_Canon_read_or_held=False,previous_success_controls_reused_not_rerun={'leaf01':56,'leaf02_delta':3,'OC3':59},future_actual_refs={'Root_scope':None,'caller_review':None,'runner_v2_review':None,'runtime_review':None,'runtime_qualification':None,'new_current4':None},execution_grant=False))
    own_fields=['source_hdf_ref','source_mf_ref','review_hdf_ref','review_mf_ref','review_decision_ref','review_hostpair_witness_ref']
    runner_fields=['runner_source_refs','runner_review_refs','runner_review_witness_ref']
    contract=dict(schema='researchos.public21-root-calling-contract.v1',source_author=AUTHOR,source_author_thread=THREAD,Root_actor=caller.ROOT,Root_thread=caller.ROOT_THREAD,caller_ref=pin(caller_path),registrar_ref=pin(caller_path),source_inputs_ref=inputs_ref,runner_source_refs=leaf,programme_ref=caller.PROGRAMME_REF,locked_python_ref=leaf_contract['locked_python_ref'],source_guard_ref=guard_ref,owned_job_ref=leaf_contract['owned_job'],canonical_transactions_ref=caller.base().TP_REF,OC3_ref=caller.OC3_REF,specialization_inverse_ref=inverse_ref,controls_ref=controls_ref,scope_key=caller.SCOPE_KEY,scope_per_case='PUBLIC21_BOOTSTRAP_ONLY:<32lowerhex>',ownership_key='schema21_public_bootstrap_<32lowerhex>',scope_lease_policy=dict(maximum_seconds=caller.MAX_LEASE_SECONDS,minimum_remaining_before_entry_and_bootstrap_seconds=caller.ENTRY_REMAINING_SECONDS,child_timeout_seconds=90,all_phases_recheck=True),mode_order=['prepare','Root independent runtime review and issuance','propose','check','Root new activation capture','activate','Root new pre-entry capture','execute','Root external full return capture and independent programme/fixture review'],CLI=['fixed Python -I -S -B -X utf8 public21_root.source.py <prepare|propose|check|execute> <ref.path> <ref.sha256> <ref.bytes>','fixed Python -I -S -B -X utf8 public21_root.source.py activate <facts.path> <facts.sha256> <facts.bytes> <activation.path> <activation.sha256> <activation.bytes>'],CLI_stdout='one complete JSON line; original outer actual exit/call+return captured externally by Root after return; no future pair as prerequisite',own_review_fields=own_fields,runner_review_fields=runner_fields,Root_caller_mandatory_contract=leaf_contract['Root_caller_mandatory_contract'],Root_scope_interface=leaf_contract['Root_scope_interface'],source_review_contract=dict(caller=dict(decision_verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',decision_fields=['review_author','source_author','independent_non_author','formal_acceptance:false','execution_grant:false','source_hdf_ref','source_mf_ref','caller_ref','registrar_ref','calling_contract_ref'],review_hdf_fields=['review_author','source_author','manifest_ref','source_decision_ref','source_hdf_ref','source_mf_ref','reviewed_utc'],witness_schema='researchos.root-public21-external-review-witness.v1'),runner=dict(hdf_schema='researchos.independent-public21-source-handoff.v1',decision_schema='researchos.independent-public21-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',Source_acceptance=True,Source_integrity_verified=True,blocking_findings=[],fixed_v2_source_refs=leaf,required_fields=['reviewer','source_author','source_HDF_ref','source_MF_ref','decision_ref','runner_ref','contract_ref','formal_acceptance:false','execution_grant:false'],MF_members_required=['HDF','decision'],witness_schema='researchos.root-public21-runner-review-witness.v1',future_actual_review_refs=None)),peer_delivery=dict(schema='researchos.public21-peer-review-delivery.v1',exact_fields=['schema','review_author','root_thread_id','operation','verdict','review_refs','formal_acceptance:false','execution_grant:false'],operations={'SOURCE_REVIEW_WITNESS':'SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION','RUNNER_SOURCE_REVIEW_WITNESS':'ACCEPTED_SOURCE_ONLY','RUNTIME_QUALIFICATION_ISSUANCE':'RUNTIME_CLOSURE_ACCEPTED'},body='strict whole JSON or exact anchored backend Message Type: FINAL_ANSWER\nTask name: /root\nSender: <canonical actor removeprefix codex:>\nPayload:\n + strict whole JSON',actual_requirements=['original Root session header plus adjacent actual metadata and backend Final, source prefix/offset/line hashes and byte readback','metadata ordinal+1=Final ordinal; metadata timestamp<=Final timestamp<=metadata+1 second','actual author /root/<reviewer>, recipient /root, client_authored=false, one input_text; exact message_id/received_at','reviewer is canonical codex:/root/<agent>, differs actual Root executor and caller/runner Source author','exact full three-field HDF/MF/decision ref sets; no substrings or author statements']),Root_capture=dict(schema='researchos.root-public21-capture-result.v1',binding_scope_key=caller.SCOPE_KEY,operation_marker='PUBLIC21_CAPTURE_OPERATION:<operation>',operations=sorted(caller.CAPTURE_OPS),actual='full actual header/call/output+source prefix/offset/binding; exact Root actor/thread, tools.exec_command actual result0, complete recursively structured path/sha256/bytes refs; operation/source/peer bound, no SHA-string proof'),runtime=dict(qualification_schema='researchos.root-public21-qualified-runtime.v1',status='QUALIFIED_FOR_PUBLIC21_BOOTSTRAP',payload_schema='researchos.root-public21-runtime-qualification-payload.v1',scope_schema='researchos.root-public21-runtime-qualification-scope.v1',scope_slice='PUBLIC21_RUNTIME_RESOURCE_QUALIFICATION',review_HDF_schema='researchos.public21-runtime-independent-review-hdf.v1',review_decision_schema='researchos.public21-runtime-independent-review-decision.v1',manifest_schema='researchos.root-public21-runtime-manifest.v1',review_verdict='RUNTIME_CLOSURE_ACCEPTED',fields=['source_hdf_ref','source_mf_ref','caller_ref','runner_contract_ref','qualification_scope_ref','python_ref','control_ref','runtime_manifest_ref','resource_refs','review_hdf_ref','review_mf_ref','review_decision_ref','review_hostpair_binding_ref','root_issuance_binding_ref','payload_ref','payload_created_utc','created_utc','review_author','issued_by','root_thread_id','source_author','runner_source_author','independent_non_author:true','formal_programme_qualification:false'],time_order='scope.created<=review.reviewed<=actual_peer_received<=payload_created<=actual Root call<=actual Root output<=late wrapper.created<=now; wrapper-only created_utc excluded from payload projection',closed_resources='all existing Source/reviews/programme original chains and native programmes, caller/leaf/OC3/guard/TP/OwnedJob, locked Python, all actual imported standard library modules/caches, SQLite extension/DLL and actual loaded Windows modules; no future issuance/review result in earlier manifest; no live changing CP/OW in immutable resource list',authority='prepare produces only resources after true Source reviews and Root completed prerequisite capture; separate nonauthor runtime review and true Root issuance needed'),requests=dict(prepare=dict(schema='researchos.root-public21-runtime-prepare-request.v1',fields=own_fields+runner_fields+['issued_by','root_thread_id','execution_grant:false','qualification_scope_ref','before_canonical_refs','expected_revisions','preparation_host_binding_ref','output_root=integration_codex/public21-runtime-<32lowerhex>']),registration=dict(schema='researchos.root-public21-registration-request.v1',fields=own_fields+runner_fields+['issued_by','root_thread_id','scope_key','formal_acceptance:false','case_request_ref','caller_receipt_root','registration_root','before_canonical_refs','expected_revisions','root_resume_ref','postreview_live_ref','runtime_qualification_ref','created_utc','lease_expires_at','pending_ref']),activation=dict(schema='researchos.root-public21-activation.v1',fields=['issued_by','root_thread_id','scope_key','formal_acceptance:false','facts_ref','before_canonical_refs','created_utc','capture_binding_ref']),execute=dict(schema='researchos.root-public21-actual-request.v1',fields=['issued_by','root_thread_id','scope_key','formal_acceptance:false','scope_ref','facts_ref','case_request_ref','current_canonical_refs','runtime_qualification_ref','registration_result_ref','host_call_intent_ref','pre_entry_host_binding_ref','created_utc'])),new_case=dict(exact_fields=['case_id','output_root'],case_id='32lowerhex',output_root='integration_codex/schema21-public-<id>',caller_receipt_root='integration_codex/public21-caller-<id>',registration_root='integration_codex/public21-registration-<id>',all_one_shot_new=True),current4='full actual checkpoint,path_ownership,step_state,commands refs and expected revisions from new Root postreview capture; CP/OW CAS delta+1/+1, SS/CM bytes unchanged; future revision dynamic, no fixed376/377 grant',failure_ledger='unchanged OC3 type(next) is int>=actual start, strict contiguous ordinals/nonbool; preserve unique original identities and unknown exits NULL; no retry/reset',callback='OC3 exact AST inverse pure projection; TP only two exclusive handles; callback has no path read/pin/Canon reopen; full four before bytes and committed exclusive pair/journal saved',post_return='exact actual leaf return retained before publication; genuine persisted case.closed reconciled against returned publication fields/full state; Root separately captures caller actual outer call+return and checks exit/Job/source-closure/errors, never infer formal acceptance',security='private generated Owner file is not read, copied, hashed or recorded by caller; only metadata/pinned public programme/runtime/Source refs; no provider/model/key/Home/os.Environ',Source_tests_only=True,actual_stages_executed=[],future_refs=dict(caller_independent_review=None,runner_v2_independent_review=None,new_RuntimeScope=None,runtime_qualification=None,new_RootScope=None,new_current4=None,Root_original_captures=None,actual_fixture=None),formal_acceptance=False,parent_acceptance=False,execution_grant=False)
    contract_ref=save('root-calling-contract.source.json',contract)
    save('Source-preparation.summary.json',dict(source_ref=pin(caller_path),contract_ref=contract_ref,inputs_ref=inputs_ref,controls_ref=controls_ref,guard_closed_ref=guard_closed_ref,specialization_inverse_ref=inverse_ref,controls_passed=len(results),Source_author=AUTHOR,author_thread=THREAD,Root_branch_called=False,Native_SQL_Go_TP_model_calls=0,formal_acceptance=False,execution_grant=False))
    print(json.dumps(dict(Source_prepared=True,caller_ref=pin(caller_path),contract_ref=contract_ref,inputs_ref=inputs_ref,controls_ref=controls_ref,guard_closed_ref=guard_closed_ref,count=len(results),all_passed=True,Root_branch_called=False,formal_acceptance=False,execution_grant=False),ensure_ascii=False,allow_nan=False))
if __name__=='__main__':
    try:main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1',flush=True);raise
    else:print('ROOT_PYTHON_EXIT=0',flush=True)
