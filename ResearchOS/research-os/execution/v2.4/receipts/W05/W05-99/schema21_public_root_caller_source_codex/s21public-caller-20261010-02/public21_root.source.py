"""Strict Root public21 caller. Import has no Canon, SQL or child side effect.

OC3 provides unchanged reference/path/JSON/original-audit/current4/failure/TP
primitives. Selected OC3 function bodies are specialized only by explicit AST
literal mappings; the mapping and effective source are reviewable. New gates
bind a reviewed public21 leaf, genuine qualified programmes and SQLite runtime.
"""
from __future__ import annotations
import ast, copy, hashlib, json, ntpath, re, sys, types
from pathlib import Path
from datetime import datetime, timezone
R=Path('D:/作品集/ResearchOS/research-os')
V=R/'execution/v2.4'; B=V/'receipts/W05/W05-99'
N=Path(__file__).resolve().parent
ROOT='codex:/root'; ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUTHOR='codex:/root/backup_regression_resources'
SCOPE_KEY='PUBLIC21_BOOTSTRAP_ONLY'
STATE='ROOT_REGISTERED_PENDING_PUBLIC21_BOOTSTRAP'
PHASES=('prepare','bootstrap21','inspect21','complete')
MAX_LEASE_SECONDS=1800
ENTRY_REMAINING_SECONDS=180
OC3_REF={'path':str(B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'),'sha256':'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06','bytes':65191}
LEAF_BASE=B/'genuine_schema21_public_bootstrap_runner_source_codex/s21public-20261010-02'
LEAF_REFS={'hdf':{'path':str(LEAF_BASE/'HDF.json'),'sha256':'67370cddc352f299c5c8569ae69e0b90dec64a8f281746d4510a55dac1d02c0d','bytes':6131},
 'mf':{'path':str(LEAF_BASE/'MF.json'),'sha256':'045363095aa0b1efaa3359cdead8d246153ba1f695cd98095a20dc016dcb791f','bytes':19678},
 'runner_ref':{'path':str(LEAF_BASE/'public21_runner.py'),'sha256':'6d8bd926a577e2d44820c6e23d5d93364dcfb2a14487dd1fc7410271094c7c28','bytes':18911},
 'contract_ref':{'path':str(LEAF_BASE/'contract.json'),'sha256':'c22fc6d1bb3ce01574bf65f32387f8f76799a1152916d85bc94c3e6d7bb4b5a2','bytes':31831}}
PROGRAMME_REF={'path':str(V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/old21.programme.qualification.bound.actual.root.json'),'sha256':'8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70','bytes':5911}
RUNNER_REVIEW_BASE=B/'schema21_public_bootstrap_source_independent_review_codex/review-public21-20261010-02'
RUNNER_ACCEPTED_REVIEW_REFS={
 'hdf':{'path':str(RUNNER_REVIEW_BASE/'HDF.json'),'sha256':'c17544228612c3d42db04976b4fa8f215c5460de354cc93efb368d9bcb2fbebd','bytes':3308},
 'mf':{'path':str(RUNNER_REVIEW_BASE/'MF.json'),'sha256':'f67ef77e8e1c6e5cf10c25a6a4c6df631c602f7a4d870a34ce0008e9b4ab0fe8','bytes':25822},
 'decision':{'path':str(RUNNER_REVIEW_BASE/'source-decision.json'),'sha256':'8e65943bc9bed92f33343de5a27d18acfc6c1e1ee015b09cd3dcb1d05e53138f','bytes':3268}}
RUNNER_REAL_PEER_AUDIT_REF={'path':str(V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-source-review-v2.actual-audit.root.json'),'sha256':'775d81746688b95de66cdb101c5caec0d22ebed3bdeffec194afcf31eac782dd','bytes':1126}
_base=None; _kernel=None
def base():
    global _base
    if _base is None:
        raw=Path(OC3_REF['path']).read_bytes()
        if len(raw)!=OC3_REF['bytes'] or hashlib.sha256(raw).hexdigest()!=OC3_REF['sha256']:raise ValueError('OC3_SOURCE_PIN')
        m=types.ModuleType('public21_oc3_reference');m.__file__=OC3_REF['path']
        exec(compile(raw,m.__file__,'exec'),m.__dict__);_base=m
    return _base
def need(ok,code): return base().need(ok,code)
def doc(ref): return base().doc(ref)
def checked(ref): return base().checked(ref)
def pin(path): return base().pin(path)
def same_ref(a,b): return base().same_ref(a,b)
def canonical(path): return base().canonical(path)
def when(value): return base().when(value)
def save(path,value): return base().save(path,value)
def refs_equal(a,b):
    return type(a) is list and type(b) is list and len(a)==len(b) and all(same_ref(x,y) for x,y in zip(a,b))
def finite_lease(created,expires,minimum_remaining=0):
    start,end=when(created),when(expires);now=datetime.now(timezone.utc)
    need(start<=now and 0<(end-start).total_seconds()<=MAX_LEASE_SECONDS and (end-now).total_seconds()>minimum_remaining,'FINITE_FRESH_PUBLIC21_LEASE_BUDGET')
def safe_directory(path,new=False):
    canonical(str(path));p=Path(path)
    for ancestor in (p,*p.parents):
        if ancestor.exists():
            need(not ancestor.is_symlink() and not ancestor.is_junction()
                and not (getattr(ancestor.lstat(),'st_file_attributes',0)&0x400)
                and ntpath.normcase(str(ancestor.resolve(strict=True)))==ntpath.normcase(str(ancestor.absolute())),'DIRECTORY_ALIAS')
    need(p.parent.is_dir() and (not p.exists() if new else p.is_dir()),'DIRECTORY_EXISTENCE')
    return p
CAPTURE_OPS={'SOURCE_REVIEW_WITNESS','RUNNER_SOURCE_REVIEW_WITNESS','POSTREVIEW_CURRENT_FOUR','ACTIVATION_FACTS_CURRENT_FOUR','RUNTIME_QUALIFICATION_ISSUANCE','RUNTIME_MANIFEST_PREREQUISITES','PUBLIC21_BOOTSTRAP_PREREQUISITES'}
def decode_peer_body(text,actor):
    envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor.removeprefix('codex:')+'\nPayload:\n'
    result=base().strict(text[len(envelope):] if text.startswith(envelope) else text)
    need(type(result) is dict,'WHOLE_TYPED_PEER_JSON')
    return result
def validate_task94_body(delivered,expected_refs):
    need(set(delivered)=={'task','decision','resolved_findings','findings','review_directory','HDF','MF','source_decision','postseal_tool_io','source_runner','source_contract','verification','execution_grant','formal_acceptance','Leaf_RootScope_Native_Go_SQL_model_TP_calls','STOP'} and delivered['task']=='Task94' and delivered['decision']=='ACCEPTED_SOURCE_ONLY' and delivered['findings']==[] and delivered['resolved_findings']==['PUBLIC21-OBSERVATION-001'] and delivered['execution_grant'] is False and delivered['formal_acceptance'] is False and delivered['Leaf_RootScope_Native_Go_SQL_model_TP_calls']==0 and delivered['STOP'] is True and canonical(delivered['review_directory'])==canonical(str(RUNNER_REVIEW_BASE)),'EXACT_REAL_TASK94_DELIVERY')
    refs=[]
    for field,role,file in (('HDF','hdf','HDF.json'),('MF','mf','MF.json'),('source_decision','decision','source-decision.json')):
        item=delivered[field];need(type(item) is dict and set(item)==({'sha256','bytes','verified_members'} if field=='MF' else {'sha256','bytes'}),'TASK94_TYPED_DIGEST_BYTES')
        ref=dict(path=str(RUNNER_REVIEW_BASE/file),sha256=item['sha256'],bytes=item['bytes']);base().shape(ref);need(same_ref(ref,RUNNER_ACCEPTED_REVIEW_REFS[role]),'TASK94_COMPLETE_ROLE_PATH_SHA_BYTES');refs.append(ref)
    need(base().exact_ref_set(refs)==base().exact_ref_set(expected_refs),'TASK94_EXPECTED_REVIEW_REFS')
    for field,role in (('source_runner','runner_ref'),('source_contract','contract_ref')):
        item=delivered[field];need(type(item) is dict and set(item)=={'sha256','bytes'} and same_ref(dict(path=LEAF_REFS[role]['path'],**item),LEAF_REFS[role]),'TASK94_CURRENT_LEAF_BYTES')
    verification=delivered['verification'];need(type(verification) is dict and verification.get('exact_runner_inverse') is True and verification.get('guarded_inputs_closed')==66 and verification.get('new_AST_fault_controls_passed')==12 and verification.get('new_mechanical_failures')==[],'TASK94_ACTUAL_SOURCE_RESULT')
def validate_peer_delivery(binding_ref,expected_refs,actor,operation):
    need(type(actor) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+',actor) and actor not in (ROOT,AUTHOR),'ACTUAL_NONAUTHOR_PEER')
    binding=doc(binding_ref);first,last=base().original_capture_rows(binding,checked(binding['original_capture_ref']),peer=True)
    p=last['payload']
    need(first['type']=='inter_agent_communication_metadata' and type(first['payload'].get('trigger_turn')) is bool and last['type']=='response_item' and last['ordinal']==first['ordinal']+1 and 0<=(when(last['timestamp'])-when(first['timestamp'])).total_seconds()<=1,'ADJACENT_REAL_PEER_METADATA_FINAL')
    need(p.get('type')=='agent_message' and p.get('author')==actor.removeprefix('codex:') and p.get('recipient')=='/root' and last.get('metadata',{}).get('client_authored') is False and type(p.get('content')) is list and len(p['content'])==1 and set(p['content'][0])=={'type','text'} and p['content'][0]['type']=='input_text' and type(p['content'][0]['text']) is str,'BACKEND_PEER_IDENTITY')
    delivered=decode_peer_body(p['content'][0]['text'],actor)
    if operation=='RUNNER_SOURCE_REVIEW_WITNESS':
        original=doc(RUNNER_REAL_PEER_AUDIT_REF)
        need(actor=='codex:/root/attach_restore_independent_review' and original.get('actor_id')==actor and original.get('Root_thread_id')==ROOT_THREAD and same_ref(binding['original_capture_ref'],original['original_capture_ref']) and binding['source_line_offsets']==original['source_line_offsets'] and binding['original_line_sha256']==original['original_line_sha256'],'EXACT_PINNED_REAL_TASK94_PLATFORM_PAIR')
        validate_task94_body(delivered,expected_refs)
    else:
        expected_verdict={'SOURCE_REVIEW_WITNESS':'SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION','RUNTIME_QUALIFICATION_ISSUANCE':'RUNTIME_CLOSURE_ACCEPTED'}.get(operation)
        need(expected_verdict is not None and delivered.get('schema')=='researchos.public21-peer-review-delivery.v1' and delivered.get('review_author')==actor and delivered.get('root_thread_id')==ROOT_THREAD and delivered.get('operation')==operation and delivered.get('verdict')==expected_verdict and delivered.get('formal_acceptance') is False and delivered.get('execution_grant') is False,'EXACT_PUBLIC21_PEER_TYPED_DELIVERY')
        need(base().exact_ref_set(delivered.get('review_refs'))==base().exact_ref_set(expected_refs),'PEER_COMPLETE_REVIEW_REFS')
    need(binding.get('peer_actor')==actor and binding.get('message_id')==p.get('id') and type(p.get('id')) is str and p['id'] and binding.get('received_at')==last['timestamp'],'PEER_FULL_REF_ID_BINDING')
    return binding,when(last['timestamp'])
def validate_root_capture(binding,raw,refs,operation=None,peer_actor=None):
    # OC3 exact raw source/three rows, typed host extraction and complete refs.
    need(binding.get('scope_key')==SCOPE_KEY,'DISTINCT_PUBLIC21_CAPTURE_SCOPE')
    return kernel()['raw_root_capture'](binding,raw,refs,operation,peer_actor)
LITERAL_MAP={
 'researchos.root-old21-external-review-witness.v1':'researchos.root-public21-external-review-witness.v1',
 'researchos.root-old21-qualified-runtime.v2':'researchos.root-public21-qualified-runtime.v1',
 'researchos.root-old21-runtime-qualification-payload.v2':'researchos.root-public21-runtime-qualification-payload.v1',
 'researchos.root-old21-runtime-qualification-scope.v2':'researchos.root-public21-runtime-qualification-scope.v1',
 'researchos.old21-runtime-independent-review-hdf.v2':'researchos.public21-runtime-independent-review-hdf.v1',
 'researchos.old21-runtime-independent-review-decision.v2':'researchos.public21-runtime-independent-review-decision.v1',
 'researchos.root-old21-runtime-manifest.v1':'researchos.root-public21-runtime-manifest.v1',
 'OLD21_RUNTIME_RESOURCE_QUALIFICATION':'PUBLIC21_RUNTIME_RESOURCE_QUALIFICATION',
 'builder_contract_ref':'runner_contract_ref','builder_source_author':'runner_source_author','go_ref':'control_ref',
 'fresh_old21_root_scope_ref':'public21_bootstrap_root_scope_ref',
 'fresh_old21_registration_facts_ref':'public21_bootstrap_registration_facts_ref',
 'OLD21_CAPTURE_OPERATION:':'PUBLIC21_CAPTURE_OPERATION:',
 'Root registered a separate fresh old21 build slice; candidate programme qualification remains pending.':'Root registered a distinct public21 bootstrap-only observation; formal acceptance remains pending.'}
def kernel():
    global _kernel
    if _kernel is None:
        original=checked(OC3_REF).decode('utf-8');tree=ast.parse(original)
        names={'own_review','runtime_review_chain','projection','validate_root_capture'}
        nodes=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        class Literals(ast.NodeTransformer):
            def visit_Constant(self,node):
                if type(node.value) is str and node.value in LITERAL_MAP:node.value=LITERAL_MAP[node.value]
                return node
            def visit_keyword(self,node):
                # OC3 projection uses update(field=value), whose field is not an
                # ast.Constant. Only these two distinct namespace pointers change.
                if node.arg in ('fresh_old21_root_scope_ref','fresh_old21_registration_facts_ref'):node.arg=LITERAL_MAP[node.arg]
                return self.generic_visit(node)
        transform=ast.fix_missing_locations(Literals().visit(ast.Module(body=nodes,type_ignores=[])))
        env=dict(base().__dict__);env.update(__file__=str(Path(__file__).resolve()),N=N,BUILDER_AUTHOR=AUTHOR,AUTHOR=AUTHOR,CALLER_AUTHOR=AUTHOR,
            CAPTURE_RESULT_SCHEMA='researchos.root-public21-capture-result.v1',CAPTURE_OPERATIONS=CAPTURE_OPS,
            validate_peer_delivery=validate_peer_delivery,STATE=STATE,ROOT=ROOT,ROOT_THREAD=ROOT_THREAD)
        exec(compile(transform,'reviewable-OC3-public21-literal-specialization','exec'),env)
        env['raw_root_capture']=env['validate_root_capture']
        env['validate_root_capture']=validate_root_capture
        _kernel=env
    return _kernel
def own_review(q): return kernel()['own_review'](q)
def current_four(refs,revisions): return base().current_four(refs,revisions)
def request_identity(q,case):
    need(q.get('schema')=='researchos.root-public21-registration-request.v1' and q.get('issued_by')==ROOT and q.get('root_thread_id')==ROOT_THREAD and q.get('scope_key')==SCOPE_KEY and q.get('formal_acceptance') is False,'NEW_ROOT_PUBLIC21_REQUEST')
    need(type(case) is dict and set(case)=={'case_id','output_root'} and type(case['case_id']) is str and re.fullmatch('[0-9a-f]{32}',case['case_id']),'EXACT_PUBLIC21_CASE')
    cid=case['case_id']; parent=B/'integration_codex'
    paths=[parent/(prefix+cid) for prefix in ('schema21-public-','public21-caller-','public21-registration-')]
    need(canonical(case['output_root'])==canonical(str(paths[0])) and canonical(q['caller_receipt_root'])==canonical(str(paths[1])) and canonical(q['registration_root'])==canonical(str(paths[2])),'DISTINCT_PUBLIC21_NAMESPACES')
    need(not any(k in q for k in ('builder_review_refs','builder_review_witness_ref','public371_registration_ref','Main23_scope_ref','old21_build_scope_ref')),'BORROWED_BUILD_OR_PUBLIC22_SCOPE')
    return dict(case_id=cid,slice_id=SCOPE_KEY+':'+cid,key='schema21_public_bootstrap_'+cid,paths=paths)

def review_member_refs(value,root):
    # The actual Task90 review MF uses relative_path metadata, not a fourth ref
    # authority field. Validate its exact namespace, then keep the strict ref.
    need(value.get('schema')=='researchos.independent-public21-source-manifest.v1' and type(value.get('members')) is list and value['members'],'EXACT_PUBLIC21_REVIEW_MANIFEST')
    refs=[]
    for member in value['members']:
        need(type(member) is dict and set(member)=={'relative_path','path','sha256','bytes'} and type(member['relative_path']) is str,'EXACT_PUBLIC21_REVIEW_MEMBER')
        rel=member['relative_path'];parts=rel.replace('\\','/').split('/')
        need(rel and not ntpath.isabs(rel) and '\x00' not in rel and ':' not in rel and all(x not in ('','.','..') for x in parts),'REVIEW_MEMBER_RELATIVE_PATH')
        ref={k:member[k] for k in ('path','sha256','bytes')};base().shape(ref)
        need(canonical(str(Path(root).joinpath(*parts)))==canonical(ref['path']),'REVIEW_MEMBER_NAMESPACE_PATH')
        refs.append(ref)
    need(len(base().exact_ref_set(refs))==len(refs),'REVIEW_MEMBER_DUPLICATE')
    return refs
def public21_review_manifest(ref):
    value=doc(ref);refs=review_member_refs(value,Path(ref['path']).parent)
    for member in refs:checked(member)
    return dict(value,members=refs)
def runner_chain(q):
    need(type(q['runner_source_refs']) is dict and set(q['runner_source_refs'])==set(LEAF_REFS) and all(same_ref(q['runner_source_refs'][k],LEAF_REFS[k]) for k in LEAF_REFS),'EXACT_NEW_REVIEWED_V2_RUNNER_SOURCE')
    source=doc(LEAF_REFS['hdf']);mf=base().manifest(LEAF_REFS['mf']);contract=doc(LEAF_REFS['contract_ref'])
    need(source.get('source_author')==AUTHOR and source.get('formal_acceptance') is False and source.get('execution_grant') is False and same_ref(source['manifest_ref'],LEAF_REFS['mf']),'RUNNER_SOURCE_HDF')
    for key in ('runner_ref','contract_ref'):
        need(same_ref(source[key],LEAF_REFS[key]) and any(same_ref(source[key],x) for x in mf['members']),'RUNNER_SOURCE_MEMBERS')
    need(contract.get('schema')=='researchos.schema21-public-bootstrap-contract.v1' and contract.get('source_author')==AUTHOR and contract.get('scope_key')==SCOPE_KEY and contract.get('runtime_grant') is False and contract.get('execution_grant') is False and same_ref(contract['runner_ref'],LEAF_REFS['runner_ref']) and same_ref(contract['old21_qualification_ref'],PROGRAMME_REF),'RUNNER_CONTRACT_SOURCE_PROGRAMME')
    refs=q['runner_review_refs'];need(type(refs) is dict and set(refs)=={'hdf','mf','decision'} and all(same_ref(refs[k],RUNNER_ACCEPTED_REVIEW_REFS[k]) for k in refs),'EXACT_ACTUAL_TASK94_RUNNER_REVIEW_REFS')
    review=doc(refs['hdf']);review_mf=base().manifest(refs['mf']);decision=doc(refs['decision']);actor=decision.get('reviewer_id')
    need(review.get('schema')=='researchos.schema21-public-bootstrap-independent-source-review-handoff.v1' and decision.get('schema')=='researchos.schema21-public-bootstrap-independent-source-decision.v1' and review.get('decision')==decision.get('decision')=='ACCEPTED_SOURCE_ONLY' and decision.get('exact_runner_inverse') is True and decision.get('findings')==review.get('findings')==[] and review.get('reviewer')==actor=='codex:/root/attach_restore_independent_review' and decision.get('source_author')==AUTHOR and actor not in (ROOT,AUTHOR),'ACTUAL_RUNNER_NONAUTHOR_ACCEPTANCE')
    need(review.get('Root_scope_or_runtime_qualification_granted') is False and review.get('Leaf_Native_Go_SQL_model_TP_calls')==0 and decision.get('Leaf_RootScope_calls')==0,'RUNNER_REVIEW_SOURCE_ONLY')
    for k,field in (('hdf','source_hdf_ref'),('mf','source_mf_ref')):
        need(same_ref(review[field],LEAF_REFS[k]) and same_ref(decision[field],LEAF_REFS[k]),'RUNNER_REVIEW_SOURCE_TARGET')
    for k in ('runner_ref','contract_ref'):need(same_ref(decision[k],LEAF_REFS[k]) and same_ref(review['source_'+k],LEAF_REFS[k]),'RUNNER_REVIEW_CODE_TARGET')
    need(same_ref(review['decision_ref'],refs['decision']) and any(same_ref(refs['decision'],x) for x in review_mf['members']) and any(same_ref(refs['hdf'],x) for x in review_mf['members']),'RUNNER_REVIEW_MANIFEST_TARGET')
    need(decision.get('formal_acceptance') is False and decision.get('execution_grant') is False and review.get('execution_grant') is False,'RUNNER_SOURCE_NOT_RUNTIME_GRANT')
    witness=doc(q['runner_review_witness_ref']);need(witness.get('schema')=='researchos.root-public21-runner-review-witness.v1' and witness.get('issued_by')==ROOT and witness.get('root_thread_id')==ROOT_THREAD and witness.get('review_author')==actor and refs_equal(witness['review_refs'],list(refs.values())),'ROOT_RUNNER_REVIEW_WITNESS')
    capture=doc(witness['capture_binding_ref']);validate_root_capture(capture,checked(capture['original_capture_ref']),list(refs.values()),'RUNNER_SOURCE_REVIEW_WITNESS',actor)
    need(when(capture['tool_result_timestamp'])<=when(witness['created_utc'])<=datetime.now(timezone.utc),'RUNNER_REVIEW_CAUSAL_ORDER')
    peer=doc(capture['peer_delivery_binding_ref'])
    allrefs=list(LEAF_REFS.values())+mf['members']+list(refs.values())+review_mf['members']+[source['input_manifest_ref'],q['runner_review_witness_ref'],witness['capture_binding_ref'],capture['original_capture_ref'],capture['peer_delivery_binding_ref'],peer['original_capture_ref'],RUNNER_REAL_PEER_AUDIT_REF]
    allrefs+=doc(source['input_manifest_ref'])['references']
    return dict(source=source,contract=contract,review=review,decision=decision,review_refs=refs,review_actor=actor,refs=allrefs)
def programme_chain():
    value=doc(PROGRAMME_REF)
    need(value.get('schema')=='researchos.root-old21-programme-qualification.v1' and value.get('issued_by')==ROOT and value.get('root_thread_id')==ROOT_THREAD and value.get('status')=='QUALIFIED_OLD21_BUILD' and value.get('programme_qualification') is True and value.get('independent_non_author') is True and value.get('source_schema_version')==21 and type(value['source_schema_version']) is int and value.get('execution_grant') is False and value.get('formal_acceptance') is False,'REAL_ROOT_BOUND_OLD21_PROGRAMME')
    need(value['review_author'] not in (ROOT,AUTHOR,value['source_author']) and value['build_executor']==ROOT,'INDEPENDENT_REAL_PROGRAMME_REVIEW')
    payload=doc(value['payload_ref'])
    need(payload.get('schema')=='researchos.root-old21-programme-binding-payload.v1' and payload.get('issued_by')==ROOT and payload.get('root_thread_id')==ROOT_THREAD and payload.get('execution_grant') is False and payload.get('formal_acceptance') is False,'PROGRAMME_ROOT_PAYLOAD')
    for key in ('control','backup'):need(same_ref(payload['program_refs'][key],value['program_refs'][key]),'PROGRAMME_PAYLOAD_PROGRAM_BYTES')
    need(base().exact_ref_set(payload['review_refs'])==base().exact_ref_set(value['review_refs']) and payload['review_author']==value['review_author'],'PROGRAMME_PAYLOAD_REVIEW_REFS')
    review_refs=value['review_refs'];review=doc(review_refs[0]);mf=base().manifest(review_refs[1]);decision=doc(review_refs[2]);qualification=doc(review_refs[3])
    need(decision.get('schema')=='researchos.old21-actual-programme-review-decision.v1' and decision.get('verdict')=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING' and decision.get('review_author')==value['review_author'] and decision.get('independent_non_author') is True and same_ref(decision['qualification_ref'],review_refs[3]) and same_ref(value['qualification_ref'],review_refs[3]),'PROGRAMME_ACTUAL_DECISION')
    for key in ('control','backup'):need(same_ref(decision['program_refs'][key],value['program_refs'][key]),'PROGRAMME_INDEPENDENT_PROGRAM_PINS')
    need(all(any(same_ref(ref,x) for x in mf['members']) for ref in review_refs[2:]),'PROGRAMME_REVIEW_MEMBERS')
    # Earlier original issuance binds an exact compact observer input with full refs.
    binding=doc(value['root_issuance_binding_ref']);first,last=base().original_capture_rows(binding,checked(binding['original_capture_ref']))
    call,out=first['payload'],last['payload']
    need(call.get('call_id')==out.get('call_id')==binding['original_call_id'] and call.get('type') in ('custom_tool_call','function_call') and out.get('type') in ('custom_tool_call_output','function_call_output') and 'OLD21_CAPTURE_OPERATION:OLD21_PROGRAMME_QUALIFICATION_BINDING' in call.get('input',call.get('arguments','')) and binding.get('operation')=='OLD21_PROGRAMME_QUALIFICATION_BINDING' and binding['tool_call_timestamp']==first['timestamp'] and binding['tool_result_timestamp']==last['timestamp'],'PROGRAMME_ACTUAL_ROOT_CALL_PAIR')
    hosts=[x for x in base().structured_documents(out['output']) if x.get('chunk_id')=='7ba7fd' and type(x.get('exit_code')) is int and x['exit_code']==0]
    need(len(hosts)==1,'PINNED_PROGRAMME_ACTUAL_HOST')
    typed=[x for x in base().structured_documents(hosts[0]['output']) if x.get('schema')=='researchos.root-old21-programme-compact-capture-result.v1'];need(len(typed)==1,'PROGRAMME_TYPED_ROOT_RESULT')
    result=typed[0];observer=doc(result['observer_input_ref'])
    need(result.get('issued_by')==result.get('observer_actor')==ROOT and result.get('root_thread_id')==ROOT_THREAD and result.get('operation')==observer.get('operation')=='OLD21_PROGRAMME_QUALIFICATION_BINDING' and result.get('all_requested_refs_read_and_verified') is True and result.get('observed_ref_count')==len(observer['observed_refs'])==136 and same_ref(result['payload_ref'],value['payload_ref']) and same_ref(observer['payload_ref'],value['payload_ref']) and result.get('peer_actor')==observer.get('peer_actor')==value['review_author'],'PROGRAMME_COMPLETE_OBSERVER_BINDING')
    peer=doc(value['independent_peer_delivery_binding_ref']);a,z=base().original_capture_rows(peer,checked(peer['original_capture_ref']),peer=True);p=z['payload']
    need(a['type']=='inter_agent_communication_metadata' and z['ordinal']==a['ordinal']+1 and 0<=(when(z['timestamp'])-when(a['timestamp'])).total_seconds()<=1 and p.get('type')=='agent_message' and p.get('author')==value['review_author'].removeprefix('codex:') and p.get('recipient')=='/root' and z.get('metadata',{}).get('client_authored') is False and len(p.get('content',[]))==1 and p['content'][0].get('type')=='input_text','PROGRAMME_ORIGINAL_PEER_IDENTITY')
    body=decode_peer_body(p['content'][0]['text'],value['review_author'])
    need(body.get('schema')=='researchos.old21-actual-programme-review-delivery.v1' and body.get('review_author')==value['review_author'] and body.get('root_thread_id')==ROOT_THREAD and body.get('verdict')=='QUALIFIED_OLD21_BUILD_PENDING_ROOT_BINDING' and body.get('independent_non_author') is True and body.get('formal_acceptance') is False and body.get('execution_grant') is False and base().exact_ref_set(body['review_refs'])==base().exact_ref_set(review_refs) and peer['message_id']==p['id'] and peer['received_at']==z['timestamp'],'PROGRAMME_ORIGINAL_PEER_FULL_REFS')
    need(when(z['timestamp'])<=when(payload['created_utc'])<=when(first['timestamp'])<=when(last['timestamp'])<=when(value['created_utc'])<=datetime.now(timezone.utc),'PROGRAMME_ORIGINAL_TIME_ORDER')
    # Historic live Canon references in old issuer observations are historical data;
    # fresh public21 authority uses its separate new current4, never those old bytes.
    immutable=[ref for ref in observer['observed_refs'] if canonical(ref['path']) not in {canonical(str(x)) for x in base().CANON}]
    refs=[PROGRAMME_REF,value['payload_ref'],value['root_issuance_binding_ref'],binding['original_capture_ref'],result['observer_input_ref'],value['independent_peer_delivery_binding_ref'],peer['original_capture_ref'],*review_refs,*mf['members'],*value['program_refs'].values(),value['provenance_ref'],*immutable]
    return dict(document=value,refs=refs)
def runtime_closure(qualification_ref,runner,preexisting_refs):
    value=doc(qualification_ref)
    need(value.get('status')=='QUALIFIED_FOR_PUBLIC21_BOOTSTRAP' and value.get('formal_programme_qualification') is False and value.get('independent_non_author') is True,'DISTINCT_PUBLIC21_RUNTIME_QUALIFICATION')
    refs=kernel()['runtime_review_chain'](qualification_ref,value,runner['contract'])
    qs=doc(value['qualification_scope_ref']);finite_lease(qs['created_utc'],qs['lease_expires_at'])
    py=pin(sys.executable);need(same_ref(py,runner['contract']['locked_python_ref']) and same_ref(value['python_ref'],py) and same_ref(value['control_ref'],runner['contract']['old21_control']),'LOCKED_PYTHON_QUALIFIED_CONTROL')
    # Import, not connect; qualify the real SQLite extension/DLL before any child.
    import sqlite3, _sqlite3
    job=base().load(runner['contract']['owned_job'],'public21_runtime_job')
    required=[py,OC3_REF,base().GUARD_REF,base().TP_REF,pin(__file__),*LEAF_REFS.values(),runner['source']['input_manifest_ref'],PROGRAMME_REF]+runner['refs']+preexisting_refs+list(doc(runner['source']['input_manifest_ref'])['references'])
    required+=[pin(x) for x in job.runtime_resource_paths()]
    for module in tuple(sys.modules.values()):
        for name in ('__file__','__cached__'):
            path=getattr(module,name,None)
            if path and Path(path).is_file():required.append(pin(path))
    qualified={canonical(x['path']):x for x in value['resource_refs']}
    need(all(canonical(ref['path']) in qualified and same_ref(ref,qualified[canonical(ref['path'])]) for ref in required),'UNQUALIFIED_PYTHON_SQLITE_DLL_WINDOWS_SOURCE_RESOURCE')
    return dict(qualification=value,refs=[qualification_ref,*refs,*value['resource_refs']])
def future_request(request_ref):
    q=doc(request_ref);case=doc(q['case_request_ref']);identity=request_identity(q,case)
    current=current_four(q['before_canonical_refs'],q['expected_revisions'])
    source=own_review(q);runner=runner_chain(q);programme=programme_chain()
    need(same_ref(runner['contract']['old21_control'],programme['document']['program_refs']['control']) and same_ref(runner['contract']['old21_backup'],programme['document']['program_refs']['backup']),'RUNNER_REAL_PROGRAMME_BINDING')
    resume=doc(q['root_resume_ref']);live=doc(q['postreview_live_ref'])
    for row in (resume,live):need(row.get('issued_by')==ROOT and refs_equal(row['canonical_refs'],q['before_canonical_refs']) and row['expected_revisions']==q['expected_revisions'],'POSTREVIEW_FULL_CURRENT4')
    need(same_ref(live['root_resume_ref'],q['root_resume_ref']) and same_ref(live['review_decision_ref'],q['review_decision_ref']) and when(live['created_utc'])>when(source['review']['reviewed_utc']) and when(q['created_utc'])>=when(live['created_utc']) and when(q['created_utc'])<=datetime.now(timezone.utc) and when(q['lease_expires_at'])>datetime.now(timezone.utc),'FRESH_ROOT_CURRENT4_FINITE_LEASE')
    capture=doc(live['capture_binding_ref']);validate_root_capture(capture,checked(capture['original_capture_ref']),q['before_canonical_refs'],'POSTREVIEW_CURRENT_FOUR')
    need(when(capture['tool_result_timestamp'])>when(source['review']['reviewed_utc']),'CURRENT4_ORIGINAL_AFTER_REVIEW')
    finite_lease(q['created_utc'],q['lease_expires_at'])
    for p in identity['paths'][:2]:safe_directory(p,new=True)
    p=identity['paths'][2];safe_directory(p,new=not p.exists())
    resources=runtime_closure(q['runtime_qualification_ref'],runner,source['refs']+programme['refs'])
    refs=[request_ref,q['case_request_ref'],q['root_resume_ref'],q['postreview_live_ref'],live['capture_binding_ref'],capture['original_capture_ref'],*source['refs'],*runner['refs'],*programme['refs'],*resources['refs']]
    return q,identity,current,source,runner,programme,resources,refs
def projection(cp,ow,scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,pending,created,identity):
    env=kernel();previous={k:env.get(k) for k in ('KEY','SLICE','STATE')}
    env.update(KEY=identity['key'],SLICE=identity['slice_id'],STATE=STATE)
    try:return env['projection'](cp,ow,scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,pending,created)
    finally:env.update(previous)
def propose(request_ref):
    q,identity,current,source,runner,programme,resources,refs=future_request(request_ref)
    pending,pending_refs=base().failure_rows(q['pending_ref'],current['documents'][0]);root=identity['paths'][2]
    held=base().guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:
        held.acquire(base().local_refs(refs+pending_refs,base().CANON[:2]));need(not root.exists(),'NEW_REGISTRATION_ROOT');root.mkdir()
        scope=dict(schema='researchos.root-public21-scope.v1',issued_by=ROOT,root_thread_id=ROOT_THREAD,scope_key=SCOPE_KEY,slice_id=identity['slice_id'],registration_request_ref=request_ref,case_request_ref=q['case_request_ref'],runner_contract_ref=LEAF_REFS['contract_ref'],runner_ref=LEAF_REFS['runner_ref'],output_root=doc(q['case_request_ref'])['output_root'],caller_receipt_root=q['caller_receipt_root'],lease_expires_at=q['lease_expires_at'],formal_acceptance=False,parent_acceptance=False)
        scope_ref=save(root/'scope.root.json',scope)
        common=dict(step_id='W05-99',slice_id=identity['slice_id'],scope_key=SCOPE_KEY,state=STATE,owner=ROOT,scope_ref=scope_ref,output_root=scope['output_root'],lease_status='ACTIVE',lease_expires_at=q['lease_expires_at'])
        owner=dict(common,owner_id=ROOT,selected_worker_id=ROOT);owner_ref=save(root/'owner.root.json',owner)
        worker=dict(common,worker_id=ROOT,selected_owner_ref=owner_ref);worker_ref=save(root/'worker.root.json',worker)
        archives=[]
        for i,raw in enumerate(current['raw']):
            with (root/(str(i)+'.before.raw.json')).open('xb') as f:f.write(raw)
            archives.append(pin(root/(str(i)+'.before.raw.json')))
        facts_ref=save(root/'facts.root.json',dict(schema='researchos.root-public21-registration-facts.v1',issued_by=ROOT,registration_request_ref=request_ref,before_canonical_refs=current['requested_refs'],before_archive_refs=archives,scope_ref=scope_ref,owner_ref=owner_ref,worker_ref=worker_ref,formal_acceptance=False))
        after=projection(*current['documents'][:2],scope_ref,owner_ref,worker_ref,facts_ref,owner,worker,pending,q['created_utc'],identity)
        for i,value in enumerate(after):save(root/(str(i)+'.after.proposed.json'),value)
    finally:
        cleanup=held.close()
        if root.is_dir():save(root/'propose.guard.closed.json',cleanup)
        need(cleanup.get('closed') is True and cleanup.get('retained_handles_count')==0 and not cleanup.get('errors'),'PROPOSE_GUARD_CLOSED')
    return facts_ref
def register(mode,facts_ref,activation_ref=None):
    need(mode in ('check','activate'),'REGISTRATION_MODE');facts=doc(facts_ref)
    q,identity,current,source,runner,programme,resources,refs=future_request(facts['registration_request_ref'])
    root=Path(q['registration_root']);need(same_ref(facts_ref,pin(root/'facts.root.json')) and facts.get('issued_by')==ROOT and refs_equal(facts['before_canonical_refs'],current['requested_refs']),'EXACT_REGISTRATION_FACTS')
    scope=doc(facts['scope_ref']);owner=doc(facts['owner_ref']);worker=doc(facts['worker_ref'])
    need(scope.get('schema')=='researchos.root-public21-scope.v1' and scope.get('issued_by')==ROOT and scope.get('root_thread_id')==ROOT_THREAD and scope.get('formal_acceptance') is False and scope.get('parent_acceptance') is False and scope['scope_key']==SCOPE_KEY and scope['slice_id']==identity['slice_id'] and same_ref(scope['registration_request_ref'],facts['registration_request_ref']) and same_ref(scope['case_request_ref'],q['case_request_ref']) and same_ref(scope['runner_ref'],LEAF_REFS['runner_ref']) and same_ref(scope['runner_contract_ref'],LEAF_REFS['contract_ref']) and scope['lease_expires_at']==q['lease_expires_at'] and canonical(scope['output_root'])==canonical(doc(q['case_request_ref'])['output_root']) and canonical(scope['caller_receipt_root'])==canonical(q['caller_receipt_root']),'SCOPE_EXACT_REQUEST')
    for row in (owner,worker):need(row.get('step_id')=='W05-99' and row.get('owner')==ROOT and row.get('scope_key')==SCOPE_KEY and row.get('slice_id')==scope['slice_id'] and row.get('state')==STATE and row.get('lease_status')=='ACTIVE' and same_ref(row['scope_ref'],facts['scope_ref']) and row.get('lease_expires_at')==scope['lease_expires_at'] and row.get('output_root')==scope['output_root'],'OWNER_WORKER_SCOPE')
    need(owner['owner_id']==owner['selected_worker_id']==worker['worker_id']==ROOT and same_ref(worker['selected_owner_ref'],facts['owner_ref']),'REGISTERED_ACYCLIC_OWNER_WORKER')
    finite_lease(q['created_utc'],scope['lease_expires_at'])
    need(len(facts['before_archive_refs'])==4 and all(checked(ref)==raw for ref,raw in zip(facts['before_archive_refs'],current['raw'])),'FOUR_COMPLETE_BEFORE_ARCHIVES')
    pending,pending_refs=base().failure_rows(q['pending_ref'],current['documents'][0])
    if mode=='activate':
        activation=doc(activation_ref);need(activation.get('schema')=='researchos.root-public21-activation.v1' and activation.get('issued_by')==ROOT and activation.get('root_thread_id')==ROOT_THREAD and activation.get('scope_key')==SCOPE_KEY and activation.get('formal_acceptance') is False and same_ref(activation['facts_ref'],facts_ref) and refs_equal(activation['before_canonical_refs'],current['requested_refs']) and when(activation['created_utc'])>when(q['created_utc']),'NEW_ROOT_ACTIVATION')
        capture=doc(activation['capture_binding_ref']);validate_root_capture(capture,checked(capture['original_capture_ref']),[facts_ref,*current['requested_refs']],'ACTIVATION_FACTS_CURRENT_FOUR')
        need(when(q['created_utc'])<when(capture['tool_result_timestamp'])<=when(activation['created_utc'])<=datetime.now(timezone.utc),'ACTIVATION_ORIGINAL_TIME')
        refs += [activation_ref,activation['capture_binding_ref'],capture['original_capture_ref']]
    refs += pending_refs+[facts_ref,facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],base().GUARD_REF,base().TP_REF,*facts['before_archive_refs'],*current['physical_refs'][2:]]
    held=base().guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);transaction=None
    def transform(cp,ow):
        need(cp==current['documents'][0] and ow==current['documents'][1],'EXCLUSIVE_PAIR_DRIFT')
        # Pure inherited OC3 projection: never reopens held Canon in callback.
        return projection(cp,ow,facts['scope_ref'],facts['owner_ref'],facts['worker_ref'],facts_ref,owner,worker,pending,q['created_utc'],identity)
    try:
        held.acquire(base().local_refs(refs,base().CANON[:2]));after=transform(*current['documents'][:2])
        if mode=='activate':transaction=base().load(base().TP_REF,'public21_TP').update_pair(current['physical_refs'][:2],transform,root,'activate')
        else:need(all(same_ref(ref,pin(p)) for ref,p in zip(current['physical_refs'],base().CANON)),'CHECK_CHANGED_CANON')
        need(all(same_ref(ref,pin(p)) for ref,p in zip(current['physical_refs'][2:],base().CANON[2:])),'SS_CM_CHANGED')
    finally:
        cleanup=held.close();save(root/(mode+'.guard.closed.json'),cleanup);need(cleanup.get('closed') is True and cleanup.get('retained_handles_count')==0 and not cleanup.get('errors'),'REGISTRATION_GUARD_CLOSED')
    return save(root/(mode+'.result.json'),dict(schema='researchos.root-public21-registration-result.v1',mode=mode,facts_ref=facts_ref,scope_ref=facts['scope_ref'],proposed_after_refs=[dict(path=str(p),sha256=hashlib.sha256(base().encoded(v)).hexdigest(),bytes=len(base().encoded(v))) for p,v in zip(base().CANON[:2],after)],transaction=transaction,complete_inverse=True,full_before_archive_refs=facts['before_archive_refs'],SS_CM_unchanged=True,formal_acceptance=False))
def live_lease(actual,new=False):
    scope=doc(actual['scope_ref']);facts=doc(actual['facts_ref']);q=doc(scope['registration_request_ref']);case=doc(actual['case_request_ref']);identity=request_identity(q,case)
    owner=doc(facts['owner_ref']);worker=doc(facts['worker_ref'])
    need(scope.get('schema')=='researchos.root-public21-scope.v1' and scope.get('issued_by')==ROOT and scope.get('root_thread_id')==ROOT_THREAD and scope.get('scope_key')==SCOPE_KEY and scope.get('slice_id')==identity['slice_id'] and scope.get('formal_acceptance') is False and scope.get('parent_acceptance') is False and same_ref(facts['scope_ref'],actual['scope_ref']) and same_ref(facts['registration_request_ref'],scope['registration_request_ref']) and same_ref(actual['case_request_ref'],scope['case_request_ref']) and same_ref(q['case_request_ref'],actual['case_request_ref']),'NEW_PUBLIC21_SCOPE_FACTS_CASE')
    expected=dict(q['expected_revisions']);expected['checkpoint']+=1;expected['path_ownership']+=1
    current=current_four(actual['current_canonical_refs'],expected);cp,ow=current['documents'][:2]
    need(refs_equal(q['before_canonical_refs'][2:],current['physical_refs'][2:]) and same_ref(cp['work_in_progress']['public21_bootstrap_root_scope_ref'],actual['scope_ref']) and same_ref(cp['work_in_progress']['public21_bootstrap_registration_facts_ref'],actual['facts_ref']),'LIVE_REGISTERED_PUBLIC21')
    task=ow['card_path_bindings']['W05-99']['subtasks'][identity['key']];workers=[x for x in cp['workers'] if x.get('slice_id')==identity['slice_id']];need(len(workers)==1,'ONE_PUBLIC21_CANON_WORKER')
    for row in (owner,worker,task,workers[0]):need(row.get('step_id')=='W05-99' and row.get('scope_key')==SCOPE_KEY and row.get('slice_id')==identity['slice_id'] and row.get('owner')==ROOT and row.get('state')==STATE and row.get('lease_status')=='ACTIVE' and same_ref(row['scope_ref'],actual['scope_ref']) and row.get('lease_expires_at')==scope['lease_expires_at'] and canonical(row['output_root'])==canonical(case['output_root']),'LIVE_OWNER_WORKER_LEASE_DRIFT')
    need(same_ref(task['owner_document_ref'],facts['owner_ref']) and same_ref(task['worker_document_ref'],facts['worker_ref']) and same_ref(workers[0]['worker_document_ref'],facts['worker_ref']) and same_ref(worker['selected_owner_ref'],facts['owner_ref']) and owner['selected_worker_id']==worker['worker_id']==ROOT,'ACYCLIC_LIVE_DOCUMENTS')
    need(when(scope['lease_expires_at'])>datetime.now(timezone.utc) and canonical(scope['output_root'])==canonical(case['output_root']) and canonical(scope['caller_receipt_root'])==canonical(q['caller_receipt_root']),'FRESH_PUBLIC21_LEASE_OUTPUT')
    need(scope['lease_expires_at']==q['lease_expires_at'] and same_ref(scope['runner_ref'],LEAF_REFS['runner_ref']) and same_ref(scope['runner_contract_ref'],LEAF_REFS['contract_ref']),'LIVE_LEAF_LEASE_BINDING')
    finite_lease(q['created_utc'],scope['lease_expires_at'],ENTRY_REMAINING_SECONDS if new else 0)
    if new:
        safe_directory(identity['paths'][0],new=True);safe_directory(identity['paths'][1],new=True)
    return scope,facts,q,identity,current
class LiveScope:
    def __init__(self,actual,held,context,resources,programme):
        self.actual=actual;self.held=held;self.context=copy.deepcopy(context);self.resources=copy.deepcopy(resources);self.programme=copy.deepcopy(programme);self.next_phase=0
    def _fresh(self):
        need(self.held is not None,'ROOT_HELD_CLOSURE_RELEASED')
        result=live_lease(self.actual);qualification=doc(self.actual['runtime_qualification_ref']);qscope=doc(qualification['qualification_scope_ref'])
        finite_lease(qscope['created_utc'],qscope['lease_expires_at'])
        return result
    def require_registered(self,contract_ref,request_ref,source_author):
        scope,*_=self._fresh();need(source_author==AUTHOR and same_ref(contract_ref,scope['runner_contract_ref']) and same_ref(request_ref,self.actual['case_request_ref']),'EXACT_REGISTERED_PUBLIC21_RUNNER')
    def require_resources(self,contract_ref,input_manifest_ref):
        scope,*_=self._fresh();need(same_ref(contract_ref,scope['runner_contract_ref']) and same_ref(input_manifest_ref,self.resources['input_manifest_ref']),'EXACT_PUBLIC21_RESOURCES')
        for key in ('input_manifest_ref','source_review_ref','resource_qualification_ref','runtime_manifest_ref','outer_host_binding_ref'):checked(self.resources[key])
        return copy.deepcopy(self.resources)
    def qualified_old21_programmes(self,contract_ref,qualification_ref):
        scope,*_=self._fresh();need(same_ref(contract_ref,scope['runner_contract_ref']) and same_ref(qualification_ref,PROGRAMME_REF),'EXACT_GENUINE_OLD21_QUALIFICATION');checked(PROGRAMME_REF)
        return copy.deepcopy(self.programme)
    def require_phase(self,phase,request_ref,output_root):
        scope,*_=self._fresh();need(self.next_phase<len(PHASES) and phase==PHASES[self.next_phase] and same_ref(request_ref,self.actual['case_request_ref']) and canonical(output_root)==canonical(scope['output_root']),'PUBLIC21_PHASE_SEQUENCE')
        if phase=='bootstrap21':
            q=doc(scope['registration_request_ref']);finite_lease(q['created_utc'],scope['lease_expires_at'],ENTRY_REMAINING_SECONDS)
            qualified=doc(self.actual['runtime_qualification_ref']);qs=doc(qualified['qualification_scope_ref']);finite_lease(qs['created_utc'],qs['lease_expires_at'],ENTRY_REMAINING_SECONDS)
        self.next_phase+=1
    def receipt_context(self):self._fresh();return copy.deepcopy(self.context)
def execute(actual_ref):
    actual=doc(actual_ref);need(actual.get('schema')=='researchos.root-public21-actual-request.v1' and actual.get('issued_by')==ROOT and actual.get('root_thread_id')==ROOT_THREAD and actual.get('scope_key')==SCOPE_KEY and actual.get('formal_acceptance') is False,'ROOT_ACTUAL_PUBLIC21_REQUEST')
    scope,facts,q,identity,current=live_lease(actual,new=True)
    source=own_review(q);runner=runner_chain(q);programme=programme_chain();resources=runtime_closure(actual['runtime_qualification_ref'],runner,source['refs']+programme['refs'])
    need(same_ref(actual['runtime_qualification_ref'],q['runtime_qualification_ref']) and same_ref(scope['runner_contract_ref'],LEAF_REFS['contract_ref']) and same_ref(scope['runner_ref'],LEAF_REFS['runner_ref']),'SCOPE_CURRENT_ACCEPTED_SOURCE')
    result=doc(actual['registration_result_ref']);need(result.get('schema')=='researchos.root-public21-registration-result.v1' and result.get('mode')=='activate' and result.get('complete_inverse') is True and result.get('SS_CM_unchanged') is True and result.get('formal_acceptance') is False and result.get('transaction') is not None and same_ref(result['facts_ref'],actual['facts_ref']) and same_ref(result['scope_ref'],actual['scope_ref']) and refs_equal(result['proposed_after_refs'],current['physical_refs'][:2]),'ACTUAL_PUBLIC21_TP_RESULT')
    journal=Path(result['transaction']['transaction_journal']);need(journal.parent==Path(q['registration_root']) and not journal.is_symlink() and not journal.is_junction(),'EXACT_PUBLIC21_TP_JOURNAL')
    committed_ref=pin(journal/'committed.json');committed=doc(committed_ref);need(committed.get('both_verified_while_exclusively_held') is True and committed.get('written_indices')==[0,1] and refs_equal(committed['after_refs'],current['physical_refs'][:2]),'PUBLIC21_ACTUAL_COMMITTED_PAIR')
    intent=doc(actual['host_call_intent_ref']);need(intent.get('issued_by')==ROOT and intent.get('kind')=='ACTUAL_HOST_CALL_INTENT' and intent.get('external_hostpair_required') is True and same_ref(intent['scope_ref'],actual['scope_ref']) and same_ref(intent['case_request_ref'],actual['case_request_ref']),'ROOT_POST_RETURN_CAPTURE_INTENT')
    pre=doc(actual['pre_entry_host_binding_ref']);expected=[actual[k] for k in ('scope_ref','facts_ref','registration_result_ref','runtime_qualification_ref')]+list(runner['review_refs'].values())+current['physical_refs']
    validate_root_capture(pre,checked(pre['original_capture_ref']),expected,'PUBLIC21_BOOTSTRAP_PREREQUISITES')
    need(when(pre['tool_result_timestamp'])<=when(actual['created_utc'])<=datetime.now(timezone.utc),'PRE_ENTRY_PAIR_ALREADY_COMPLETED')
    binding=dict(input_manifest_ref=runner['source']['input_manifest_ref'],source_review_ref=runner['review_refs']['decision'],resource_qualification_ref=actual['runtime_qualification_ref'],runtime_manifest_ref=resources['qualification']['runtime_manifest_ref'],outer_host_binding_ref=actual['pre_entry_host_binding_ref'],source_author=AUTHOR,reviewer_actor=runner['review_actor'])
    p=programme['document'];pbinding=dict(qualification_ref=PROGRAMME_REF,program_refs=p['program_refs'],source_commit=p['source_commit'],source_tree=p['source_tree'],source_schema_version=21,outer_host_binding_ref=actual['pre_entry_host_binding_ref'])
    refs=source['refs']+runner['refs']+programme['refs']+resources['refs']+[actual_ref,actual['scope_ref'],actual['facts_ref'],actual['case_request_ref'],actual['registration_result_ref'],actual['host_call_intent_ref'],actual['pre_entry_host_binding_ref'],pre['original_capture_ref'],scope['registration_request_ref'],facts['owner_ref'],facts['worker_ref'],committed_ref,*current['physical_refs'],OC3_REF,base().GUARD_REF,base().TP_REF,pin(__file__)]
    leaf=base().load(LEAF_REFS['runner_ref'],'qualified_public21_leaf')
    held=base().guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);live=None;state=None;error=None;cleanup=None;receipt_root=identity['paths'][1]
    try:
        held.acquire(base().local_refs(refs));live_lease(actual,new=True);safe_directory(receipt_root,new=True);receipt_root.mkdir()
        live=LiveScope(actual,held,dict(executor=ROOT,owner=ROOT,worker=ROOT,root_thread_id=ROOT_THREAD,scope_key=SCOPE_KEY,lease_expires_at=scope['lease_expires_at'],current_canonical_refs=current['physical_refs'],root_request_ref=actual_ref,scope_ref=actual['scope_ref'],registration_result_ref=actual['registration_result_ref'],host_call_intent_ref=actual['host_call_intent_ref'],caller_source_review_ref=q['review_decision_ref'],runner_source_review_ref=runner['review_refs']['decision'],resource_qualification_ref=actual['runtime_qualification_ref'],runtime_manifest_ref=binding['runtime_manifest_ref'],pre_entry_host_binding_ref=actual['pre_entry_host_binding_ref'],actual_bootstrap_hostpair_external_after_return=True),binding,pbinding)
        state=leaf.run_registered_case(LEAF_REFS['contract_ref'],actual['case_request_ref'],live)
        need(live.next_phase==len(PHASES) or bool(state.get('first_failure')) or str(state.get('status','')).startswith('STOPPED'),'INCOMPLETE_PUBLIC21_PHASES')
        if state.get('public_bootstrap_observed') is True:
            need(state.get('status')=='PUBLIC21_BOOTSTRAP_OBSERVED_PENDING_INDEPENDENT_REVIEW' and len(state['calls'])==1 and state['calls'][0]['actual_exit']==0 and state['closed_receipt']['status']=='PUBLISHED','OBSERVED_BOOTSTRAP_CLOSURE')
            stored=doc(state['closed_receipt']['ref'])
            need(stored['closed_receipt']['status']=='PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF' and stored['closed_receipt']['ref'] is None,'REAL_PERSISTED_LEAF_RECEIPT_SEMANTICS')
            normalized=copy.deepcopy(state);normalized['closed_receipt']=stored['closed_receipt'];need(normalized==stored,'FULL_LEAF_PERSISTED_RETURN_RECONCILIATION')
    except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc),phase='root_caller',last_child_exit=None,original_ordinal=None,Root_assignment_required=True)
    finally:
        if live is not None:live.held=None
        try:
            cleanup=held.close();need(cleanup.get('closed') is True and cleanup.get('retained_handles_count')==0 and not cleanup.get('errors'),'ROOT_PUBLIC21_GUARD_CLEANUP')
        except BaseException as exc:
            if error is None:error=dict(type=type(exc).__name__,message=str(exc),phase='root_guard_close',last_child_exit=None,original_ordinal=None,Root_assignment_required=True)
    record=dict(schema='researchos.root-public21-caller-return.v1',actual_request_ref=actual_ref,runner_returned_state=state,caller_error=error,source_guard_cleanup=cleanup,external_original_hostpair_required=True,Root_failure_assignment_required=bool(error or state and (state.get('first_failure') or str(state.get('status','')).startswith('STOPPED'))),automatic_retry=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False)
    if receipt_root.is_dir():
        try:
            if state is not None:record['persisted_runner_state_ref']=save(receipt_root/'runner-returned-state.root.json',state)
            record['return_record_ref']=save(receipt_root/'caller-return.root.json',record)
        except BaseException as exc:record['persistence_error']=dict(type=type(exc).__name__,message=str(exc),original_ordinal=None);record['Root_failure_assignment_required']=True
    record['Root_must_persist_full_return']='return_record_ref' not in record
    return record
def prepare(request_ref):
    """Root future inventory only; no Canon write, child or SQLite connection."""
    q=doc(request_ref);need(q.get('schema')=='researchos.root-public21-runtime-prepare-request.v1' and q.get('issued_by')==ROOT and q.get('root_thread_id')==ROOT_THREAD and q.get('execution_grant') is False,'ROOT_RESOURCE_PREPARE_ONLY')
    source=own_review(q);runner=runner_chain(q);programme=programme_chain();scope=doc(q['qualification_scope_ref'])
    need(scope.get('schema')=='researchos.root-public21-runtime-qualification-scope.v1' and scope.get('issued_by')==ROOT and scope.get('root_thread_id')==ROOT_THREAD and scope.get('slice_id')=='PUBLIC21_RUNTIME_RESOURCE_QUALIFICATION' and scope.get('formal_acceptance') is False and scope.get('execution_grant') is False and same_ref(scope['source_hdf_ref'],q['source_hdf_ref']) and same_ref(scope['source_mf_ref'],q['source_mf_ref']) and same_ref(scope['caller_ref'],pin(__file__)) and same_ref(scope['runner_contract_ref'],LEAF_REFS['contract_ref']) and when(scope['lease_expires_at'])>datetime.now(timezone.utc),'NEW_PUBLIC21_RESOURCE_SCOPE')
    finite_lease(scope['created_utc'],scope['lease_expires_at'])
    current=current_four(q['before_canonical_refs'],q['expected_revisions'])
    pre=doc(q['preparation_host_binding_ref']);validate_root_capture(pre,checked(pre['original_capture_ref']),[q['qualification_scope_ref'],q['source_hdf_ref'],q['source_mf_ref'],*q['runner_review_refs'].values(),*current['physical_refs']],'RUNTIME_MANIFEST_PREREQUISITES')
    import sqlite3,_sqlite3
    job=base().load(runner['contract']['owned_job'],'public21_prepared_runtime_job')
    refs=source['refs']+runner['refs']+programme['refs']+[request_ref,q['qualification_scope_ref'],q['preparation_host_binding_ref'],pre['original_capture_ref'],OC3_REF,base().GUARD_REF,base().TP_REF,pin(__file__),pin(sys.executable)]
    refs += [pin(path) for path in job.runtime_resource_paths()]
    for module in tuple(sys.modules.values()):
        for field in ('__file__','__cached__'):
            path=getattr(module,field,None)
            if path and Path(path).is_file():refs.append(pin(path))
    refs=base().local_refs(refs)
    out=safe_directory(q['output_root'],new=True);need(out.parent==B/'integration_codex' and re.fullmatch('public21-runtime-[0-9a-f]{32}',out.name),'NEW_RESOURCE_MANIFEST_NAMESPACE')
    held=base().guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:
        held.acquire(refs);out.mkdir()
        manifest_ref=save(out/'runtime-manifest.root.json',dict(schema='researchos.root-public21-runtime-manifest.v1',issued_by=ROOT,root_thread_id=ROOT_THREAD,source_author=AUTHOR,runner_source_author=AUTHOR,source_hdf_ref=q['source_hdf_ref'],source_mf_ref=q['source_mf_ref'],caller_ref=pin(__file__),runner_contract_ref=LEAF_REFS['contract_ref'],qualification_scope_ref=q['qualification_scope_ref'],resource_refs=refs,formal_acceptance=False,execution_grant=False))
    finally:
        cleanup=held.close()
        if out.is_dir():save(out/'prepare.guard.closed.json',cleanup)
        need(cleanup.get('closed') is True and cleanup.get('retained_handles_count')==0 and not cleanup.get('errors'),'PREPARE_RESOURCE_GUARD_CLOSED')
    return dict(runtime_manifest_ref=manifest_ref,independent_runtime_review_required=True,Root_qualification_issuance_required=True,execution_grant=False,formal_acceptance=False)
if __name__=='__main__':
    need(len(sys.argv) in (5,8),'USAGE_mode_ref_path_sha_bytes_optional_activation_ref')
    mode=sys.argv[1];ref=dict(path=sys.argv[2],sha256=sys.argv[3],bytes=int(sys.argv[4]))
    need(mode in ('prepare','propose','check','activate','execute'),'SOURCE_CLI_MODES')
    activation=dict(path=sys.argv[5],sha256=sys.argv[6],bytes=int(sys.argv[7])) if len(sys.argv)==8 else None
    need((mode=='activate')==(activation is not None),'ACTIVATION_REF_EXACT_MODE')
    value=prepare(ref) if mode=='prepare' else propose(ref) if mode=='propose' else execute(ref) if mode=='execute' else register(mode,ref,activation)
    print(json.dumps(value,ensure_ascii=False,allow_nan=False),flush=True)
