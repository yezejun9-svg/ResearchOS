import ast, hashlib, json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
before=json.loads((OUT/'inputs.final.json').read_bytes())['entries']
for r in before:
    a=ref(Path(r['path']))
    assert a['sha256']==r['sha256'] and a['bytes']==r['bytes']
for p in OUT.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
for p in (OUT/'tool-observations.json',OUT/'tool-observations.final.json'):
    for item in json.loads(p.read_bytes()):
        assert item['result'] is not None and item['result']['exit_code']==0,item['key']
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
doc={'schema':'researchos.source-preparation-manifest.v1','members':members,'count':len(members),'excluded_only_self':True,'target_executions':0,'candidate_imports':0,'source_acceptance':False,'new_failure_origins':[]}
with (OUT/'manifest.json').open('xb') as f:f.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'manifest':ref(OUT/'manifest.json'),'handoff':ref(OUT/'handoff.json'),'listed_members':len(members),'input_count':len(before),'input_drift':0,'new_failure_origins':0,'STOPPED':True},ensure_ascii=False))
