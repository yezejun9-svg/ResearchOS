import ast,hashlib,json,difflib,os
from pathlib import Path
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os')
H=Path(__file__).resolve().parent
W=R/'.local/worktrees/codex-w0599-session-list-proof-r312'
P=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V=P/'v2-preparation-48a141cf916944aabe60ea42f6bd6dbe'
OLD=P/'907592b8e03d433da7de947435274481'
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def save(n,x):
 with (H/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
pins={'execute.py':'b0610c0dc587dc138a5282660fe98841ab3cc41f98dc4607eadd2be9f6315782','launch.py':'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e','static_audit.json':'af6860c21dec419dd0e6c237797433b61e988deb1c18e0761567068888996986','manifest.json':'da2d92526ee41ce99db469d67c5a6e53bf28e3f592e5cd9672f4f8654fcfd38e','handoff.json':'84801a82f0ff4a67a54a9f439ce2f544131512b9029ee023528fe26e42d7e6d9'}
for n,d in pins.items():need(sha((V/n).read_bytes())==d,'pin '+n)
manifest=json.loads((V/'manifest.json').read_bytes())
inputs=[]
for row in manifest['files']:
 f=Path(row['path']);b=f.read_bytes();need(sha(b)==row['sha256'] and len(b)==row['bytes'],'manifest '+f.name);inputs.append(ref(f))
audit=json.loads((V/'static_audit.json').read_bytes())
for k in ['v1_driver','v2_driver','old_failure','old_handoff','source_current','domain_current','unchanged_root_assertions']:
 row=audit[k];f=Path(row['path']);b=f.read_bytes();need(sha(b)==row['sha256'] and len(b)==row['bytes'],'auditpin '+k);inputs.append(ref(f))
old=(OLD/'execute.py').read_bytes();new=(V/'execute.py').read_bytes()
need((OLD/'launch.py').read_bytes()==(V/'launch.py').read_bytes(),'launcher unchanged')
normalized=new.replace(b"WORK=W/'.local/closedcopy-v2-48a141cf916944aabe60ea42f6bd6dbe'",b"WORK=W/'.local/closedcopy-907592b8'",1)
start=normalized.index(b' # Check the exact worktree and its .local parent without following aliases.')
end=normalized.index(b" helper=types.ModuleType('owned_helper')",start)
replacement=b" require(not WORK.exists(),'Work already exists; no automatic retry')\n WORK.mkdir();[(WORK/x).mkdir() for x in ['cache','gotmp','temp']]\n"
need(normalized[:start]+replacement+normalized[end:]==old,'exact inverse two changes')
for f in [V/'execute.py',V/'launch.py',V/'root_assertions.original.py']:ast.parse(f.read_bytes(),filename=str(f))
root=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310/list_replay.v2.py'
need(sha(root.read_bytes())=='85e35100bd7ed509883a0ae4729f68aab283032002f8eb8784d28900e97c54ea','Root assertion origin')
def functions(raw):
 lines=raw.splitlines(keepends=True)
 return {n.name:b''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
original_functions=functions(root.read_bytes());copied_functions=functions((V/'root_assertions.original.py').read_bytes())
need(set(copied_functions)=={'typed_cells','canonical_saved_cells','check_closed','check_wire'},'four copied functions')
need(all(copied_functions[k]==original_functions[k] for k in copied_functions),'Root assertions byte preservation')
tree=ast.parse(new)
names=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets))
need(len(names)==14 and len(set(names))==14,'exact14')
origin=json.loads((OLD/'failure_origin.json').read_bytes())
need(origin['actual_driver_exit']==1 and origin['invocations']==[] and origin['completed']==[] and origin['not_run']==names,'old preparation failure preserved')
work=W/'.local/closedcopy-v2-48a141cf916944aabe60ea42f6bd6dbe'
need(not os.path.lexists(work),'new leaf absent')
state={'exact_worktree':str(W),'worktree_resolved':str(W.resolve()),'worktree_is_symlink':W.is_symlink(),'worktree_reparse':bool(getattr(os.lstat(W),'st_file_attributes',0)&0x400),'parent_exists':os.path.lexists(work.parent),'new_leaf_lexists':os.path.lexists(work)}
need(W.resolve()==W.absolute() and not state['worktree_is_symlink'] and not state['worktree_reparse'],'actual worktree path')
SCOPE=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-exact1-r312/scope_registration.json'
need(sha(SCOPE.read_bytes())=='31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c','scope')
inputs += [ref(root),ref(SCOPE),ref(OLD/'launch.py')]+[ref(V/n) for n in ['manifest.json','handoff.json']]
protected=[(Path(x['path']) if Path(x['path']).is_absolute() else R/x['path'],x) for x in inputs]
(H/'copies').mkdir()
for i,f in enumerate([V/'execute.py',V/'launch.py',OLD/'execute.py',OLD/'launch.py',V/'static_audit.json',V/'manifest.json',V/'handoff.json',OLD/'failure_origin.json',OLD/'stopped_handoff.json',V/'root_assertions.original.py',V/'root_assertions.origin.json',V/'source.edited.go',V/'source.before.go',SCOPE]):
 with (H/'copies'/f'{i:02d}-{f.name}').open('xb') as out:out.write(f.read_bytes())
