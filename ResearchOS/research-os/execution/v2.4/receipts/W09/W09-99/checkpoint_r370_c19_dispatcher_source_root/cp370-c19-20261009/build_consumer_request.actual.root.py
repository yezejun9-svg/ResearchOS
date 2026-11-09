"""Create two-consumer request only after independent actual registration review."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,types,sys,uuid

N=Path(__file__).resolve().parent
W=N.parent.parent
V4=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
RV=W/'cp370_actual_registration_independent_review_codex/actualr4-01a120ab'

def pin(path):
    path=path.resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(Path(ref['path']))==ref
    return Path(ref['path']).read_bytes()

def exact(path,sha,size):
    ref=dict(path=str(path.resolve(strict=True)),sha256=sha,bytes=size);read(ref);return ref

def save(path,value):
    with path.open('xb') as file:
        file.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
    return pin(path)

reviews=[exact(RV/name,sha,size) for name,sha,size in (
    ('HDF.json','22da2ded8fec67a3ef5232b1e3766d17a4b9d269ef9f6ecd7237f9b349afdee9',3016),
    ('MF.json','d545503e8beeeb7578f3728dae930f3f9f1d6d604ccf60ae9f649d8d758b2354',4470),
    ('actual-decision.json','a9fcdd5c39e6d355d9b3e9915be9c2971dae14c093d180fe25037ab453ae8a9d',5757))]
rh,rm,decision=[json.loads(read(ref)) for ref in reviews]
assert decision['decision']=='ACTUAL_REGISTRATION_VERIFIED_NONFORMAL'
assert decision['actor_id']=='codex:/root/attach_fixture_source_review' and decision['actor_role']=='INDEPENDENT_NON_AUTHOR'
assert decision['actual_registration_verified'] is True and decision['formal_acceptance'] is False and decision['parent_acceptance'] is False
assert rh['manifest_ref']==reviews[1] and reviews[2] in rm['members']
vector_ref=exact(N/'Main-C19-consumers-current-canonical-vector.actual.root.json','9583d32014e3b06bd3f80b20e019cab6ee869e44913dac0b24a9cc3b0c993ed5',1075)
vector=json.loads(read(vector_ref))
assert vector['refs']==decision['current_canonical_refs']
for ref in vector['refs']:read(ref)
facts_ref=exact(V4/'registration-facts.root.json','285a0ebebaa067be95108e25ba32500e027652eefe81adfb77e2dd796a809232',4843)
facts=json.loads(read(facts_ref));scope_ref=facts['scope_ref'];scope=json.loads(read(scope_ref))
assert decision['root_facts_ref']==facts_ref
result_ref=decision['actual_registration_result_ref'];result=json.loads(read(result_ref))
assert result['mode']=='activate' and result['proposed_after_refs']==vector['refs'][:2]
proof=dict(schema='researchos.root-main-c19-two-dispatcher-actual-registration-proof.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),
    scope_ref=scope_ref,current_canonical_vector_ref=vector_ref,previous_checkpoint_revision=369,registered_checkpoint_revision=370,
    registration_result_ref=result_ref,actual_registration_original_tool_io_ref=pin(N/'registrar-v4-activate.actual.original-tool-io.root.json'),
    actual_registration_independent_review_refs=reviews,actual_registration_verified=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0)
proof_ref=save(N/'Main-C19-two-dispatcher-registration-proof.actual.root.json',proof)
build_request=json.loads(read(facts['build_request_ref']))
output=Path(scope['authorized_output_root'])/('run-'+uuid.uuid4().hex)
assert not output.exists()
request=dict(schema='researchos.w09-c19-two-dispatcher-root-request.v1',issued_by='codex:/root',scope_ref=scope_ref,current_canonical_vector_ref=vector_ref,
    actual_registration_proof_ref=proof_ref,current_owner_ref=facts['owner_document_ref'],current_worker_ref=facts['worker_document_ref'],
    source_hdf_ref=scope['source_hdf_ref'],source_review_ref=scope['source_review_ref'],native_qualified_hdf_ref=scope['native_qualified_hdf_ref'],
    native_handoff_ref=scope['native_handoff_ref'],native_historical_request_ref=scope['native_historical_request_ref'],
    historical_cp369_archives=build_request['historical_cp369_archives'],output_dir=str(output),exact_routes=['test.research.fixture','test.retrieval'],
    formal_acceptance=False,native_producer_rerun=False,registry_writes=False,canonical_writes=False,go_provider_calls=False)
caller_ref=scope['caller_ref'];raw=read(caller_ref)
assert caller_ref['sha256']=='f3d044d49980f4399ee91723d9548fd3f856999de38d082b43cd262b025bc9de' and caller_ref['bytes']==37305
module=types.ModuleType('root_accepted_c19_caller_request_validation');module.__file__=caller_ref['path'];sys.modules[module.__name__]=module
exec(compile(raw,caller_ref['path'],'exec'),module.__dict__)
checked_scope,checked_output,_=module.root_request(request)
assert checked_scope==scope and checked_output==output
for ref in vector['refs']:read(ref)
request_ref=save(N/'Main-C19-two-dispatcher-request.actual.root.json',request)
resume=json.loads((N/'RESUME.cp370-registered.live1005.root.json').read_bytes())
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),CP370_status='ACTUAL_ROOT_REGISTRATION_INDEPENDENTLY_VERIFIED_NONFORMAL',
    C19_actual_consumers_status='REQUEST_FROZEN_NOT_RUN',C19_actual_consumer_request_ref=request_ref,C19_actual_registration_proof_ref=proof_ref,
    CP370_actual_independent_review_refs=reviews,C19_actual_output_dir=str(output))
resume_ref=save(N/'RESUME.cp370-consumers-request-ready.live1005.root.json',resume)
print(json.dumps(dict(request_ref=request_ref,registration_proof_ref=proof_ref,resume_ref=resume_ref,output_dir=str(output),
    pure_caller_request_validation_passed=True,next_original=1005,dispatcher_run=False,Native_rerun=False,formal_delta=0),ensure_ascii=False),flush=True)
