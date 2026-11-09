"""Own review only: finite public-ref IO + Python source AST. No candidate imports."""
from pathlib import Path
import ast
import hashlib
import json

OWN = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_adapter_independent_source_review_codex/3a2dfa5a7b9545dbb85c82703e519be7')
AUTHOR = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_binding_preparation_codex/a03c54991b5b44f9bdb6743d8b78b0c9')
def save(name, obj):
    with (OWN/name).open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
def pin(path, raw=None):
    p=Path(path)
    b=p.read_bytes() if raw is None else raw
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
h=json.loads((AUTHOR/'handoff.json').read_bytes())
mf=json.loads((AUTHOR/'manifest.json').read_bytes())
scope=json.loads(Path(h['scope_template_ref']['path']).read_bytes())
before=json.loads(Path(h['inputs_before_ref']['path']).read_bytes())
after=json.loads(Path(h['inputs_after_ref']['path']).read_bytes())
listed=before+mf['members']
listed.append(pin(AUTHOR/'manifest.json'))
for key in ('utility_ref','owned_helper_ref','debug_helper_ref'):
    listed.append(scope[key])
intent_ref=next(r for r in before if Path(r['path']).name=='canonical-write.intent.json')
root_review_ref=json.loads(Path(intent_ref['path']).read_bytes())['review_ref']
listed.append(root_review_ref)
records={}
buffers={}
for expected in listed:
    p=Path(expected['path'])
    raw=p.read_bytes()
    actual=pin(p,raw)
    key=str(p)
    records[key]={'expected_ref':expected,'actual_ref':actual,
                  'matches':expected['sha256']==actual['sha256'] and expected['bytes']==actual['bytes']}
    buffers[key]=raw
save('input-pins.before.json',{'rows':list(records.values()),
    'author_manifest_members':len(mf['members']),
    'named_input_refs':len(before),'after_ref_list_exact':before==after['refs'],
    'backing_catalog_members_rehashed':False,'extra_public_chained_review_ref':root_review_ref})
snapshots=OWN/'snapshots'
snapshots.mkdir()
snapshot_rows=[]
for expected in mf['members']:
    p=Path(expected['path'])
    dst=snapshots/('author.'+p.name+'.txt')
    with dst.open('xb') as f:f.write(buffers[str(p)])
    snapshot_rows.append({'source_ref':expected,'snapshot_ref':pin(dst)})
for key in ('controller_ref','launcher_ref','utility_ref','owned_helper_ref','debug_helper_ref'):
    ref=scope[key]
    p=Path(ref['path'])
    raw=p.read_bytes()
    dst=snapshots/(key+'.txt')
    with dst.open('xb') as f:f.write(raw)
    snapshot_rows.append({'source_ref':ref,'snapshot_ref':pin(dst)})
save('snapshot-map.json',snapshot_rows)
ast_rows=[]
for key in ('authority_adapter_ref','binding_adapter_ref'):
    ref=h[key]
    tree=ast.parse(buffers[str(Path(ref['path']))].decode('utf-8'))
    ast_rows.append({'source_ref':ref,'AST_parse_only':True,
                    'candidate_imported_or_executed':False,
                    'functions':[[n.name,n.lineno,n.end_lineno] for n in tree.body
                                 if isinstance(n,(ast.FunctionDef,ast.ClassDef))]})
save('AST-source-inventory.json',ast_rows)
old_scope=json.loads(Path(before[1]['path']).read_bytes())
inverse=dict(scope)
changed=[k for k in set(old_scope)|set(scope) if old_scope.get(k)!=scope.get(k)]
for k in changed:
    if k in old_scope:inverse[k]=old_scope[k]
    else:inverse.pop(k,None)
save('scope-object-inverse.json',{'actual_changed_keys':sorted(changed),
    'restored_parsed_object_equal':inverse==old_scope,
    'raw_serialization_inverse_not_claimed':True})
final=[]
for key,row in records.items():
    final.append({'initial_ref':row['actual_ref'],'final_ref':pin(key),
                  'same_raw_bytes':Path(key).read_bytes()==buffers[key]})
drift=[r for r in final if not r['same_raw_bytes']]
mismatch=[r for r in records.values() if not r['matches']]
save('input-pins.after.json',{'rows':final,'drift':drift,'initial_mismatches':mismatch})
save('origins.json',{'schema':'researchos.independent-review-origins.v1',
     'new_origins':[],'new_failed_events':0,'old_origins_recounted':False,
     'canonical_failure_counter_written':False})
print(json.dumps({'own':str(OWN),'unique_public_refs_actually_hashed':len(records),
      'author_members':len(mf['members']),'named_refs':len(before),
      'snapshot_count':len(snapshot_rows),'initial_mismatches':len(mismatch),
      'drift':len(drift),'AST_sources':len(ast_rows),'candidate_execution':False,
      'new_failure_origins':0},ensure_ascii=False))

