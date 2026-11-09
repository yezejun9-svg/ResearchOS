"""Root verifies real peer deliveries and prepares three bounded readbacks."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, types, sys

N = Path(__file__).resolve().parent
R = Path(r'D:\作品集\ResearchOS\research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')

def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def exact(p, sha, size):
    ref = pin(p); assert (ref['sha256'], ref['bytes']) == (sha, size)
    return ref

def save(name, value):
    p = N / name
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()
    with p.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)

caller = exact(B / 'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py',
    'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06', 65191)
module = types.ModuleType('old21_root_binding_readonly')
module.__file__ = caller['path']; sys.modules[module.__name__] = module
exec(compile(Path(caller['path']).read_bytes(), caller['path'], 'exec'), module.__dict__)
groups = {
    'caller': ('schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-03',
        'codex:/root/full_w09_source_review', 'SOURCE_REVIEW_WITNESS', [
        ('318d460e0db51bb63b205396ff0e38d21e4fae5decfc2980bad8ecca8b8dc117',4863),
        ('486e3f6c97f9a8c5668d62219d369743b22bcf56cd5ae6e18d586e451aba7a53',6354),
        ('60b1ef04b5b4727f96d507539b6093aa46ede6874b0b8eac353e99cb1c55c1c5',8704)]),
    'builder': ('schema21_programme_builder_independent_source_review_codex/review-main21b-20261010-01',
        'codex:/root/full_w09_source_review', 'BUILDER_SOURCE_REVIEW_WITNESS', [
        ('5c50677387c3d737561124eb1cd4b0d0e0b87e9ebdb5bce38f1230a6dd697ed1',4353),
        ('15047b67e37c5423a2a5a711111f2e3580bd88cbd818d58a0ae3c86c366c0a06',8413),
        ('820a39f52557593591877f47f346321a97cffd5229adf98dcc9fc2a71f5937ee',7082)]),
    'runtime': ('schema21_runtime_resource_independent_review_codex/runtime-s21root-20261010-03',
        'codex:/root/attach_fixture_source_review', 'RUNTIME_QUALIFICATION_ISSUANCE', [
        ('7a298dc71a11337feb57a5382941ac739728da2c69daf2a36e22e272241efe43',4428),
        ('d146a528ce85f03afd2d1f33d556506604a086d9a587a30196b4bd5d174e7a74',50577),
        ('6bc128395e828a42a9244b963587d77988b6ec28e328e0bcd20045882700fe08',37145)])}
groups = {k:v for k,v in groups.items() if k == 'runtime'}
prepared = {}
for key, (folder, actor, operation, pins) in groups.items():
    refs = [exact(B/folder/name, sha, size) for name,(sha,size) in zip(('HDF.json','MF.json','decision.json'),pins)]
    hdf, mf, decision = [json.loads(Path(x['path']).read_bytes()) for x in refs]
    for ref in mf['members']:
        exact(ref['path'],ref['sha256'],ref['bytes'])
    if key == 'builder':
        origin = B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-01'
        observation = json.loads((origin/'actual-Task68-Root-received-Final.observation.json').read_bytes())
        raw = Path(exact(origin/'actual-Task68-Root-received-Final.raw.jsonl',
            '797f80403540a5f9da512f47d8698498c40bf36869fb5b4b4f64600e8d57e083',27173)['path']).read_bytes()
        lines = raw.splitlines(keepends=True)
        offsets = observation['source_line_offsets']; prefix_size = observation['source_prefix_size_observed']
    else:
        matches = []; previous = None
        envelope = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: '+actor.removeprefix('codex:')+'\nPayload:\n'
        with AUDIT.open('rb') as f:
            header = f.readline(); f.seek(0,2); prefix_size = f.tell()
            start = max(len(header),prefix_size-32*1024*1024); f.seek(start)
            if start>len(header): f.readline()
            while True:
                pos=f.tell(); line=f.readline()
                if not line: break
                event=json.loads(line); p=event.get('payload',{})
                if event.get('type')=='response_item' and isinstance(p,dict) and p.get('type')=='agent_message' and p.get('author')==actor.removeprefix('codex:') and p.get('recipient')=='/root':
                    content=p.get('content',[])
                    if len(content)==1 and content[0].get('type')=='input_text':
                        text=content[0].get('text','')
                        if text.startswith(envelope):
                            try: delivered=json.loads(text[len(envelope):])
                            except ValueError: delivered=None
                            if isinstance(delivered,dict) and delivered.get('schema')=='researchos.old21-peer-review-delivery.v2' and delivered.get('operation')==operation and module.exact_ref_set(delivered.get('review_refs'))==module.exact_ref_set(refs):
                                matches.append((previous,(line,pos,event)))
                previous=(line,pos,event)
        assert len(matches)==1, (key,'ONE_TRUE_PEER_FINAL_REQUIRED')
        (first,fp,fe),(last,lp,le)=matches[0]
        lines=[header,first,last]; offsets=[0,fp,lp]; raw=b''.join(lines)
    events=[json.loads(x) for x in lines]
    first,last=events[1:]
    assert first['type']=='inter_agent_communication_metadata' and last['ordinal']==first['ordinal']+1
    assert 0 <= (module.when(last['timestamp'])-module.when(first['timestamp'])).total_seconds() <= 1 and last['metadata']['client_authored'] is False
    with AUDIT.open('rb') as f:
        for off,line in zip(offsets,lines):
            assert off+len(line)<=prefix_size
            f.seek(off); assert f.readline()==line
    raw_ref=save('old21.v3.'+key+'.peer.raw.jsonl',raw)
    binding=save('old21.v3.'+key+'.peer.binding.root.json',dict(
        schema='researchos.root-actual-peer-capture-binding.v2',issued_by='codex:/root',root_thread_id=THREAD,
        peer_actor=actor,original_capture_ref=raw_ref,source_audit_path=AUDIT.as_posix(),
        source_prefix_size_observed=prefix_size,source_line_offsets=offsets,source_line_bytes=[len(x) for x in lines],
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
        message_id=last['payload']['id'],received_at=last['timestamp']))
    module.validate_peer_delivery(binding,refs,actor,operation)
    if key=='runtime':
        assert decision['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and decision['independent_non_author'] is True
        fields=('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref','runtime_manifest_ref')
        payload=dict(schema='researchos.root-old21-runtime-qualification-payload.v2',issued_by='codex:/root',
            root_thread_id=THREAD,status='QUALIFIED_FOR_OLD21_BUILD',independent_non_author=True,
            formal_programme_qualification=False,review_author=actor,resource_refs=decision['resource_refs'],
            review_hdf_ref=refs[0],review_mf_ref=refs[1],review_decision_ref=refs[2],review_hostpair_binding_ref=binding,
            payload_created_utc=datetime.now(timezone.utc).isoformat())
        for field in fields: payload[field]=decision[field]
        for ref in decision['resource_refs']: exact(ref['path'],ref['sha256'],ref['bytes'])
        payload_ref=save('old21.v3.runtime-qualification.payload.actual.root.json',payload)
        observed=[payload_ref,decision['qualification_scope_ref']]+refs+[binding]; observed_actor=None
    else:
        payload_ref=None; observed=refs; observed_actor=actor
    observer=save('old21.v3.'+key+'.observer-input.root.json',dict(operation=operation,observed_refs=observed,peer_actor=observed_actor))
    prepared[key]=dict(review_refs=refs,peer_binding_ref=binding,observer_input_ref=observer,payload_ref=payload_ref)
summary=save('old21.v3.prepared-runtime-binding.root.json',prepared)
print(json.dumps(dict(prepared_ref=summary,prepared=prepared),ensure_ascii=False,indent=2))
