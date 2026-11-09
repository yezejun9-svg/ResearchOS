import hashlib,json
from pathlib import Path
O=Path(__file__).parent
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
save('audit.invocation.known-fields.json',{'tool_chunk_id':'9db1c1','tool_exit_code':0,'separately_captured_native_exit':None,'original_native_stdout_file':None,'known_stdout_json':{'review_ref':ref(O/'review.json'),'checks':281,'failed_audit_checks':0,'requests':1},'provenance':'Known tool output fields transcribed; not an original complete tool payload or independent native stream. Only own readonly audit was run.','target_execution':False,'new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.readonly-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'compatibility_matrix_ref':ref(O/'compatibility-matrix.json'),'invocation_known_fields_ref':ref(O/'audit.invocation.known-fields.json'),'confirmed_code_blockers':['CLI43-BS-OBS-02'],'minimal_next_revision':'Only after strict module_observation successfully returns, metadata.runtime derives all_observed_inputs_pre_pinned=True before saving. Preserve unknown resource rejection, point-time and lifecycle facts. New immutable module/wrappers/Root bound scope must be reviewed.','full_chain_static_review_completed':True,'actual_target_execution':False,'actual_registration_executed':False,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json','compatibility-matrix.json']},ensure_ascii=False))
