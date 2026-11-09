from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c';V=B/'workspace_epoch_fixture_independent_review_codex/4f3906c8c9e6422281cfc0bdb33a488a'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for dest,src in [('read.py','w0599_epoch_read.py'),('verify.py','w0599_epoch_verify.py'),('seal.py','w0599_epoch_seal.py')]:
 with (V/dest).open('x',encoding='utf-8',newline='') as f:f.write((Path('C:/Users/yqyyds/AppData/Local/Temp')/src).read_text(encoding='utf-8'))
refs=json.loads((V/'input-refs.json').read_text(encoding='utf-8'));drift=[r for r in refs if pin(Path(r['path']))!=r]
h={'version':'INDEPENDENT_WORKSPACE_EPOCH_SOURCE_REVIEW_V1','reviewer':'/root/typed_fixture_source_review','verdict':'APPROVE','status':'APPROVE_SOURCE_COMPONENT_ONLY_FOR_ROOT_FRESH_INTEGRATION','scope':'SOURCE_COMPONENT_ONLY','source_namespace':Q.as_posix(),'review_namespace':V.as_posix(),'source_HDF':pin(Q/'HDF.json'),'source_MF':pin(Q/'MF.json'),'source_member':pin(Q/'candidate-root/internal/domain/client_workspace_test.go'),'report':pin(V/'report.md'),'checks':pin(V/'checks.json'),'input_refs':pin(V/'input-refs.json'),'public_tool_IO':pin(V/'tool-io.json'),'all_input_refs':refs,'final_input_drift':drift,'critical_findings':[],'important_findings':[],'Root_adoption_and_actual_pending':True,'formal_acceptance':False,'authority':'NONE','Main_adopted':False,'actual_tests_passed':False,'Go_compile_test_native_SQL_model_executed':False,'fixture_scope':'SYNTHETIC_CURRENT_STATE_MAPPING_NOT_HISTORICAL_HANDOFF','preserved_counts':{'calls':16,'assertion_or_error_if':17,'Test_names':5,'target_calls':7,'target_if':7},'new_mechanical_failures':[],'failure_counter_reset':False,'protected_paths_written':[],'original_FULL':'1261PASS25FAIL4SKIP FAILED unchanged','Root_latest_CP':'357 as parent context, not rewritten or independently reverified'}
write('HDF.json',h);members=[pin(p) for p in sorted(V.iterdir()) if p.is_file()]
write('MF.json',{'version':'IMMUTABLE_INDEPENDENT_SOURCE_REVIEW_V1','status':h['status'],'members':members,'self_hash_excluded':['MF.json'],'postseal_IO_excluded':['seal-tool-io.json'],'formal_acceptance':False})
print(json.dumps({'HDF':pin(V/'HDF.json'),'MF':pin(V/'MF.json'),'report':pin(V/'report.md'),'input_drift':drift,'STOP':True},ensure_ascii=False))
