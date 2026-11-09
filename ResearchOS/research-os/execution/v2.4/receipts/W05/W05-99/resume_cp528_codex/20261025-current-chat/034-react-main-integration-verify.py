import ast,hashlib,json,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
b=read(N/'React-Main-integration-baseline.json');s=read(N/'continuation-cp536/React-Main-integration-scope.json');a=read(R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat/SOURCE14-SEAL.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *x:subprocess.check_output(git+list(x),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==s['target_commit'] and not g('diff','--cached','--name-only')
dirty=g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0));assert dirty==b['dirty_paths']
for x in b['dirty_files']:
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert ref(p)['sha256']==x['sha256']
for x in b['protected_source']+b['original_dist_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
old_files=subprocess.check_output(['rg','--files','--hidden','--no-ignore',s['production_dist_preservation']],cwd=R).decode('utf8').splitlines()
assert {str(Path(x).resolve())for x in old_files}=={str(Path(x['path']).resolve())for x in b['original_dist_refs']}
build=Path(s['build_output']);new_files=subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(build)],cwd=R).decode('utf8').splitlines();actual={Path(p).relative_to(build).as_posix():ref(Path(p))for p in new_files}
assert set(actual)==set(a['active_dist_sha256'])
for p,x in actual.items():assert x['sha256']==a['active_dist_sha256'][p]
for p,sha in a['source_sha256'].items():assert ref(R/p)['sha256']==sha
tree=ast.parse((R/'ops/ci/ui.py').read_text(encoding='utf8'));patterns=None
for node in ast.walk(tree):
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='patterns'for t in node.targets):patterns=ast.literal_eval(node.value)
assert len(patterns)==20
manifest={p.relative_to(R).as_posix():ref(p)['sha256']for pattern in patterns for p in R.glob(pattern)if p.is_file()}
required=['apps/web/src/components/app-shell.jsx','apps/web/src/components/ui.jsx','apps/web/src/components/workbench-layout.jsx','tests/ui/frontend-redesign.cjs','tests/ui/frontend-redesign-fixture.cjs','tests/ui/desktop/w13-react.test.js']
assert all(p in manifest for p in required)
out={'schema':'researchos.React-main-local-integration-result.v1','status':'REVIEWED_SOURCE_INTEGRATED_AND_EXACT_STAGED_BUILD_VERIFIED','Main_HEAD':s['target_commit'],'Main_tree':s['target_tree'],'prior_Main_HEAD':s['expected_Main_HEAD'],'source_changed_count':12,'existing_dirty_count_preserved':20,'protected_unchanged':9,'old_dist_files_unchanged':33,'staged_build':str(build),'staged_build_refs':list(actual.values()),'bundle_byte_equal_to_independently_reviewed_candidate':True,'ci_input_patterns':20,'ci_source_manifest_count':len(manifest),'required_ci_bound':{p:manifest[p]for p in required},'Main_working_tree_claim':'Original protected dirty changes retained, not a globally clean working tree','original_runtime_or_data_action':False,'native_packaged_Desktop':'NOT_RUN','formal_increment':0,'C57_base_commit_unchanged':'085b4711afe0c1288448b174eef24ecd5af0551b'}
with(N/'React-Main-integration-result.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
