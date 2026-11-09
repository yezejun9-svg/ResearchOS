from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
V=B/'official_test2json_resource_independent_review_codex/fd737b147f004cb4be2e57a0f85d9c4e'
Q=B/'integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 with (V/name).open('x',encoding='utf-8',newline='') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for dest,src in [('read-review.py','w0599_tool_review.py'),('verify.py','w0599_tool_verify.py'),('seal.py','w0599_tool_seal.py')]:
 with (V/dest).open('x',encoding='utf-8',newline='') as f:f.write((Path('C:/Users/yqyyds/AppData/Local/Temp')/src).read_text(encoding='utf-8'))
checks=json.loads((V/'checks.json').read_text(encoding='utf-8'))
refs=json.loads((V/'input-refs.json').read_text(encoding='utf-8'))
drift=[r for r in refs if pin(Path(r['path']))!=r]
h={'version':'INDEPENDENT_RESOURCE_REVIEW_V1','reviewer':'/root/typed_fixture_source_review','verdict':'APPROVE','status':'ACCEPTED_TOOL_COMPILATION_COMPONENT_ONLY','scope':'TOOL_COMPILATION_COMPONENT','formal_acceptance':False,'authority':'NONE','Main_adopted':False,'review_namespace':V.as_posix(),'actual_closed':pin(Q/'resource-build.closed.json'),'binary':checks['binary'],'input_refs':pin(V/'input-refs.json'),'actual_original_public_IO':pin(Q/'original-tool-io.json'),'review_public_IO':pin(V/'tool-io.json'),'report':pin(V/'report.md'),'checks':pin(V/'checks.json'),'input_count':len(refs),'final_input_drift':drift,'target_binary_executed':False,'product_tests_accepted':False,'source_Q2_reviewed':False,'actual_jobs_reviewed':2,'selected_source_inputs':759,'packages':102,'new_mechanical_failures':[],'protected_paths_written':[],'all_input_refs':refs,'limits':checks['limitations'],'next_use':'Fresh Root hash/guard of exact reporter required; no ongoing guard implied','global_status':'FULL FAILED 1261/25/4 unchanged; no governance or Goal state changes'}
write('HDF.json',h)
members=[pin(p) for p in sorted(V.iterdir()) if p.is_file()]
write('MF.json',{'version':'IMMUTABLE_INDEPENDENT_RESOURCE_REVIEW_V1','status':h['status'],'members':members,'self_hash_excluded':['MF.json'],'postseal_io_excluded':['seal-tool-io.json'],'formal_acceptance':False})
print(json.dumps({'HDF':pin(V/'HDF.json'),'MF':pin(V/'MF.json'),'report':pin(V/'report.md'),'input_drift':drift,'member_count':len(members),'STOP':True},ensure_ascii=False))
