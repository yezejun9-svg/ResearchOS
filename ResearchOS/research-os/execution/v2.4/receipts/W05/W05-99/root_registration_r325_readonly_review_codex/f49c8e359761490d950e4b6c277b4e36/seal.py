import json,hashlib
from pathlib import Path
O=Path(__file__).parent
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
review=json.loads((O/'review.json').read_bytes())
save('audit.invocation.known-fields.json',{'tool_chunk_id':'baed11','tool_exit_code':0,'separately_captured_native_exit':None,'original_native_stream_file':None,'known_stdout':{'review_ref':ref(O/'review.json'),'checks':24973,'failed_checks':[],'direct_read_files':289,'prepared_verified_refs':24018,'runtime_observed':187},'boundary':'Only own readonly auditor ran; these are known tool fields, not independent native stream capture. Catalogue member declarations compared without repeated full resource tree hashing.','actual_target_execution':False,'new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.readonly-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':review['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'invocation_known_fields_ref':ref(O/'audit.invocation.known-fields.json'),'copied_canonical_before_refs':review['copied_canonical_before_refs'],'expected_before':review['expected_before'],'expected_after':review['expected_after'],'register_sha256':review['register_sha256'],'wrapper_sha256':review['wrapper_sha256'],'prepared_refs_sha256':review['prepared_refs_sha256'],'audit_sha256':review['audit_sha256'],'sealer_ref':review['sealer_ref'],'later_pending_origin_refs':review['later_pending_origin_refs'],'new_failure_origins':[],'actual_registration_executed':False,'source_acceptance':False,'formal_increment':0,'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
