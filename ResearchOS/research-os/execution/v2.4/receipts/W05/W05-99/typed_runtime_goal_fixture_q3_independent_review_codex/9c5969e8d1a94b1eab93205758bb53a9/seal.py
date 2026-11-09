from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
V=B/'typed_runtime_goal_fixture_q3_independent_review_codex/9c5969e8d1a94b1eab93205758bb53a9';Q=B/'typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for dest,src in [('read.py','w0599_q3_read.py'),('verify.py','w0599_q3_verify.py'),('seal.py','w0599_q3_seal.py')]:
 with (V/dest).open('x',encoding='utf-8',newline='') as f:f.write((Path('C:/Users/yqyyds/AppData/Local/Temp')/src).read_text(encoding='utf-8'))
refs=json.loads((V/'input-refs.json').read_text(encoding='utf-8'));drift=[r for r in refs if pin(Path(r['path']))!=r];checks=json.loads((V/'checks.json').read_text(encoding='utf-8'))
h={'version':'INDEPENDENT_MINIMAL_SOURCE_REVIEW_V1','reviewer':'/root/typed_fixture_source_review','verdict':'APPROVE','status':'APPROVE_SOURCE_COMPONENT_ONLY_FOR_ROOT_FRESH_INTEGRATION','scope':'SOURCE_COMPONENT_ONLY','source_namespace':Q.as_posix(),'review_namespace':V.as_posix(),'source_HDF':pin(Q/'HDF.json'),'source_MF':pin(Q/'MF.json'),'report':pin(V/'report.md'),'checks':pin(V/'checks.json'),'input_refs':pin(V/'input-refs.json'),'public_tool_IO':pin(V/'tool-io.json'),'all_input_refs':refs,'final_input_drift':drift,'source_findings_closed':checks['prior_findings'],'critical_findings':[],'important_findings':[],'Root_fresh_T6_source_readiness':True,'Root_adoption_and_actual_decision_pending':True,'formal_acceptance':False,'authority':'NONE','Main_adopted':False,'Go_AST_compile_test_native_SQL_model_executed':False,'target_10_leaves_accepted':False,'actual_parent_child_and_all_Job_descendant_closure':'PENDING_ROOT_ACTUAL','tool_compilation_component_only':True,'new_mechanical_failures':[],'failure_counter_reset':False,'protected_paths_written':[],'prior_errors_and_reviews_preserved':True,'original_FULL':'1261PASS25FAIL4SKIP FAILED unchanged'}
write('HDF.json',h);members=[pin(p) for p in sorted(V.iterdir()) if p.is_file()]
write('MF.json',{'version':'IMMUTABLE_INDEPENDENT_SOURCE_REVIEW_V1','status':h['status'],'members':members,'self_hash_excluded':['MF.json'],'postseal_IO_excluded':['seal-tool-io.json'],'formal_acceptance':False})
print(json.dumps({'HDF':pin(V/'HDF.json'),'MF':pin(V/'MF.json'),'report':pin(V/'report.md'),'input_drift':drift,'STOP':True},ensure_ascii=False))
