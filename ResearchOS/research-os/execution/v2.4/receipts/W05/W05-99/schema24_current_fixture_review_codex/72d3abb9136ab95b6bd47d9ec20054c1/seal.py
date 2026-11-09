import pathlib,sys,json,hashlib,datetime
sys.dont_write_bytecode=True
q=pathlib.Path(__file__).resolve().parent
inputs=json.loads((q/'input.json').read_bytes())
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,data):
 p=q/name
 with p.open('xb') as f:f.write((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(p)
sources=[ref(pathlib.Path(inputs['T'])/s) for s in inputs['source_files']]
report={**inputs,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':sources,'report_ref':ref(q/'report.md'),'tool_io_ref':ref(q/'original-tool-io.json'),'running_suite_prefix_snapshot':{'prefix_bytes':1405571,'prefix_sha256':'68dfd029cc615e325a7f84340cc545ddec9f1ca83d8b86777b29aae763cc5d76','final_suite_verdict':None},'conclusions':{'queue_fresh':'current24 expectation/update exact validator; preserve historical22','public_replay':'current24 restore fixed policy; optional separate realNew+exact23 publicfixture to retain historical23','actual_Service_New':'actual24 current correct; only fresh expected version update; explicit22to23 branches unchanged'},'Production_changes_required':False,'tests_run_here':False}
structured=write('report.json',report)
members={name:ref(q/name) for name in ['report.md','original-tool-io.json','input.json','seal.py','report.json']}
manifest=write('manifest.json',{'schema':'researchos.readonly-immutable-receipt-manifest.v1','members':members,'new_mechanical_failures':[],'formal_acceptance':False,'Main_adopted':False})
print(json.dumps({'namespace':str(q),'refs':{**members,'manifest.json':manifest},'source_count':len(sources),'new_mechanical_failures':[]},ensure_ascii=False))
