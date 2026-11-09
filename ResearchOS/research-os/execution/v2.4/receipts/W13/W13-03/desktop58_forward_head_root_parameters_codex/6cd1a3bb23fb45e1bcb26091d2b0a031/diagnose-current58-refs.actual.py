"""Root readonly diagnostic of historical before refs versus current58. No generated request or canonical write."""
import sys
sys.dont_write_bytecode=True
import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
f=json.loads((OUT/'root-facts.partial.json').read_bytes())
basis=json.loads(Path(f['basis_prepared_ref']['path']).read_bytes())
r=json.loads(Path(f['source_closure_review_ref']['path']).read_bytes())
scope=json.loads(Path(r['scope_ref']['path']).read_bytes())
after=json.loads((Path(r['manifest_ref']['path']).parent/'immutable-inputs.after.json').read_bytes())
groups={'basis':basis['immutable_inputs'],'source_after':after}
union=sorted(set(scope['shared38_paths']+scope['cli8_paths']+r['source_paths']))
by_path={}
for label,rows in groups.items():
    assert type(rows) is list
    for row in rows:
        assert type(row) is dict and {'path','sha256','bytes'}<=set(row)
        p=Path(row['path']);p=p if p.is_absolute() else ROOT/p
        by_path.setdefault(str(p.resolve()).casefold(),[]).append({'group':label,'sha256':row['sha256'],'bytes':row['bytes']})
conflicts=[]
for rel in union:
    p=(ROOT/rel).resolve();b=p.read_bytes();actual={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    old=[row for row in by_path.get(str(p).casefold(),[]) if row['sha256']!=actual['sha256'] or row['bytes']!=actual['bytes']]
    if old:conflicts.append({'path':rel,'authorized_source15':rel in r['source_paths'],'actual':actual,'historical':old})
print(json.dumps({'current58_count':len(union),'conflicts':conflicts,'all_conflicts_are_exact15_preimages':all(x['authorized_source15'] for x in conflicts),'writes':0,'native_child_calls':0},ensure_ascii=False))
