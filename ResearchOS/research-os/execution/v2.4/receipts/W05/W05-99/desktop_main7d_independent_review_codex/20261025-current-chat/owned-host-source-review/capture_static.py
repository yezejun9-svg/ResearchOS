import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
R=Path('D:/作品集/ResearchOS/research-os')
E=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp558/Product-host-exact14-source-scope.json'
raw=S.read_bytes(); assert hashlib.sha256(raw).hexdigest()=='3f1a86d6967544245f0d7c589996c70d2cd8d08d00fa7f7fab8edaef069f7bce'
scope=json.loads(raw); W=Path(scope['worktree']); O=E/'static-001'; O.mkdir(exist_ok=False)
(O/'scope.json').write_bytes(raw)
refs=[]
for rel in scope['allowed_source_paths']:
 p=W/rel; b=p.read_bytes(); f=O/'source'/rel; f.parent.mkdir(parents=True,exist_ok=True); f.write_bytes(b)
 refs.append(dict(path=rel,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
changed=[x['path'] for x in refs if hashlib.sha256((W/x['path']).read_bytes()).hexdigest()!=x['sha256']]
proc=subprocess.run(['git','diff','--no-ext-diff','--',*scope['allowed_source_paths']],cwd=W,capture_output=True,check=True)
(O/'tracked-diff.txt').write_bytes(proc.stdout)
record=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),scope_sha256=hashlib.sha256(raw).hexdigest(),snapshot_refs=refs,changed_during_capture=changed,source_freeze=False,native_runs=0,tests_run=0)
(O/'SNAPSHOT.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
