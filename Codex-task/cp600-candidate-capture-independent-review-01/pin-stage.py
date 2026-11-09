from pathlib import Path
import hashlib,json,difflib
OUT=Path(__file__).parent
AUTHOR=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author')
BASE=Path('D:/作品集/ResearchOS/research-os')
LIVE=BASE/'.local/worktrees/host-candidate-capture-20261104'
SCOPE=BASE/'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/candidate-capture'
rows=[]
def pin(path,want):
 data=path.read_bytes();sha=hashlib.sha256(data).hexdigest();rows.append(dict(path=str(path),sha256=sha,expected=want,bytes=len(data),match=sha==want));assert sha==want,str(path);return data
f=json.loads(pin(AUTHOR/'FROZEN.json','b5728395e5435f6934937ceb97daeb857b59c665c55fe36cd790e5263c9eabb8'))
m=json.loads(pin(AUTHOR/'EVIDENCE_MANIFEST.json','67ace46e0a44a228be9a9086a01c659a7308d767f365870e2e2fa9b0cd46f862'))
assert f['source_edits_stopped'] and len(f['source_pins'])==6
for item in m['entries']:pin(AUTHOR/item['path'],item['sha256'])
scope=json.loads(pin(SCOPE/'scope.json','a09e9527ab5f116db8ee7c757e34f8deefaa32ca661bea253a387e1f167a5ae8'))
pin(SCOPE/'reviews/design/design-review.json','1245d2689c8a8f3134fd302ab3695c6a1f78dfdb37215fb272f3e23cbd87c6be')
pin(SCOPE/'readiness/MANIFEST.final.json','d0f46a83b9a1ce5300e67d145e0b833b8d75bd0c5e58a345f9817965b42fe583')
pin(SCOPE/'readiness/CLARIFICATION-01.md','5d0f81849c20b0d6a7f811837a03b29fad25946b79229850a2be567c6949a63b')
diff=[]
for item in f['source_pins']:
 rel=item['path'];data=pin(LIVE/rel,item['sha256'])
 snapshot=pin(AUTHOR/'attempt-02/snapshot'/Path(rel).name,item['sha256'])
 assert data==snapshot
 dest=OUT/'snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(snapshot)
 baseline=scope['baseline_sha256'][rel]
 old=[] if baseline=='ABSENT_BEFORE' else pin(BASE/rel,baseline).decode('utf-8').splitlines(keepends=True)
 diff.extend(difflib.unified_diff(old,snapshot.decode('utf-8').splitlines(keepends=True),fromfile='Main/'+rel,tofile='frozen/'+rel))
(OUT/'source.diff').write_text(''.join(diff),encoding='utf-8',newline='')
(OUT/'pin-verification.json').write_text(json.dumps(dict(status='ALL_MATCH',checks=len(rows),author_evidence_files=len(m['entries']),live_source_files=6,source_pins=f['source_pins'],rows=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='ALL_MATCH',checks=len(rows),author_evidence_files=len(m['entries']),live_source_files=6,staged_snapshot_files=6)))
