from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent;run=here/'run-03'
overlay=json.loads((run/'overlay-corrected.json').read_bytes())
source=here/'independent_atomic_test.go'
target=run/'atomic-test'/'independent_atomic_test.go'
assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
virtual=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104/internal/domain/independent_harness_atomic_test.go')
overlay['Replace'][str(virtual)]=str(target)
out=run/'overlay-atomic.json';assert not out.exists()
out.write_text(json.dumps(overlay,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
manifest={'origin_key':'backend-v1-unknown-terminal-atomic-window','source_changed':False,'test_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'test':str(target),'overlay_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'classification':'FRESH_DB_OWNED_FAKE_PROCESS_TERMINAL_WRITE_FAULT'}
out=run/'atomic-fixture.json';assert not out.exists();out.write_text(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared_atomic_fixture':True,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
