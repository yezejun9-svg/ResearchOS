import hashlib
import json
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
B=Path(__file__).parent
S=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_source_codex/20261015-current-chat'
P=S/'candidate-ab308912-final2/command-index.json'
def ref(p):
    x=p.read_bytes()
    return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
rows=json.loads(P.read_text(encoding='utf8'))
assert len(rows)==146
verified={}
details=[]
for row in rows:
    d=Path(row['directory'])
    assert d.resolve().is_relative_to(S.resolve())
    files={p:ref(p) for p in d.iterdir() if p.is_file()}
    mapping={}
    for field in ['before_sha256','after_sha256','stdout_sha256','stderr_sha256']:
        stem=field.split('_')[0]
        found=[(p,v) for p,v in files.items() if v['sha256']==row[field] and stem in p.name.lower()]
        assert len(found)==1,(field,str(d),[p.name for p in files])
        p,v=found[0]
        mapping[stem]=v
        verified[str(p)]=v
    before=json.loads((R/mapping['before']['path']).read_text(encoding='utf-8-sig'))
    after=json.loads((R/mapping['after']['path']).read_text(encoding='utf-8-sig'))
    assert before['argv']==row['argv'] and before['cwd']==row['cwd']
    native_fields=[k for k in ['native_exit','native_exit_code','exit_code','returncode'] if k in after]
    assert native_fields,(str(d),list(after))
    assert any(after[k]==row['native_exit'] for k in native_fields),(str(d),after,row['native_exit'])
    details.append({'directory':str(d),'native_exit':row['native_exit'],'files':mapping})
o=B/'continuation-cp520/root-r4-command-capture-verification.json'
with o.open('x',encoding='utf8') as f:
    json.dump({'index':ref(P),'captures_verified':len(rows),'files_verified':len(verified),'nonzero_count':sum(x['native_exit']!=0 for x in rows),'details':details,'previous_root_manifest_nested_verifier_only_9_direct_refs':'Supplement closes alternate command-index flattened sha256 layout, no semantic acceptance'},f,ensure_ascii=False,indent=2)
print(json.dumps({'output':ref(o),'captures_verified':len(rows),'files_verified':len(verified),'nonzero_count':sum(x['native_exit']!=0 for x in rows)},ensure_ascii=False))
