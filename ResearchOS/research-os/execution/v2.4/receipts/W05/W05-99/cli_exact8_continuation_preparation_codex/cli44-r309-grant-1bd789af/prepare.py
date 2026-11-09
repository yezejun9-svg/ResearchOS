"""Immutable v4 grant-input amendment; no runner import, compiler, SQL or test."""
from pathlib import Path
import ast
import hashlib
import json

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'cli44-r309-c927f880'
def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
    with (HERE/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def rep(body,old,new):
    if body.count(old)!=1:raise RuntimeError('replacement count '+old[:80])
    return body.replace(old,new,1)
oldm=json.loads((OLD/'manifest.v3.json').read_bytes())
for row in oldm['entries']:
    if ref(OLD/row['path'])['sha256']!=row['sha256']:raise RuntimeError('oldv3 drift')
for name in ('reused7718.current.json','uri65.current.json','finite_selectors.v3.json','reused_provenance.json'):
    with (HERE/name).open('xb') as f:f.write((OLD/name).read_bytes())
body=(OLD/'runner.v3.py').read_text(encoding='utf-8')
body=rep(body,'_KNOWN_INPUTS = set()','_KNOWN_INPUTS = set()\n_AUTHORIZED_SCOPE_INPUT = None')
body=rep(body,'def authorize(args):\n','def authorize(args):\n    global _AUTHORIZED_SCOPE_INPUT\n')
body=rep(body,'raw = Path(args.scope).read_bytes()','scope_path = Path(args.scope).resolve()\n    raw = scope_path.read_bytes()')
body=rep(body,'scope = json.loads(raw)','_AUTHORIZED_SCOPE_INPUT = {"path": str(scope_path), "sha256": sha(raw), "bytes": len(raw)}\n    _KNOWN_INPUTS.add(scope_path)\n    scope = json.loads(raw)')
body=rep(body,'manifest = HERE / "manifest.v3.json"','manifest = HERE / "manifest.v4.json"')
body=rep(body,'grant["prepared_manifest_v3_sha256"]','grant["prepared_manifest_v4_sha256"]')
body=rep(body,'return {"scope": file_ref(args.scope), "grant": grant}','return {"scope": dict(_AUTHORIZED_SCOPE_INPUT), "grant": grant}')
body=rep(body,'def freeze_reused_inputs():\n','def freeze_reused_inputs():\n    require(_AUTHORIZED_SCOPE_INPUT is not None, "ROOT_SCOPE_INPUT_MISSING")\n    require(file_ref(_AUTHORIZED_SCOPE_INPUT["path"]) == _AUTHORIZED_SCOPE_INPUT, "ROOT_SCOPE_INPUT_CHANGED")\n')
body=rep(body,'paths = [x["path"] for x in original] + [x["path"] for x in current_runtime]',
 'paths = [x["path"] for x in original] + [x["path"] for x in current_runtime] + [_AUTHORIZED_SCOPE_INPUT["path"]]')
ast.parse(body)
with (HERE/'runner.v4.py').open('xb') as f:f.write(body.encode('utf-8'))
spec=json.loads((OLD/'prepared_execution_spec.v3.json').read_bytes())
spec['decision']='CLI44_V4_ROOT_GRANT_INPUT_FROZEN_PREPARED_NOT_EXECUTED'
spec['runner']=ref(HERE/'runner.v4.py')
grant=spec['root_grant']['cli44_continuation']
del grant['prepared_manifest_v3_sha256']
grant['prepared_manifest_v4_sha256']='<actual manifest.v4 SHA; Root grant is external and frozen after authorization, no SHA cycle>'
for key,name in [('selectors','finite_selectors.v3.json'),('reused_provenance','reused_provenance.json'),('current_original_input_check','reused7718.current.json'),('uri_runtime_pins','uri65.current.json')]:spec[key]=ref(HERE/name)
spec['launch']=[x.replace(str(OLD/'runner.v3.py'),str(HERE/'runner.v4.py')) for x in spec['launch']]
spec['minimal_v4_amendment']={'original_v3_handoff':ref(OLD/'handoff.v3.json'),
 'change':'Exact actual authorized Root scope raw SHA+bytes+resolved path are tracked immediately, rechecked before freeze, included in full per-case before/native-after/fixture-after/current vectors.',
 'unchanged':'Same44/145 roster bytes, same candidate8, original7718 proof, same reused executables, original76 and one controller-failure history; no rehash/recompile/retest in preparation.',
 'source_or_product_change':False}
save('prepared_execution_spec.v4.json',spec)
save('static_audit.v4.json',{'decision':'AST_VALID_GRANT_IN_FULLVECTOR_PREPARED_ONLY',
 'runner':ref(HERE/'runner.v4.py'),'old_v3_runner':ref(OLD/'runner.v3.py'),
 'old_manifest':ref(OLD/'manifest.v3.json'),'old_manifest_all_members_unchanged':True,
 'roster_identical':(OLD/'finite_selectors.v3.json').read_bytes()==(HERE/'finite_selectors.v3.json').read_bytes(),
 'grant_verified_from_same_raw_bytes_as_authorization':True,
 'grant_path_and_hash_tracked_before_any_output_or_child':True,
 'grant_rechecked_before_first_freeze_and_every_case_phase':True,
 'helper_import_compile_case_count':0})
entries=[]
for p in sorted(HERE.iterdir()):
    if p.is_file():
        x=ref(p);x['path']=p.name;entries.append(x)
save('manifest.v4.json',{'schema':'researchos.prepared-runner-manifest.v4','entries':entries,'count':len(entries),'self_excluded':True,'handoff_excluded':True,'external_helper':grant['owned_process_helper_ref']})
save('handoff.v4.json',{'decision':spec['decision'],'runner':ref(HERE/'runner.v4.py'),
 'manifest':ref(HERE/'manifest.v4.json'),'spec':ref(HERE/'prepared_execution_spec.v4.json'),
 'roster':ref(HERE/'finite_selectors.v3.json'),'audit':ref(HERE/'static_audit.v4.json'),
 'original_v3':ref(OLD/'handoff.v3.json'),'case_count':0,'compile_count':0,
 'source_acceptance':False,'new_failure_origins':[]})
print(json.dumps({n:ref(HERE/n) for n in ('runner.v4.py','manifest.v4.json','prepared_execution_spec.v4.json','handoff.v4.json')},ensure_ascii=False))
