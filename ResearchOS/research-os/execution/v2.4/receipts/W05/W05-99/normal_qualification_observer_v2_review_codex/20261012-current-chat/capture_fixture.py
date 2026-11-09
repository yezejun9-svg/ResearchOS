import sys
sys.dont_write_bytecode=True
import pathlib, importlib.util, hashlib, json, traceback
out=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/researchos-storage-continuation-cp441-20261012/observer-v2/observe.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='0360de13d900c0787ef5e44cb19f13041bb3622ca1d0faeb1181463a9eca1f64'
spec=importlib.util.spec_from_file_location('frozen_observer',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.PROJECT,m.SESSION,m.OWNER='fixture-project','fixture-session','fixture-owner'
results=[]
for kind in ['blob','text']:
    m.DATABASE=out/('synthetic-'+kind+'.sqlite')
    before=hashlib.sha256(m.DATABASE.read_bytes()).hexdigest()
    try:
        m.observe('fixture-request')
        r={'kind':kind,'result':'unexpected-success'}
    except Exception as e:
        r={'kind':kind,'error':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    r['db_unchanged']=before==hashlib.sha256(m.DATABASE.read_bytes()).hexdigest()
    r['database_override']=str(m.DATABASE)
    results.append(r)
print(json.dumps({'purpose':'capture unchanged counterexamples against existing C-only synthetic fixtures','real_database_accessed':False,'results':results},indent=2))
assert results[0]['error']=='AssertionError' and results[1]['message']=='ORIGINAL_REQUEST_HASH_MISMATCH'
assert all(r['db_unchanged'] for r in results)
