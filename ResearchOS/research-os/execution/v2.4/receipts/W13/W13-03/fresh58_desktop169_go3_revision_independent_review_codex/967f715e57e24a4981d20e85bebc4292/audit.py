import ast, hashlib, json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
P=ROOT/'execution/v2.4/receipts/W13/W13-03'
N=P/'fresh58_desktop169_go3_revision_preparation_codex/736e757cdbc148a286c1d2426b8a7382'
OUT=Path(__file__).parent
checks=[]; inputs={}
def check(label, value): checks.append({'check':label,'passed':bool(value)})
def ref(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def pin(r):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
    a=ref(p);check('pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);inputs[str(p)]=a
    return p.read_bytes()
def doc(p):
    p=Path(p);inputs[str(p)]=ref(p);return json.loads(p.read_bytes())
def save(name,v):
    with (OUT/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

mf=doc(N/'manifest.json');check('new manifest count',mf['count']==len(mf['entries'])==24)
for r in mf['entries']:pin(r)
h=doc(N/'handoff.json')
check('handoff supplied hash',ref(N/'handoff.json')['sha256']=='33b4430e1105e5a0f4eb4e93f6fcd2057ad9159bd43d3728c406741650a4cd64')
check('manifest supplied hash',ref(N/'manifest.json')['sha256']=='2c40d46acb8e8d65c37c2911e65e428f75d61708531ba5d81ab67fb2b1788469')
def allrefs(v):
    if isinstance(v,dict):
        if {'path','sha256','bytes'}<=v.keys():yield v
        else:
            for x in v.values():yield from allrefs(x)
    elif isinstance(v,list):
        for x in v:yield from allrefs(x)
for r in allrefs(h):pin(r)
idx=doc(N/'inverse-index.json');inverse=[]
for row in idx['files']:
    old=pin(row['baseline_ref']);new=pin(row['candidate_ref']);back=new
    for e in reversed(row['edits']):
        a=e['new'].encode();b=e['old'].encode();check('inverse occurrence '+Path(row['candidate_ref']['path']).name,back.count(a)==e['occurrences']);back=back.replace(a,b)
    equal=back==old;check('whole byte inverse '+row['candidate_ref']['path'],equal)
    oldtree=ast.parse(old);newtree=ast.parse(new)
    od={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    nd={n.name:n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    for name in row.get('unchanged_definitions_byte_AST',[]):
        check('unchanged AST '+name,ast.dump(od[name],include_attributes=False)==ast.dump(nd[name],include_attributes=False))
        a=old.splitlines(keepends=True);b=new.splitlines(keepends=True)
        check('unchanged bytes '+name,b''.join(a[od[name].lineno-1:od[name].end_lineno])==b''.join(b[nd[name].lineno-1:nd[name].end_lineno]))
    inverse.append({'baseline_ref':row['baseline_ref'],'candidate_ref':row['candidate_ref'],'whole_byte_inverse':equal})
s=doc(N/'scope.v2.proposed.json')
for r in allrefs(s):pin(r)
for key in ['authorization_verifier_ref','source_catalog_ref','resource_catalog_ref','current58_CLI2_qualification_ref','expected_registration','inner_seconds','outer_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']:
    check('future required NULL '+key,s[key] is None)
check('no execution permission',s['execution_authorized'] is False and s['preparation_only'] is True)
check('finite unchanged limits',(s['node_cases'],s['Go_top_cases'],s['native_top_command_cap'],s['loopback_HTTP_max'],s['cleanup_seconds'],s['formal_increment'])==(169,3,176,390,5,0))
for rel in ['tests/ui/desktop/http-wire-boundary.test.mjs','tests/ui/desktop/w13-react.test.js','apps/desktop/tests/w14-native.js','apps/desktop/tests/w14-review.js']:
    docpath=ROOT/rel;inputs[str(docpath)]=ref(docpath)
audit={'schema':'researchos.readonly-static-audit.v1','candidate_execution':False,'checks':checks,'failed':[x for x in checks if not x['passed']],'inverse':inverse,'input_refs':list(inputs.values()),'method':'JSON/hash/AST only; no candidate import, compilation or execution'}
save('audit.json',audit)
print(json.dumps({'checks':len(checks),'failed':audit['failed'],'audit_ref':ref(OUT/'audit.json')},ensure_ascii=False))
