import hashlib,json
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
audit=json.loads((O/'audit.json').read_bytes());draft_raw=(O/'review.json').read_bytes();draft=json.loads(draft_raw)
expected={'check':'scope/binding shared field schema','pass':False}
if audit['failed_checks']!=[expected]:raise RuntimeError('Only the observed schema-comparison diagnostic may be corrected')
if hashlib.sha256(draft_raw).hexdigest()!='993de7510d268998dedc97cdf577238c48c3d1558a461ba81995374bce773ab5':raise RuntimeError('Original draft changed')
scope=json.loads((N/'scope_registration.json').read_bytes());binding=json.loads((N/'binding.pre-review.json').read_bytes())
corrected=[{'check':'scope actual dedicated schema','pass':scope['schema']=='researchos.cli43-fresh-compiler-held2-scope.v2'},{'check':'binding actual dedicated schema','pass':binding['schema']=='researchos.cli43-root-metadata-binding.v1'}]
for row in audit['input_refs']:
 p=Path(row['path']);actual=ref(p)
 corrected.append({'check':'current after-correction stable '+str(p),'pass':actual==row})
prior_checks=[x for x in audit['checks'] if x!=expected]
all_checks=prior_checks+corrected
if any(not x['pass'] for x in all_checks):raise RuntimeError('Corrected schema or current input failed; stop without final review')
save('audit.v2.json',{'schema':'researchos.readonly-audit-correction.v1','original_audit_ref':ref(O/'audit.json'),'original_audit_tool_chunk':'3e8813','original_audit_tool_exit':0,'original_audit_native_separate':None,'original_false_predicate':expected,'correction':'Scope and metadata binding are different fixed schemas, not equal-valued shared fields. Only this auditor predicate is replaced. Other saved checks are reused, not represented as newly run.','checks':all_checks,'failed_checks':[],'reused_checks':len(prior_checks),'new_schema_and_current_checks':len(corrected),'original_review_sha256':hashlib.sha256(draft_raw).hexdigest(),'product_native_execution':False,'new_failure_origins':[]})
old=O/'review.json';retained=O/'review.audit-draft.invalid.json'
if retained.exists() or retained.parent!=O or old.parent!=O:raise RuntimeError('Owned retention guard')
old.rename(retained)
if retained.read_bytes()!=draft_raw:raise RuntimeError('Draft retention mismatch')
draft['decision']='READY_FOR_ROOT_CURRENT43_HELD2_ONCE';draft['requested_changes']=[];draft['audit_ref']=ref(O/'audit.v2.json')
draft['preserved_audit_diagnostic_ref']=ref(retained)
draft['audit_diagnostic']='Original readonly audit exited 0 with one incorrect equality predicate between two different valid schemas. Original code/audit/draft bytes retained; corrected schema checks and current input bytes verified. No new failed native invocation or product failure.'
save('review.json',draft)
save('audit.invocation.known-fields.json',{'tool_chunk_id':'3e8813','tool_exit_code':0,'separately_captured_native_exit':None,'original_review_ref':ref(retained),'checks':385,'failed_checks':[expected],'provenance':'Known tool fields; not original independent native streams. Original audit source and output retained.','target_execution':False,'new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.readonly-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':draft['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.v2.json'),'original_audit_ref':ref(O/'audit.json'),'preserved_audit_draft_ref':ref(retained),'scope_ref':draft['scope_ref'],'scope_invocation_ref':draft['scope_invocation_ref'],'bound_manifest_ref':draft['bound_manifest_ref'],'expected_before':[324,152,430],'expected_after':[325,153,442],'actual_target_execution':False,'actual_registration_executed':False,'new_failure_origins':[],'status':'STOPPED','limitation':'Conditional preparation only; actual independent registration review, CAS, seal and unique grant remain required. No product/source/formal acceptance.'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({n:ref(O/n) for n in ['review.json','manifest.json','handoff.json','audit.v2.json']},ensure_ascii=False))
