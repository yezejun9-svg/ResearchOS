from pathlib import Path
import hashlib,json,difflib
OUT=Path(__file__).parent
OLD=OUT.parent/'w14-native-create-clients-independent-review-01'
BASE=Path('D:/作品集/ResearchOS/research-os')
LIVE=BASE/'.local/worktrees/w14-native-create-clients-20261104'
C=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-w14-clients-author/freeze-02')
D=BASE/'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/author/freeze-02'
M='12252ed255167a9a60398680145dd50c86ffef4dfcba7969b81f7edc32f61784'
rows=[]
def pin(p,want):
 b=p.read_bytes();got=hashlib.sha256(b).hexdigest();rows.append(dict(path=str(p),sha256=got,expected=want,bytes=len(b),match=got==want));assert got==want,str(p);return b
m=json.loads(pin(C/'MANIFEST.final.json',M));pin(D/'MANIFEST.final.json',M)
assert m['construction_frozen'] and not m['source_modification_permitted']
for item in m['raw_and_support_files']:
 for root in (C,D):pin(root/item['path'],item['sha256'])
for item in m['source_pins']:pin(LIVE/item['path'],item['sha256'])
oldC=C.parent/'freeze-01';oldD=D.parent/'freeze-01'
oldM=json.loads(pin(oldC/'MANIFEST.json','4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02'))
pin(oldD/'MANIFEST.json','4b0adde5874c424eb43b1414cdfe36d6d919888f4c3fa69ecd41e4704e8a1c02')
for item in oldM['raw_and_support_files']:
 for root in (oldC,oldD):pin(root/item['path'],item['sha256'])
pin(OLD/'source-review.json','8215291ba3e98de8774132c042a4bc4228945fdf61a3fa516e9c554af31fc102')
diff=[]
for item in m['source_pins']:
 rel=item['path'];old=pin(oldC/'source-snapshot'/rel,next(p['sha256'] for p in oldM['source_pins'] if p['path']==rel)).decode('utf-8').splitlines(keepends=True)
 new=(C/'source-snapshot'/rel).read_text(encoding='utf-8').splitlines(keepends=True)
 diff.extend(difflib.unified_diff(old,new,fromfile='freeze01/'+rel,tofile='freeze02/'+rel))
(OUT/'repair.diff').write_text(''.join(diff),encoding='utf-8',newline='')
extra=pin(OLD/'independent-go-extra.txt','58a9af8b238b182a39070a84c23bf1123bb6bb5e87a138e05b1f172eb9a97d91')
(OUT/'combined_native_attestation_test.go').write_bytes((C/'source-snapshot/apps/cli/cli_native_attestation_test.go').read_bytes()+b'\n'+extra+b'\n'+(OUT/'additional-go-cases.txt').read_bytes())
(OUT/'go-overlay.json').write_text(json.dumps({'Replace':{str(LIVE/'apps/cli/cli_native_attestation_test.go'):str(OUT/'combined_native_attestation_test.go')}}),encoding='utf-8')
stage=[]
for rel in ('apps/desktop/main/lib/native.js','apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/ipc.js','tests/ui/native-create-attestation-fixture.cjs'):
 data=(C/'source-snapshot'/rel).read_bytes();p=OUT/'isolated-frozen-node'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);stage.append(dict(path=rel,sha256=hashlib.sha256(data).hexdigest(),origin='freeze02'))
for rel in ('apps/desktop/main/lib/host.js','apps/desktop/main/lib/v2.js','apps/desktop/main/lib/wire-values.mjs'):
 data=(OLD/'isolated-frozen-node'/rel).read_bytes();p=OUT/'isolated-frozen-node'/rel;p.write_bytes(data);stage.append(dict(path=rel,sha256=hashlib.sha256(data).hexdigest(),origin='independent pinned Main dependencies from v1 staging'))
(OUT/'baseline-http-wire.js').write_bytes(pin(OLD/'baseline-http-wire.js','216ff4f4c46b112d83984d4aae3895ce00d9a4ff1d9a92685f9d54b4dcde0d38'))
node=pin(OLD/'independent-node-attempt-02.cjs','ee571e72124f10efd6aace00a6f96a248ac9caa640c77072281b79276636615b').decode('utf-8')
node=node.replace("'node-independent-checks-attempt-02.json'","'node-independent-checks.json'")
(OUT/'independent-node.cjs').write_text(node,encoding='utf-8',newline='')
(OUT/'pin-verification.json').write_text(json.dumps(dict(status='ALL_MATCH',checks=len(rows),rows=rows,node_staging=stage),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='ALL_MATCH',checks=len(rows),new_support=len(m['raw_and_support_files']),old_support=len(oldM['raw_and_support_files']),live_paths=9,construction_frozen=True)))
