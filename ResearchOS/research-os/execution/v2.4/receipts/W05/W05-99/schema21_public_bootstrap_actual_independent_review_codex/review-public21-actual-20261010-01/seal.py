import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).parent
def ref(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(n,x):
 p=O/n
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
a=doc(O/'audit-result.json');p1=a['details']['actual_host_call'];p2=a['details']['actual_host_result']
hostresults=[]
for v in p2['output']:
 if v.get('type')=='input_text':
  try:
   d=json.loads(v['text'])
   if isinstance(d,dict) and 'chunk_id' in d:hostresults.append(d)
  except json.JSONDecodeError:pass
assert len(hostresults)==1
h=hostresults[0]
corrections=[
 dict(name='actual_host_call_result_pair',passed=p1['type']=='custom_tool_call' and p2['type']=='custom_tool_call_output' and p1['call_id']==p2['call_id'],reason='Original host uses custom_tool_call/custom_tool_call_output, not function_call/function_call_output. Prior failed predicate preserved.'),
 dict(name='actual_host_success',passed=h['chunk_id']=='9340b0' and h['exit_code']==0 and 'ROOT_ACTUAL_PYTHON_EXIT=0' in h['output'],reason='Original marker is ROOT_ACTUAL_PYTHON_EXIT=0; prior predicate looked for ROOT_PYTHON_EXIT=0. Original raw output retained.')
]
assert all(x['passed'] for x in corrections)
assert {x['name'] for x in a['failed']}=={x['name'] for x in corrections}
pins=doc(O/'source-pins.json');assert all(ref(x['path'])==x for x in pins)
save('host-predicate-qualification.json',dict(original_audit_ref=ref(O/'audit-result.json'),corrections=corrections,actual_outer_exit=h['exit_code'],actual_Python_exit=0,actual_native_exit=0,original_host_output_truncated=True,full_return_file_verified=True))
io=doc(O/'tool-io.json')
failures=[]
for ordinal,chunk,py,cause in [(1162,'2f488e',None,'Reviewer read nonexistent root_scope_ref key; correct key scope_ref.'),(1163,'6c7d13',None,'Reviewer rg used two unobserved nonexistent frozen_source/internal/store paths.'),(1165,'7034b1',1,'Current canonical checkpoint changed concurrently after actual bootstrap; execution-time immutable registration archives used in subsequent distinct audit.')]:
 entry=next(x for x in io if x['result'].get('chunk_id')==chunk)
 assert entry['result']['exit_code']==1
 failure=dict(original_ordinal=ordinal,actor='codex:/root/attach_restore_independent_review',original_input=entry['input'],original_result=entry['result'],actual_outer_exit=1,actual_Python_exit=py,actual_native_exit=None,cause=cause,source_failure=False,automatic_retry=False)
 rr=save('original-'+str(ordinal)+'.json',failure);failures.append(rr)
decision=dict(schema='researchos.schema21-public-bootstrap-actual-independent-review.v1',review_author='codex:/root/attach_restore_independent_review',source_authors=['codex:/root/auth_backup_restore_source','codex:/root/attach_fixture_source_review'],executor='codex:/root',independent_non_author=True,verdict='ACCEPTED_PUBLIC21_BOOTSTRAP_COMPONENT_ONLY',status='PASS_IN_SCOPE',reviewed_case_id='9690cc6324834ded8781ce8a2233fa82',reviewed_return_ref=pins[0],check_count=47,passed_checks=47,findings=[],audit_ref=ref(O/'audit-result.json'),host_qualification_ref=ref(O/'host-predicate-qualification.json'),database_observation_ref=ref(O/'independent-database-observation.json'),source_pins_ref=ref(O/'source-pins.json'),source_guard_close_ref=ref(O/'reviewer-source-guard-close.json'),original_mechanical_failures=failures,actual_outer_exit=0,actual_Python_exit=0,actual_native_exit=0,native_identity=a['details']['identity'],qualification_age_seconds_at_entry=a['details']['qualification_age_seconds_at_entry'],current4_verified_against_execution_time_archives=True,private_owner_existence_only=True,private_owner_read_hash_copy=False,native_rerun=False,static_505_43_controls_rerun=False,ledger_checksum_claim='schema_migrations contains version/applied_at only; frozen migration SQL references pinned separately; no stored migration checksums claimed',formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,programme_qualification_issued=False,execution_grant=False,backup_restore_executed=False,full20to24='OPEN',remaining='Genuine old21 public bootstrap component accepted only. Subsequent Backup/restore/upgrade requires its separate reviewed Root registration.',stop=True)
dr=save('actual-decision.json',decision)
hdf=dict(schema='researchos.independent-review-handoff.v1',author=decision['review_author'],verdict=decision['verdict'],decision_ref=dr,evidence_refs=[ref(O/n) for n in ['audit-result.json','host-predicate-qualification.json','independent-database-observation.json','source-pins.json','reviewer-source-guard-close.json','tool-io.json']],original_failure_refs=failures,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,full20to24='OPEN',STOP=True)
hr=save('HDF.json',hdf)
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mr=save('MF.json',dict(schema='researchos.manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json'],source_pins_ref=ref(O/'source-pins.json')))
print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,files=len(members),pins=len(pins),verdict=decision['verdict'],failure_refs=failures),ensure_ascii=False))

