"""Read-only validation of actual Root adoption; no product or full test rerun."""
import hashlib
import json
from pathlib import Path
import runpy
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
ADOPT=REPO/'execution/v2.4/receipts/W09/W09-99/header_gate_root_adoption_codex/20261012-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):
    raw=p.read_bytes()
    return {'path':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
adoption=read(ADOPT/'adoption.json')
checkpoint=read(REPO/'execution/v2.4/checkpoint.json')
authority=checkpoint['work_in_progress']['w09_header_metadata_correction']
assert authority==adoption['authority']
assert checkpoint['revision']==adoption['checkpoint_revision']==402
for key in ('certificate_ref','verifier_module_ref','review_ref','delivery_ref'):
    assert ref(REPO/authority[key]['path'])==authority[key]
assert authority['review_ref']['sha256']=='cc153c9b6874e4a759138dffb2b9529643038f07f93d6727aa550c0f50e17205'
assert authority['certificate_ref']['sha256']=='9559bed246c7551c2cd78b1e17481c2da61c4b8ede6963ddf3a25a17bacde235'
assert adoption['installed_profile_ref']['sha256']=='c021c53b459cd0e8e2903d74c7112144830004c427c537b2104cd4c52c10c162'
assert ref(REPO/adoption['installed_profile_ref']['path'])==adoption['installed_profile_ref']
assert ref(REPO/adoption['helper_ref']['path'])==adoption['helper_ref']
cert=read(REPO/authority['certificate_ref']['path'])
assert ref(REPO/cert['index_ref']['path'])['sha256']==cert['index_ref']['sha256']
for original in cert['original_roots'].values(): assert ref(REPO/original['path'])==original
capture=read(REPO/authority['delivery_ref']['path'])
assert ref(REPO/capture['original_capture_ref']['path'])==capture['original_capture_ref']
lines=(REPO/capture['original_capture_ref']['path']).read_bytes().splitlines(keepends=True)
with Path(capture['source_audit_path']).open('rb') as f:
    for offset,digest,line in zip(capture['source_line_offsets'],capture['original_line_sha256'],lines):
        f.seek(offset); assert f.readline()==line and hashlib.sha256(line).hexdigest()==digest
header,meta,message=map(json.loads,lines)
assert message['payload']['id']==adoption['actual_message_id']=='amsg_01a12ed1-d639-77b2-8035-a9920dbf2fae'
assert (meta['ordinal'],message['ordinal'])==(561,562)
assert message['payload']['author']=='/root/w09_header_gate_review' and message['payload']['recipient']=='/root'
assert message['metadata']['client_authored'] is False

index=runpy.run_path(str(REPO/'execution/v2.4/formal_case_index.py'),run_name='post_adoption_index')
api=index['_profile_api']()
profile=runpy.run_path(str(REPO/'execution/v2.4/formal_profile_w09.py'),run_name='post_adoption_profile')
roots={k:REPO/v['path'] for k,v in cert['original_roots'].items()}
reader=api.Reader(REPO);reader.w09_audit_ranges=[]
correction=profile['_header_correction'](api,reader,roots)
assert correction['certificate']==cert and len(reader.w09_audit_ranges)==21
reader.finish()
snapshot={'files':{str(p):d for p,d in reader.read_hashes.items()},'audit_ranges':reader.w09_audit_ranges,'inventories':[]}
recheck=index['recheck_inputs'](snapshot);assert recheck=={'status':'PASS'}
(OUT/'post-adoption-authorization-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
context=read(roots['context'])
reader.w09_header_correction=correction
try:profile['_vector'](api,reader,context)
except api.InvalidEvidence as exc:
    assert exc.code=='NEEDS_REVALIDATION' and 'internal/domain/backup.go' in str(exc)
    source_gate={'code':exc.code,'detail':str(exc)}
else:raise AssertionError('changed business source unexpectedly accepted')
old_backup=next(r for r in context['version_vector']['source_files'] if r['path']=='internal/domain/backup.go')
new_backup=ref(REPO/old_backup['path']);assert old_backup['sha256']!=new_backup['sha256']
formal=read(ADOPT/'formal-after-adoption.stdout.json')
invocation=read(ADOPT/'formal-after-adoption.invocation.json')
assert ref(ADOPT/'formal-after-adoption.stdout.json')['sha256']==invocation['stdout_sha256']
assert hashlib.sha256((ADOPT/'formal-after-adoption.stderr.raw').read_bytes()).hexdigest()==invocation['stderr_sha256']
assert formal['integrity']=='PARTIAL' and formal['formal_cases_accepted']==0 and formal['required_formal_cases']==42
assert invocation['exit_code']==1
formal_recheck=index['recheck_inputs'](formal['dependency_snapshot']);assert formal_recheck=={'status':'PASS'}
w09=[r for r in formal['cases'] if r.get('final_owner_task')=='W09']
assert len(w09)==2 and all(r['status']=='NEEDS_REVALIDATION' and 'internal/domain/backup.go' in str(r['reasons']) for r in w09)
result={'schema':'researchos.w09.header-correction-post-adoption-review.v1',
 'reviewer_id':'/root/w09_header_gate_review','issued_at':datetime.now(timezone.utc).isoformat(),
 'decision':'SOURCE_COMPATIBILITY_ADOPTION_VERIFIED','scope':'INTERPRETER_RECOVERY_ONLY',
 'checkpoint_revision':checkpoint['revision'],'certificate_ref':authority['certificate_ref'],
 'source_review_ref':authority['review_ref'],'installed_profile_ref':adoption['installed_profile_ref'],
 'installed_helper_ref':adoption['helper_ref'],'actual_delivery_message_id':message['payload']['id'],
 'actual_delivery_offsets':capture['source_line_offsets'],'actual_delivery_ordinals':[0,561,562],
 'positive_authorize':'PASS','authorization_audit_ranges':21,'authorization_inputs_recheck':recheck,
 'next_business_gate':source_gate,'old_backup_pin':old_backup,'actual_backup_ref':new_backup,
 'formal_integrity':formal['integrity'],'formal_cases_accepted':0,'required_formal_cases':42,
 'formal_inputs_recheck':formal_recheck,'formal_snapshot_audit_ranges':len(formal['dependency_snapshot'].get('audit_ranges',[])),
 'formal_snapshot_limit':'Partial verification stopped before verify_owner publishes its audit ranges; the separate positive authorization snapshot above rechecks all21 actual ranges.',
 'native_or_consumer_calls':False,'canon_writes':False,'formal_acceptance_issued':False,
 'evidence_refs':[ref(p) for p in [ADOPT/'adoption.json',ADOPT/'actual-review-delivery.json',ADOPT/'formal-after-adoption.invocation.json',ADOPT/'formal-after-adoption.stdout.json',OUT/'post-adoption-authorization-snapshot.json',OUT/'post_adoption_check.py']]}
target=OUT/'post-adoption-review.json';assert not target.exists()
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':result['decision'],'review_ref':ref(target),'positive_authorize':'PASS','audit_ranges':21,'recheck':recheck,'source_gate':source_gate,'old_backup_sha256':old_backup['sha256'],'new_backup_sha256':new_backup['sha256'],'formal':'PARTIAL 0/42','formal_recheck':formal_recheck},ensure_ascii=False,indent=2))
