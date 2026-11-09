from pathlib import Path
import json,hashlib
v=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd')
def pin(p):
    b=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
    with (v/name).open('x',encoding='utf-8',newline='') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
refs=json.loads((v/'input-refs.json').read_text(encoding='utf-8'))
drift=[r for r in refs if pin(Path(r['path']))!=r]
for name,src in [('supplement-check.py','w0599_review_supplement.py'),('recovery815.py','w0599_review_recover815.py'),('seal.py','w0599_review_seal.py')]:
    with (v/name).open('x',encoding='utf-8',newline='') as f: f.write((Path('C:/Users/yqyyds/AppData/Local/Temp')/src).read_text(encoding='utf-8'))
h={'version':'INDEPENDENT_SOURCE_REVIEW_V1','status':'SOURCE_COMPONENT_NOT_ACCEPTED','verdict':'REQUEST_CHANGES','reviewer':'/root/typed_fixture_source_review','source_namespace':'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931','review_namespace':v.as_posix(),'scope':'SOURCE_COMPONENT_ONLY','formal_acceptance':False,'authority':'NONE','Main_adopted':False,'blocking_finding':'Missing strict actual child expected-leaf JSONL; text substring markers insufficient','required_revision':'Fresh Source namespace using Root-pinned RESEARCHOS_GO tool test2json exact compiled child and strict event validation; Root parent/descendant/lease closure remains pending','input_refs':pin(v/'input-refs.json'),'report':pin(v/'report.md'),'checks':pin(v/'checks.json'),'if_supplement':pin(v/'if-node-supplement.json'),'original_public_io_refs':[r for r in refs if 'tool-io' in r['path'] or 'source_io_codex' in r['path']],'review_execution_io':pin(v/'tool-io.json'),'new_mechanical_failure':pin(v/'failure-origin.815.json'),'failure_counter_reset':False,'rechecked_input_drift':drift,'original_full_test_totals':{'pass':1261,'fail':25,'skip':4},'original_full_status':'FAILED_UNCHANGED','execution':{'Go':0,'gofmt':0,'native':0,'SQL':0,'model':0,'DPAPI':0,'Owner':0},'all_refs':refs,'protected_paths_written':[],'global_state':'Root-reported CP356 OW168 SS CM unchanged; 6/22 historical and 0/42 current; GoalActive; not independently rerun'}
write('HDF.json',h)
members=[pin(p) for p in sorted(v.iterdir()) if p.is_file()]
write('MF.json',{'version':'IMMUTABLE_INDEPENDENT_REVIEW_MANIFEST_V1','status':'SEALED_SOURCE_COMPONENT_NOT_ACCEPTED','namespace':v.as_posix(),'formal_acceptance':False,'members':members,'self_hash_excluded':['MF.json'],'postseal_io_excluded':['seal-tool-io.json']})
print(json.dumps({'HDF':pin(v/'HDF.json'),'MF':pin(v/'MF.json'),'report':pin(v/'report.md'),'input_drift':drift,'member_count':len(members),'status':h['status'],'STOP':True},ensure_ascii=False))
