import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
def ref(x):
 b=x.read_bytes();return {'path':str(x),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(name,obj):
 with (p/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=True,indent=2)
members={x.name:ref(x) for x in sorted(p.iterdir()) if x.is_file()}
new('MF.json',{'schema':'researchos.source-manifest.v1','members':members})
new('HDF.json',{'schema':'researchos.source-read-failure-handoff.v1','failure_ordinal':798,'formal':False,'execution_authority':False,'source_status':'SEALED_READ_FAILURE_ONLY','manifest_ref':ref(p/'MF.json'),'failure_ref':ref(p/'failure-origin.798.json'),'original_tool_io_ref':ref(p/'original-tool-io.json'),'outer_exit':1,'python_exit':None,'native_exit':None,'production_db_writes':0,'private_reads':False})
print(json.dumps({'HDF':ref(p/'HDF.json'),'MF':ref(p/'MF.json'),'failure_origin':ref(p/'failure-origin.798.json')},ensure_ascii=True))

