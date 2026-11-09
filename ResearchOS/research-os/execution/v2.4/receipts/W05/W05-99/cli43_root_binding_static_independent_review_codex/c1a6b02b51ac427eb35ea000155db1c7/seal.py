import json,hashlib
from pathlib import Path
O=Path(__file__).parent
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
save('audit.invocation.known-fields.json',{'tool_chunk_id':'990888','tool_exit_code':0,'separately_captured_native_exit':None,'original_native_raw_file':None,'known_stdout_json':{'review_ref':ref(O/'review.json'),'checks':273,'failed_checks':[],'input_files':79,'target_execution':False},'provenance':'Known tool result fields; not an independently captured native stream. Only own static auditor ran.','new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.readonly-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':'PREPARATION_STATIC_REVIEWED_WITH_FUTURE_ROOT_BINDING_REQUIRED','review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'source_extracts_ref':ref(O/'source-extracts.json'),'invocation_ref':ref(O/'audit.invocation.known-fields.json'),'finding_closed':'CLI43-BS-OBS-02','candidate_templates_executed':0,'actual_registration_executed':False,'new_failure_origins':[],'remaining':'New actual Root scope and runtime catalogue must pin staged v7 code; exact ROOT-relative scope ref, independent actual registration review/CAS/seal and unique grant remain required. No product/source/formal acceptance.','status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False))
