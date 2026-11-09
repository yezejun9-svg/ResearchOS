from pathlib import Path
import hashlib,json
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
B=N.parent.parent/'qualification_recovery_boundary_boot6_codex/20261025-current-chat';W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs=[]
def verify(p,x):
 a=ref(p);assert a['sha256']==x['sha256']
 if 'bytes'in x:assert a['bytes']==x['bytes']
 refs.append(a);return a
seal=B/'final-v11-additive-seal.json';verify(seal,{'sha256':'b5cb0711c3a357ff9226ce562bf3c326098200d9723aef0765ed528c778025f7'})
s=read(seal);assert len(s['files'])==34
for x in s['files']:verify(B/x['file'],x)
manifest=B/'final-v11-six-source-manifest.json';verify(manifest,{'sha256':s['source_manifest_sha256']});m=read(manifest);assert len(m)==6
for x in m:verify(W/x['path'],x)
old={x['path']:x for x in read(B/'final-v10-six-source-manifest.json')}
changed=[x['path']for x in m if x['sha256']!=old[x['path']]['sha256']];assert changed==['internal/recoveryboundary/boot_windows_test.go']
checks=[]
for stem in ['final-v11-c-inherited-windows-tests','final-v11-d-windows-tests','final-v11-linux-crossbuild','final-v11-diff-check','v11-dev-c-natural-01','v11-dev-c-natural-02','v11-dev-c-natural-03','v11-dev-c-focused-04']:
 native=int((B/(stem+'.exit.txt')).read_text(encoding='utf-8-sig').strip());assert native==(1 if stem=='v11-dev-c-natural-02' else 0)
 raw=(B/(stem+'.stdout.raw')).read_text(encoding='utf-8-sig');checks.append({'id':stem,'native_exit':native,'skip_lines':[l for l in raw.splitlines()if 'SKIP:'in l]})
 for suffix in ['.stdout.raw','.stderr.raw','.exit.txt']:
  a=ref(B/(stem+suffix))
  if a not in refs:refs.append(a)
c=(B/'final-v11-c-inherited-windows-tests.stdout.raw').read_text(encoding='utf-8-sig')
assert '9670edefaf50d6f0353087f05cfff517a271def615cdba2a3ba23a555a9d0a28'in c
assert '--- FAIL:'not in c
out={'schema':'researchos.boot6-v11-root-verification.v1','seal':ref(seal),'source_manifest':ref(manifest),'source_count':6,'only_change_since_v10':changed,'checks':checks,'verified_refs':refs,'C_inherited_native_preimage_restore':'parent208/file106 inherited; binary/meaningful fields/flags restored','D_noAI':'explicit protected fixture native restore passed; natural dense inherited case skipped on D and tested on C','source_author_freeze_only':True,'phase2_not_yet_started':True,'formal_increment':0,'remaining':['distinct privileged management SID','readable SACL positive native case','actual targets','real FullRestart','actual C transaction','independent final57 acceptance']}
with(N/'C57-boot6-v11-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'refs':len(refs),'sources':6,'change':changed,'checks':checks,'formal_increment':0},ensure_ascii=False))
