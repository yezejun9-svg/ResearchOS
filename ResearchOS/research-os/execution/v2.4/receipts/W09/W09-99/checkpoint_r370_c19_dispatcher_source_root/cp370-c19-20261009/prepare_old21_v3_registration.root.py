"""Bind completed post-review readback and prepare a fresh old21 Root request."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,os,types,sys,uuid
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99';M=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='65e92d' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,106033,match,root=True);assert pair
binding=json.loads(Path(pair[1]['path']).read_bytes())
binding.update(source_audit_path=AUDIT.as_posix(),operation='POSTREVIEW_CURRENT_FOUR')
binding_ref=save('old21.v3.postreview-current4.binding.actual.root.json',binding)
post=json.loads((N/'old21.v3.postreview-current4.payload.actual.root.json').read_bytes())
post.update(capture_binding_ref=binding_ref,created_utc=datetime.now(timezone.utc).isoformat())
post_ref=save('old21.v3.postreview-current4.artifact.actual.root.json',post)
for ref in post['canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
prepared=json.loads((N/'old21.v3.prepared-review-bindings.root.json').read_bytes())
witnesses=json.loads((N/'old21.v3.source-witnesses.sealed.actual.root.json').read_bytes())['sealed']
case=uuid.uuid4().hex;parent=B/'integration_codex'
out=parent/('old21-build-'+case);caller_out=parent/('old21-caller-'+case);registration=parent/('old21-registration-'+case)
assert not any(p.exists() for p in (out,caller_out,registration))
case_ref=save('old21.v3.case-request.actual.root.json',dict(case_id=case,output_root=str(out)))
now=datetime.now(timezone.utc)
q=dict(schema='researchos.root-old21-registration-request.v1',issued_by='codex:/root',formal_acceptance=False,
    before_canonical_refs=post['canonical_refs'],expected_revisions=post['expected_revisions'],
    source_hdf_ref=exact(M/'HDF.json','37d0152dd58020f7c1be76d1a66b6fa2363de8782668998ad89080c84257a45b',12041),
    source_mf_ref=exact(M/'MF.json','e91b682efa8220d95ec9c54a4e6348a6f1a5736e133bb662475836384a46e176',11639),
    review_hdf_ref=prepared['caller']['review_refs'][0],review_mf_ref=prepared['caller']['review_refs'][1],
    review_decision_ref=prepared['caller']['review_refs'][2],review_hostpair_witness_ref=witnesses['caller']['witness_ref'],
    builder_review_refs=dict(zip(('hdf','mf','decision'),prepared['builder']['review_refs'])),
    builder_review_witness_ref=witnesses['builder']['witness_ref'],root_resume_ref=post['root_resume_ref'],postreview_live_ref=post_ref,
    created_utc=now.isoformat(),lease_expires_at=(now+timedelta(hours=24)).isoformat(),case_request_ref=case_ref,
    caller_receipt_root=str(caller_out),registration_root=str(registration),
    pending_ref=exact(N/'pending-diagnostics.cp373.live1097.root.json','fd7176305e001328ace48dd955a6f89c4f24d0b803667252293af25543c347ac',38468),
    runtime_qualification_ref=exact(N/'old21.v3.runtime-qualification.issued.actual.root.json','d7d01a113e030fba139039c109ba91c687b9e217ff5ec73a93959ff0f8d09a29',38051))
q_ref=save('old21.v3.registration-request.actual.root.json',q)
# The actual CLI performs runtime_closure in its own module context; this prep
# only checks the completed Root capture and unchanged current four bytes.
p=M/'old21_root.source.py';exact(p,'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06',65191)
reader=types.ModuleType('root_old21_postreview_verifier');reader.__file__=str(p);sys.modules[reader.__name__]=reader
exec(compile(p.read_bytes(),str(p),'exec'),reader.__dict__)
reader.validate_root_capture(binding,Path(pair[0]['path']).read_bytes(),post['canonical_refs'],'POSTREVIEW_CURRENT_FOUR')
print(json.dumps(dict(registration_request_ref=q_ref,case_request_ref=case_ref,case_id=case,
    output_root=str(out),caller_receipt_root=str(caller_out),registration_root=str(registration),
    current_canonical_refs=post['canonical_refs']),ensure_ascii=False,indent=2))
