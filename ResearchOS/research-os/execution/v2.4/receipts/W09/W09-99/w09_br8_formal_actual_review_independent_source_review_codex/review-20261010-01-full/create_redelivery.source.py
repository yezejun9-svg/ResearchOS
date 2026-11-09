from pathlib import Path
import datetime, hashlib, json, types, uuid

R=Path(r'D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
B=R/'execution/v2.4/receipts/W05/W05-99'
D=Path(__file__).resolve().parent
M=B/'public23_to24_handoff_independent_review_codex/review-20261010-01-full'
SUPPORT=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw=SUPPORT.read_bytes()
assert len(raw)==4940 and hashlib.sha256(raw).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('redelivery_support');s.__file__=str(SUPPORT)
exec(compile(raw,str(SUPPORT),'exec'),s.__dict__);s.D=D
frev_refs=[
 s.exact_ref(D/'HDF.json','da74c683dcc58c92253c1e4a43f89513757d7bf3987df779ef70743a03dfaf2c',8073),
 s.exact_ref(D/'MF.json','32c95cc7d465647d0b8214fa35b76d03b81d21d2308c7eb63af7144343241c96',2954),
 s.exact_ref(D/'review-decision.json','212ad90068ed7a11c65062b28a12a5b09fc63534e0f75f341d686211eea2938b',8992),
]
main24_refs=[
 s.exact_ref(M/'HDF.json','e99ce9cb5fb211afe7cb11c9462b6f0b8de293c1fe6649fed7a3fa9fa812824f',9886),
 s.exact_ref(M/'MF.json','7bbb7fac0af1fd133c692e57bdb937a4ee155404080e4bedfeebf702246d694d',2843),
 s.exact_ref(M/'review-decision.json','08c5cc448f4c1ac96b619a0a30438326826bd48dcc787cf93f567c3d6c85f090',11484),
]
assert not (D/'redelivery.json').exists()
g=s.guard()
try:
 g.acquire(frev_refs+main24_refs+[s.pin(Path(__file__)),s.pin(SUPPORT)])
 for ref in frev_refs+main24_refs:
  held=g.get_buffer(ref['path'])
  assert len(held)==ref['bytes'] and hashlib.sha256(held).hexdigest()==ref['sha256']
finally:
 closed=g.close();guard_ref=s.write('redelivery-source-guard.closed.json',closed)
assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['failure'] is None and closed['errors']==[]
redelivery_ref=s.write('redelivery.json',{
 'schema':'researchos.independent-source-review-redelivery.v1',
 'operation':'SOURCE_REVIEW_WITNESS_REDELIVERY',
 'redelivery_id':str(uuid.uuid4()),
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'review_author':'codex:/root/full_w09_source_review',
 'backend_actor_id':'/root/full_w09_source_review',
 'actor_thread_id':'01a1215b-7210-7613-b033-756b9d553b83',
 'root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98',
 'deliveries':[
  {'component':'W09_FREV_V4_SELF_REFERENCE_FIX','review_refs':frev_refs,'verdict':'ACCEPTED_SOURCE_ONLY','source_only':True},
  {'component':'PUBLIC23_TO_DISTINCT_TARGET24_ISOLATED_BACKUP_HANDOFF','review_refs':main24_refs,'verdict':'ACCEPTED_SOURCE_ONLY','source_only':True},
 ],
 'guard_ref':guard_ref,
 'original_Root_capture_failures_retained':[1241,1242],
 'original_reviews_resealed':False,
 'successful_checks_replayed':False,
 'new_actual_final_timestamp_predicted':False,
 'original_metadata_or_logs_modified':False,
 'failure_counter_reset':False,
 'retained_handles_count':0,
 'live_Canon_handles_held':0,
 'new_product_calls':0,
 'Main_Canon_Scope_Registry_writes':0,
 'execution_grant':False,
 'formal_acceptance':False,
 'parent_acceptance':False,
 'STOP':True,
})
print(json.dumps({'redelivery_ref':redelivery_ref,'redelivery_guard_ref':guard_ref,'retained_handles_count':0,'product_calls':0},ensure_ascii=False))
