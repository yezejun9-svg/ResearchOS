"""Prepare and finish Root stage grants from genuine fixed actual records."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import copy, hashlib, json, os, sys, uuid
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';W=V/'receipts/W09/W09-99';S=Path(__file__).resolve().parent
SOURCE=W/'w09_formal_root_bridge_source_codex/bridge-20261010-08'
REVIEW=W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-08-backup'
RUN=W/'w09_br8_actual_root/actual-20261010-01'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(p,rel=False):
    p=Path(p);b=p.read_bytes();return dict(path=p.relative_to(R).as_posix() if rel else str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes'])
    return b
def doc(ref):return json.loads(checked(ref))
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save(p,value,raw=False):
    b=value if raw else encoded(value)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
def role_proof(original_audit_ref,actor,role,artifact_ref,stem):
    a=doc(original_audit_ref);raw_ref=a['original_capture_ref'];raw=checked(raw_ref);lines=raw.splitlines(keepends=True)
    assert len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==a['original_line_sha256']
    events=[json.loads(x) for x in lines];assert events[0]['payload']['id']==THREAD
    assert artifact_ref['sha256'] in (lines[1]+lines[2]).decode('utf-8')
    if actor=='codex:/root':
        assert events[1]['payload']['call_id']==events[2]['payload']['call_id']
    else:
        assert events[1]['type']=='inter_agent_communication_metadata'
        assert events[2]['payload']['author']==actor and events[2]['metadata']['client_authored'] is False
        assert events[2]['ordinal']==events[1]['ordinal']+1 and events[2]['timestamp']==events[1]['timestamp']
    with Path(a['source_audit_path']).open('rb') as f:
        for offset,line in zip(a['source_line_offsets'],lines):f.seek(offset);assert f.readline()==line
    origin=R/'execution/v2.4/root_original_events/W09/W09-99'/('br8-'+stem)
    origin.mkdir(parents=True,exist_ok=False);copied=save(origin/'actual.original.raw.jsonl',raw,True)
    assert copied['sha256']==raw_ref['sha256'] and copied['bytes']==raw_ref['bytes']
    roleaudit=dict(schema='researchos.w09.actual-role-audit.v1',actor_id=actor,role=role,Root_thread_id=THREAD,
        source_audit_path=Path(a['source_audit_path']).as_posix(),source_line_offsets=a['source_line_offsets'],original_line_sha256=a['original_line_sha256'],
        source_prefix_size_observed=a['source_prefix_size_observed'],original_capture_ref=pin(Path(copied['path']),True),binding_sha256=artifact_ref['sha256'])
    ap=RUN/(stem+'.actual-role-audit.root.json');save(ap,roleaudit)
    p=Path(artifact_ref['path']);p=p if p.is_absolute() else R/p
    return dict(role=role,actor_id=actor,raw_ref=pin(p,True),actual_audit_ref=pin(ap,True))

mode=sys.argv[1]
if mode=='initialize':
    assert len(sys.argv)==2 and not RUN.exists();RUN.mkdir(parents=True)
    template=W/'w09_br6_seed_input_preparation_codex/prepare-20261010-01/context-input.main-format.template.json'
    assert pin(template)['sha256']=='d84a956c2179e3ae2e33dc2d2e69e398cbe907c29fb68b03c7ea7f18dcb58da0'
    context=json.loads(template.read_bytes());context['run_id']=uuid.uuid4().hex
    q=W/'full_w09_nf6_actual_independent_review_codex/review-actual-nf6-20261010-01/six-Mode-publication.result.json'
    assert pin(q)['sha256']=='c1498beda7203209529f643428c8063245c1d25e246db3e346c7cd4567f689df'
    modes=json.loads(q.read_bytes());assert modes['Mode_verified_count']==6 and modes['primary_error'] is None and modes['all_guards_closed'] and modes['retained_handles_count']==0
    assert len(context['registered_commands'])==len(modes['mode_decisions'])==6
    for command,item in zip(context['registered_commands'],modes['mode_decisions']):
        assert item['route']==[command['command_key'],'W09',command['check_id'],command['case_id']]
        checked(item['mode_ref']);ref=item['mode_consumption_ref'];checked(ref)
        command['mode_decision_ref']={k:ref[k] for k in ('path','sha256')}
    inp=save(RUN/'context-input.actual.root.json',context)
    accepted=pin(REVIEW/'review-decision.json');assert accepted['sha256']=='53761525a1282a463d5d607183e1525b86f1f023f106f596649934b651feb7fd'
    a=pin(S/'w09.bridge08-independent-source-review.actual-audit.root.json');assert a['sha256']=='388a109b2349ee017404db7ae58e2e9ee1987f69adccb9e8ba9f64a901f4a69f'
    proof=role_proof(a,'/root/backup_regression_resources','SOURCE_REVIEWER',accepted,'source-review')
    config=dict(formal_run_id=context['run_id'],context_input_ref=inp,source_review_audit=proof)
    cr=save(RUN/'configuration.root.json',config)
    print(json.dumps(dict(configuration_ref=cr,context_input_ref=inp,formal_run_id=context['run_id'],formal_acceptance=False),ensure_ascii=False))
elif mode=='prepare':
    assert len(sys.argv)==4;stage=sys.argv[2];extras=json.loads(Path(sys.argv[3]).read_bytes())
    config=json.loads((RUN/'configuration.root.json').read_bytes());now=datetime.now(timezone.utc);sid=uuid.uuid4().hex
    req=dict(schema='researchos.w09-root-bridge-request.v1',actor_id='codex:/root',stage=stage,Root_thread_id=THREAD,
        created_at=now.isoformat(),expires_at=(now+timedelta(minutes=55)).isoformat(),current4=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],
        output_directory=str(RUN/(stage+'-'+sid)),bridge_temp_parent=r'C:\Users\yqyyds\.researchos\w09-native-v5',
        resource_parent_ref=pin(S/'physical-C-native-v5-resource-parents.closed.root.json'),resource_audit_ref=pin(S/'w09.physical-C-native-v5-resource-parent.actual-audit.root.json'),resource_owner_sha256='d8de9a1122404c0f3a8edc4874ea3f95446cf743353428f5e91d8934b3027f12',
        bridge_source_ref=pin(SOURCE/'w09_root_bridge.source.py'),consumer_launcher_ref=pin(SOURCE/'consumer_launch.source.py'),source_hdf_ref=pin(SOURCE/'HDF.json'),source_mf_ref=pin(SOURCE/'MF.json'),source_review_ref=pin(REVIEW/'review-decision.json'),source_review_audit=config['source_review_audit'])
    assert req['bridge_source_ref']['sha256']=='22e642b51fb9f7a13b2dcb9db3057078f5479c16fb91fe0deded6b0109d1fb09'
    assert not set(extras).intersection(req);req.update(extras)
    body=save(RUN/(stage+'-'+sid+'.request.body.root.json'),req)
    grant=save(RUN/(stage+'-'+sid+'.grant.root.json'),dict(issued_by='codex:/root',stage=stage,request_body_sha256=hashlib.sha256(encoded(req)).hexdigest(),issued_at=now.isoformat(),execution_grant_scope=stage,formal_acceptance=False))
    prepared=save(RUN/(stage+'-'+sid+'.prepared.root.json'),dict(stage=stage,stage_id=sid,request_body_ref=body,grant_ref=grant))
    print(json.dumps(dict(prepared_ref=prepared,grant_ref=grant,request_body_ref=body,formal_acceptance=False,Canonical_written=False),ensure_ascii=False))
elif mode=='finalize':
    assert len(sys.argv)==8
    pr=dict(path=sys.argv[2],sha256=sys.argv[3],bytes=int(sys.argv[4]));ar=dict(path=sys.argv[5],sha256=sys.argv[6],bytes=int(sys.argv[7]))
    prepared=doc(pr);req=doc(prepared['request_body_ref']);grant=prepared['grant_ref'];checked(grant)
    proof=role_proof(ar,'codex:/root','ROOT_STAGE_GRANT',grant,prepared['stage']+'-'+prepared['stage_id'])
    req.update(grant_ref=grant,grant_audit=proof)
    final=save(RUN/(prepared['stage']+'-'+prepared['stage_id']+'.request.actual.root.json'),req)
    print(json.dumps(dict(request_ref=final,stage=prepared['stage'],output_directory=req['output_directory'],formal_acceptance=False),ensure_ascii=False))
else:raise ValueError('EXACT_THREE_METADATA_MODES')
