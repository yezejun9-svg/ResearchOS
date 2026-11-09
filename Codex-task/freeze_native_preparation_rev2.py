from pathlib import Path
import hashlib, json, difflib
wt=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-native-preparation-wiring-20261105')
main=Path('D:/作品集/ResearchOS/research-os')
out=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-preparation-wiring-author-20261105-rev2')
paths=['internal/domain/harness_preparation_windows.go','internal/domain/harness_preparation_windows_test.go','internal/domain/runtime_harness_windows.go','internal/host/harness_windows.go','internal/host/harness_windows_test.go']
sha=lambda data: hashlib.sha256(data).hexdigest()
manifest={'schema':'researchos.native-preparation-wiring-author.v1','base_head':'787a1ff772bb53d33be86e7045313ed123cd2d70','scope_sha256':'a9bf739875af702116068d3a55131d4ffd0c0730e8b12bc91b78f900b7bbdf41','b3_rev4_manifest_sha256':'522a562016d0b94ea4576d956106b08068bbf47449b6f9de01683d12b709b2b2','state':'SOURCE_CANDIDATE_UNTESTED_REV2','paths':{}}
forward=[];inverse=[]
for p in paths:
    old=(main/p).read_bytes() if (main/p).exists() else b''
    new=(wt/p).read_bytes()
    bp=out/'baseline'/p; np=out/'source'/p
    bp.parent.mkdir(parents=True,exist_ok=True);np.parent.mkdir(parents=True,exist_ok=True)
    bp.write_bytes(old);np.write_bytes(new)
    manifest['paths'][p]={'baseline_sha256':sha(old) if old else 'ABSENT_BEFORE','source_sha256':sha(new),'baseline_bytes':len(old),'source_bytes':len(new)}
    a=old.decode('utf-8').splitlines(keepends=True);b=new.decode('utf-8').splitlines(keepends=True)
    forward.extend(difflib.unified_diff(a,b,fromfile='a/'+p,tofile='b/'+p))
    inverse.extend(difflib.unified_diff(b,a,fromfile='b/'+p,tofile='a/'+p))
(out/'forward.patch').write_text(''.join(forward),encoding='utf-8',newline='')
(out/'inverse.patch').write_text(''.join(inverse),encoding='utf-8',newline='')
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(out/'MANIFEST.json'),'sha256':sha((out/'MANIFEST.json').read_bytes()),'paths':manifest['paths']},ensure_ascii=False))

