import sys
sys.dont_write_bytecode = True
import pathlib, hashlib, json
OWN = pathlib.Path(__file__).resolve().parent
def ref(path):
    raw = path.read_bytes()
    return {'path':path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
if len(sys.argv)!=4:raise ValueError('need actual prepare tool chunk, observed outer exit, observed native exit')
chunk,outer,native=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
write(OWN/'tool-diagnostics.json',{'schema':'researchos.f08-v3-tool-diagnostics.v1','prepare_chunk':chunk,'prepare_observed_tool_exit':outer,'prepare_observed_Python_exit':native,'audit_chunk':'a8292c','audit_observed_tool_exit':0,'audit_observed_Python_exit':0,'explicit_native_exit_bridge':True,'Python_flags':['-I','-S','-X','utf8'],'dont_write_bytecode':True,'prior_failed_read':{'chunk':'17042a','observed_tool_exit':1,'observed_native_exit':None,'same_input_retried':False},'successful_read_only_chunks':['b7d579','b91755','054eb0','43c93a','e946a4','6d169c','a911d5','3db44d','d84606','51a23d','8d8159','922ac6','ea516f','2626b8','e69fe8','6b3187','6f4a26'],'successful_read_only_observed_tool_exit':0,'successful_read_only_observed_native_exit':None,'successful_creation_chunk':'fbc971','candidate_code_executed':False,'Go_AST_compile_gofmt_SQL_SDK_Node_HTTP_model_runs':0,'this_seal_execution_result':'reported by actual external terminal output, not anticipated in this file'})
handoff_path=OWN/'handoff.json'
h=json.loads(handoff_path.read_bytes());h['tool_diagnostics_ref']=ref(OWN/'tool-diagnostics.json');h['manifest_self_excluded']=True
write(handoff_path,h)
files=[ref(p) for p in sorted(OWN.rglob('*')) if p.is_file() and p.name!='manifest.json']
manifest=OWN/'manifest.json';write(manifest,{'schema':'researchos.receipt-manifest.v1','files':files,'member_count':len(files),'self_excluded':True,'candidate_execution':False,'writer_status':'STOPPED'})
for expected in files:
    if ref(pathlib.Path(expected['path']))!=expected:raise ValueError('member reread drift')
inputs=json.loads((OWN/'inputs.after.json').read_bytes())
for expected in inputs['files']:
    if ref(pathlib.Path(expected['path']))!=expected:raise ValueError('original input drift at seal')
print(json.dumps({'handoff_ref':ref(handoff_path),'manifest_ref':ref(manifest),'member_count_excluding_manifest':len(files),'member_count_including_manifest':len(files)+1,'failure_origin_ref':ref(OWN/'failure-origin.17042a.json'),'source_ref':h['source_ref'],'test_ref':h['test_ref'],'all_members_reread_equal':True,'original_inputs_reread_equal':True,'writer_status':'STOPPED'},ensure_ascii=False))
