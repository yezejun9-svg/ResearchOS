import json,hashlib,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=read(N/'React-Main-integration-baseline.json');s=read(N/'continuation-cp536/React-Main-integration-scope.json');a=read(R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat/SOURCE14-SEAL.json')
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *x:subprocess.check_output(git+list(x),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==s['target_commit']and g('rev-parse','HEAD^{tree}').decode().strip()==s['target_tree'];assert not g('diff','--cached','--name-only')
dirty=g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0));assert dirty==b['dirty_paths']
for x in b['dirty_files']:
 p=R/x['relative_path'];assert p.is_file()==x['exists']
 if x['exists']:assert digest(p)==x['sha256'],str(p)
for x in b['protected_source']+b['original_dist_refs']:assert digest(Path(x['path']))==x['sha256']
for p,sha in a['source_sha256'].items():assert digest(R/p)==sha,p
out={'status':'EXACT_REVIEWED_REACT_FF_VERIFIED','Main_HEAD':s['target_commit'],'tree':s['target_tree'],'dirty_paths_unchanged':len(dirty),'protected_unchanged':len(b['protected_source']),'old_dist_files_unchanged':len(b['original_dist_refs']),'new_source_pins_exact':len(a['source_sha256']),'original_runtime_or_data_action':False,'formal_increment':0}
with(N/'React-Main-after-FF-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
root=Path(s['build_output_root']);root.mkdir(exist_ok=False)
(root/'BUILD-OUTPUT.md').write_text('This task-owned directory contains the independently reviewed React production bundle staged from Main. Existing apps/web/dist and original running instances are preserved. Keep this build until superseded by a later accepted integration; no credentials or runtime data belong here.'+chr(10),encoding='utf8')
print(json.dumps(out,ensure_ascii=False))
