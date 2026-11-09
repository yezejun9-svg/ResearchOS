from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
V=B/'typed_runtime_goal_fixture_jsonl_independent_review_codex/715d9054a9ee4de4a201bd86b1438ed38';Q=B/'typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for dest,src in [('read.py','w0599_q2_read.py'),('verify.py','w0599_q2_verify.py'),('seal.py','w0599_q2_seal.py')]:
 with (V/dest).open('x',encoding='utf-8',newline='') as f:f.write((Path('C:/Users/yqyyds/AppData/Local/Temp')/src).read_text(encoding='utf-8'))
refs=json.loads((V/'input-refs.json').read_text(encoding='utf-8'));drift=[r for r in refs if pin(Path(r['path']))!=r]
h={'version':'INDEPENDENT_SOURCE_REVISION_REVIEW_V1','reviewer':'/root/typed_fixture_source_review','verdict':'REQUEST_CHANGES','status':'SOURCE_COMPONENT_NOT_ACCEPTED','scope':'SOURCE_COMPONENT_ONLY','source_namespace':Q.as_posix(),'review_namespace':V.as_posix(),'source_HDF':pin(Q/'HDF.json'),'source_MF':pin(Q/'MF.json'),'report':pin(V/'report.md'),'checks':pin(V/'checks.json'),'input_refs':pin(V/'input-refs.json'),'public_tool_IO':pin(V/'tool-io.json'),'all_input_refs':refs,'final_input_drift':drift,'blocking_findings':[{'id':'Q2-DIGEST-FORMAT','severity':'Critical','line':267,'description':'Domain Digest returns sha256:hex, compared to bare64hex expected resource pin; exact Go resource rejected at first check.'},{'id':'Q2-OFFICIAL-OUTPUTTYPE','severity':'Important','line':129,'description':'Pinned official Go1.27.1 normal framing output includes OutputType=frame; decoder rejects unknown field.'}],'prior_CHILD_JSONL_finding_closed':False,'prior_4396_review_preserved':True,'new_mechanical_failures':[],'failure_counter_reset':False,'formal_acceptance':False,'authority':'NONE','Main_adopted':False,'Go_compile_test_native_SQL_model_executed':False,'target_10_leaves_accepted':False,'protected_paths_written':[],'tool_component_acceptance':'Prior TOOL_COMPILATION_COMPONENT acceptance retained; binary not executed','required_next_step':'Fresh Source namespace minimal two fixes, then independent Source review before Root fresh integration/actual','original_FULL':'1261PASS25FAIL4SKIP FAILED unchanged'}
write('HDF.json',h);members=[pin(p) for p in sorted(V.iterdir()) if p.is_file()]
write('MF.json',{'version':'IMMUTABLE_INDEPENDENT_SOURCE_REVIEW_V1','status':h['status'],'members':members,'self_hash_excluded':['MF.json'],'postseal_io_excluded':['seal-tool-io.json'],'formal_acceptance':False})
print(json.dumps({'HDF':pin(V/'HDF.json'),'MF':pin(V/'MF.json'),'report':pin(V/'report.md'),'input_drift':drift,'STOP':True},ensure_ascii=False))
