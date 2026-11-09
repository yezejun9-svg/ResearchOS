"""Root observes real reviewer finals and refreshes a readonly existing-case request."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,os,uuid
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
names={'pin','exact','save','outputs','capture'}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),'<Root-public-reader-helpers>','exec'),globals())
def doc(p):return json.loads(Path(p).read_bytes())
def verify(ref):
    got=pin(Path(ref['path']));assert (got['sha256'],got['bytes'])==(ref['sha256'],ref['bytes']);return ref
def peer(actor,refs,stem):
    found=[];previous=None
    with AUDIT.open('rb') as f:
        hraw=f.readline();f.seek(0,2);size=f.tell();start=max(len(hraw),size-16*1024*1024);f.seek(start)
        if start>len(hraw):f.readline()
        while True:
            pos=f.tell();raw=f.readline()
            if not raw:break
            e=json.loads(raw);p=e.get('payload',{})
            if isinstance(p,dict) and e.get('type')=='response_item' and p.get('type')=='agent_message' and p.get('author')==actor.removeprefix('codex:') and p.get('recipient')=='/root':
                c=p.get('content',[])
                if isinstance(c,list) and len(c)==1 and c[0].get('type')=='input_text':
                    text=c[0].get('text','')
                    if text.startswith('Message Type: FINAL_ANSWER\n') and all(x['sha256'] in text for x in refs):
                        assert previous is not None
                        found.append((previous,(raw,pos,e)))
            previous=(raw,pos,e)
    assert len(found)==1,'ONE_ACTUAL_FULL_REF_FINAL_REQUIRED'
    (first,fp,fe),(last,lp,le)=found[0]
    assert fe['type']=='inter_agent_communication_metadata' and le['ordinal']==fe['ordinal']+1
    assert fe['timestamp']==le['timestamp'] and le['metadata']['client_authored'] is False
    lines=[hraw,first,last];offsets=[0,fp,lp]
    with AUDIT.open('rb') as f:
        for off,raw in zip(offsets,lines):f.seek(off);assert f.read(len(raw))==raw
    with (N/(stem+'.raw.jsonl')).open('xb') as f:f.write(b''.join(lines));f.flush();os.fsync(f.fileno())
    rawref=pin(N/(stem+'.raw.jsonl'))
    return save(stem+'.binding.root.json',dict(schema='researchos.root-actual-peer-capture-binding.v2',
        issued_by='codex:/root',root_thread_id=THREAD,peer_actor=actor,original_capture_ref=rawref,
        source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=offsets,
        source_line_bytes=[len(x) for x in lines],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
        message_id=le['payload']['id'],received_at=le['timestamp'],formal_authority=False))
rc=B/'public22_existing_observation_root_caller_source_codex/recheckroot-20261009-01'
source=doc(rc/'HDF.json');i=doc(Path(source['source_inputs_ref']['path']))
review=B/'public22_existing_observation_root_caller_independent_source_review_codex/review-20261010-01'
hdf=exact(review/'HDF.json','962ec37b0dd7b1c18987e72328f6c96b6048a15f4398bc0e094d9a0d7caf9f87',6566)
mf=exact(review/'MF.json','d2d153cc58543cc085e8b917fe813027232caf92659e98b95462d55f7562bf0a',31781)
decision=exact(review/'decision.json','6fdd5d4e5bd08e82070c63cf0c6ea80f6889f44cdbe7db97290dbfc489a61893',5182)
own=peer('codex:/root/backup_regression_resources',[hdf,mf,decision],'public22.readonly.peer.caller-source')
leaf=peer('codex:/root/attach_fixture_source_review',[i[k] for k in ('leaf_review_hdf_ref','leaf_review_mf_ref','leaf_review_decision_ref')],'public22.readonly.peer.leaf-source')
def post(call,result):return any(x.get('chunk_id')=='f4a9a8' for x in outputs(result['payload'].get('output')))
live=capture(AUDIT,106000,post,root=True);assert live is not None
observed=doc(N/'public22.readonly.postreview.observed.root.json')
for ref in observed['canonical_refs']:verify(ref)
assert observed['case_request_ref']==i['case_request_ref']
case_id=uuid.uuid4().hex;now=datetime.now(timezone.utc)
q=dict(schema='researchos.root-public22-existing-registration-request.v1',issued_by='codex:/root',
    mode='READONLY_EXISTING_PUBLIC22_ORIGINAL1025',formal_acceptance=False,parent_acceptance=False,
    case_request_ref=i['case_request_ref'],evidence=i['evidence'],
    source_hdf_ref=pin(rc/'HDF.json'),source_mf_ref=source['manifest_ref'],
    review_hdf_ref=hdf,review_mf_ref=mf,review_decision_ref=decision,
    leaf_review_audit_ref=leaf,review_audit_ref=own,
    before_canonical_refs=observed['canonical_refs'],expected_revisions=observed['expected_revisions'],
    lease_id=uuid.uuid4().hex,lease_issued_at=now.isoformat(),lease_expires_at=(now+timedelta(minutes=55)).isoformat(),
    recheck_id=case_id,registration_root=str(B/'integration_codex'/('public22-recheck-registration-'+case_id)),
    receipt_root=str(B/'integration_codex'/('public22-recheck-observation-'+case_id)),
    postreview_live_audit_ref=live[1],created_utc=now.isoformat())
qref=save('public22.readonly.registration-request.actual.root.json',q)
index=save('public22.readonly.prepared.index.root.json',dict(request_ref=qref,caller_ref=source['caller_ref'],
    new_native_children=0,original1025_result='FAILED_RETAINED',formal_acceptance=False))
print(json.dumps(dict(index_ref=index,request_ref=qref,caller_ref=source['caller_ref']),ensure_ascii=False,indent=2))

