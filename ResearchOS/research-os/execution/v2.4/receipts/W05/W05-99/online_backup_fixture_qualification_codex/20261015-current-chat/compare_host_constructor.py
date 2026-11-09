import json
from pathlib import Path
e=Path(__file__).resolve().parent
def read(part):return json.loads((e/('q02-repeat-host-'+part+'.stdout.raw')).read_text(encoding='utf-8'))
db0,db1=read('db-before'),read('db-after')
f0,f1=read('files-before'),read('files-after')
names=sorted(set(f0['entries'])|set(f1['entries']))
changed={n:{'before':f0['entries'].get(n),'after':f1['entries'].get(n)} for n in names if f0['entries'].get(n)!=f1['entries'].get(n)}
a0=(e/'q02-repeat-host-acl-before.stdout.raw').read_bytes()
a1=(e/'q02-repeat-host-acl-after.stdout.raw').read_bytes()
out={'all_tables_equal':db0['tables']==db1['tables'],'schema_equal':db0['schema_sha256']==db1['schema_sha256'],
     'file_differences':changed,'acl_snapshot_equal':a0==a1}
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(',',':')))
