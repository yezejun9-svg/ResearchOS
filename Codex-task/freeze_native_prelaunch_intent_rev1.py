from pathlib import Path
import hashlib,json,difflib
wt=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-native-prelaunch-intent-20261105')
main=Path('D:/作品集/ResearchOS/research-os')
out=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-prelaunch-intent-author-20261105-rev1')
if out.exists():raise SystemExit('archive exists')
paths=['adapters/runtime/codex_qualification_windows.go','adapters/runtime/codex_qualification_capture_windows.go','adapters/runtime/codex_qualification_capture_windows_test.go']
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest={'schema':'researchos.native-prelaunch-intent-author.v1','base_head':'61fe2d6a9f9ecbdd8a9de597ffbb6757e49de667','scope_sha256':'a26dcd1a0a30694c0f2a0c222c267199fc9c35b37296527701ec3ac570305948','contract_sha256':'ad35f3ed7f92d1c1d31a40da896ae10e743b16f94fd7dc00510ec870ee4b5e5c','status':'SOURCE_CANDIDATE_UNTESTED','paths':{}}
forward=[];inverse=[]
for p in paths:
    old=(main/p).read_bytes();new=(wt/p).read_bytes()
    bp=out/'baseline'/p;np=out/'source'/p;bp.parent.mkdir(parents=True,exist_ok=True);np.parent.mkdir(parents=True,exist_ok=True)
    bp.write_bytes(old);np.write_bytes(new)
    manifest['paths'][p]={'baseline_sha256':sha(old),'source_sha256':sha(new),'baseline_bytes':len(old),'source_bytes':len(new)}
    a=old.decode('utf-8').splitlines(keepends=True);b=new.decode('utf-8').splitlines(keepends=True)
    forward.extend(difflib.unified_diff(a,b,fromfile='a/'+p,tofile='b/'+p));inverse.extend(difflib.unified_diff(b,a,fromfile='b/'+p,tofile='a/'+p))
(out/'forward.patch').write_text(''.join(forward),encoding='utf-8',newline='')
(out/'inverse.patch').write_text(''.join(inverse),encoding='utf-8',newline='')
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(out/'MANIFEST.json'),'sha256':sha((out/'MANIFEST.json').read_bytes()),'paths':manifest['paths']},ensure_ascii=False))
