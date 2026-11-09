"""Pure IO final sealing; no candidate loading or execution."""
from pathlib import Path
import ast,hashlib,json
OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,v):
    with (OUT/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return ref(OUT/name)
def need(ok,msg):
    if not ok:raise ValueError(msg)
mf=json.loads((OUT/'manifest.json').read_bytes())
for row in mf['files']:need(ref(Path(row['path']))==row,'SEALED_MEMBER_DRIFT')
before=json.loads((OUT/'inputs.before.json').read_bytes())
need([ref(Path(row['path'])) for row in before]==before,'ORIGINAL_INPUT_DRIFT')
for name in ['construct.py','seal-preparation.py','finalize.py','driver18_root_producer.v3.proposed.py']:ast.parse((OUT/name).read_bytes())
tool=save('sealing-tool-observation.json',{'schema':'researchos.readonly-tool-observation.v1','original_tool_return':{'chunk_id':'ac0bdc','wall_time_seconds':0.7072207,'exit_code':0,'original_token_count':247,'output_summary':{'source_sha256':'5a4e421c7fe8c40c65bc6de8d90f904258f1d676440ed9a71f4c7682fc958310','source_bytes':52634,'handoff_sha256':'732edb65ab50c4fd72c3e56a9416ba8b6c571d11fdc05fc22952b03569ab64c8','manifest_sha256':'91d36171f496fbca5644b4e6a4a5779c9843d7641fef321892ee871d460dc851','members':17,'new_origins':0}},'output_summary_is_not_verbatim_stdout':True,'actual_outer_exit':0,'actual_native_exit':None,'native_not_separately_sampled':True,'candidate_execution':False,'command':"& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 '"+str(OUT/'seal-preparation.py')+"'"})
handoff=save('handoff.complete.json',{'schema':'researchos.source-preparation-handoff.complete.v1','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','handoff_ref':ref(OUT/'handoff.json'),'initial_manifest_ref':ref(OUT/'manifest.json'),'source_ref':ref(OUT/'driver18_root_producer.v3.proposed.py'),'review_request_ref':before[1],'final_sealing_observation_ref':tool,'original_input_count':len(before),'original_input_drift':0,'original_sealed_members_verified':len(mf['files']),'AST_parsed_only':True,'candidate_imported_or_executed':False,'all_future_controls':'NOT_RUN','new_failure_origins':[],'actual_native_exit':None,'source_acceptance':False,'Root_CAS_or_grant_executed':False,'writer_status':'STOPPED','next_step':'Different-author full v3/source-layout/capture-closure review, then separate Root actual inputs/scope/CAS/grant; no future tuple inferred.'})
rows=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.complete.json']
manifest=save('manifest.complete.json',{'schema':'researchos.immutable-source-preparation-manifest.complete.v1','files':rows,'member_count':len(rows),'excluded_only_self':True,'old_manifest_not_overwritten':True})
print(json.dumps({'handoff':handoff,'manifest':manifest,'members':len(rows),'input_drift':0,'new_origins':0},ensure_ascii=False))