diff=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='pinned-v1',tofile='pinned-v2'))
with (H/'independent.diff').open('xb') as f:f.write(diff.encode())
checks=[
 'Eight manifest entries and all supplied v1/v2/handoff/static/current-source pins match. Exact inverse of only unique WORK leaf and guarded parent creation restores v1 bytes.',
 'Worktree and .local parent/leaf lexical+resolved paths are constrained; symlink/REPARSE_POINT refused; missing parent exclusive mkdir, existing parent validated, new leaf exclusive with no reuse or exist_ok.',
 'Postcreate revalidation catches observed aliases; no delete/reset/clean/recovery of old leaf, output or raw. Original aa7b24 prep failure remains driver1/zero child invocations/all14NOT_RUN.',
 'Four Root assertion functions copied byte-identically from pinned Root runner. Main DB/schema/typed rows/wire/permission/journal/sidecar assertions are not weakened.',
 'Same14 selectors,16percase/224totalHTTP,150snative/180sownedcase and1800sowneddriver limits. First failure/skip/unbound input stops; full Job cleanup and actual nullable exit retained.',
 'PreGo resources, actual Go graph, compiler WORK/generated/importcfg/archive/testexe closure, before/nativeafter/proofsafter and late runtime checks remain byte-identical outside path changes.',
 'Existing authorized gofmt of sole test is future operation only. Current edited54abc44 and protected domain7fb40 verified; this review does not accept source or execute gofmt/Go/SQL/helper/HTTP/SDK.',
 'Launcher same bytes uses verified helper and Job for driver; no AST result is called runtime PASS. Future once-only authorization must bind v2 hashes/new namespace before author launches.'
]
save('audit.json',{'input_refs':inputs,'actual_path_observation':state,'exact_inverse_restores_v1':True,'Root_function_byte_identity':{k:sha(v) for k,v in copied_functions.items()},'selectors':names,'checks':checks,'new_failure_origins':[],'actual_execution':False,'AST_only':True})
for f,x in protected:need(ref(f)==x,'protected input changed '+str(f))
save('review.json',{'schema':'researchos.closedcopy-harness-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION','requested_changes':[],'reviewed_at':datetime.now(timezone.utc).isoformat(),'driver_ref':ref(V/'execute.py'),'launcher_ref':ref(V/'launch.py'),'static_audit_ref':ref(V/'static_audit.json'),'author_manifest_ref':ref(V/'manifest.json'),'author_handoff_ref':ref(V/'handoff.json'),'v1_driver_ref':ref(OLD/'execute.py'),'original_failure_ref':ref(OLD/'failure_origin.json'),'independent_audit_ref':ref(H/'audit.json'),'conditions':['Root registers actual pinned v2/new-input authorization before any launcher execution.','Keep old failed preparation/raw/14NOT_RUN and same-chain failure1; no automatic retry or reset.','New execution must freeze actual post-gofmt source/full compiler closure and fresh exe before case01, preserving exact14 caps and firstUnexpectedStop.'],'known_limitations':['Path-based lstat/resolve/mkdir checks have a same-user TOCTOU window; no handle-relative directory creation or adversarial replacement exclusion is proven. Exact parent/leaf must remain exclusive to author.','AST and byte-diff evidence do not validate Windows directory/process or SQLite behavior.','Current source remains unformatted WIP; source qualification is a separate review after frozen execution evidence.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'actual_Go_SQL_Node_HTTP_MODEL_helper_execution':0,'new_failure_origins':[]})
save('manifest.json',{'files':[ref(f) for f in sorted(H.rglob('*')) if f.is_file()]})
save('handoff.json',{'review_ref':ref(H/'review.json'),'manifest_ref':ref(H/'manifest.json'),'audit_ref':ref(H/'audit.json'),'source_acceptance':False,'actual_execution':False,'new_failure_origins':[]})
print(json.dumps({n:ref(H/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False,indent=2))
