from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;B=N.parent.parent/'qualification_recovery_boundary_boot6_codex/20261025-current-chat';W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs=[]
def verify(p,x):
 a=ref(p);assert a['sha256']==x['sha256']
 if 'bytes'in x:assert a['bytes']==x['bytes']
 refs.append(a);return a
seal=B/'final-v12-additive-seal.json';verify(seal,{'sha256':'28c48b05b90032f47158272fcbcad940ccfa196bd0557a4d0879c4d860d8142b'});s=read(seal);assert len(s['evidence'])==28
for x in s['evidence']:verify(B/x['file'],x)
manifest=B/'final-v12-six-source-manifest.json';verify(manifest,{'sha256':s['source_manifest_sha256']});m=read(manifest);assert len(m)==6
pre=read(B/'final-v12-pre-source-manifest.json');assert pre==m
for x in m:verify(W/x['path'],x)
old={x['path']:x for x in read(B/'final-v11-six-source-manifest.json')};changes=[x['path']for x in m if x['sha256']!=old[x['path']]['sha256']]
expected=['internal/recoveryboundary/boot_windows.go','internal/recoveryboundary/boot_windows_test.go'];assert changes==expected
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=W)
assert g('rev-parse','HEAD').decode().strip()=='08d63ed86356a93fe5715732cfeae0624c5cb6c9';assert not g('diff','--cached','--name-only');assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==expected
checks=[]
for stem in ['v12-dev-01','v12-dev-02','final-v12-c-windows-tests','final-v12-d-windows-tests','final-v12-linux-crossbuild','final-v12-diff-check']:
 q=B/(stem+'.exit.txt');native=int(q.read_text(encoding='utf-8-sig').strip());assert native==(1 if stem=='v12-dev-01'else 0)
 stdout=(B/(stem+'.stdout.raw')).read_text(encoding='utf-8-sig');checks.append({'id':stem,'native_exit':native,'skips':[l for l in stdout.splitlines()if 'SKIP:'in l]})
out={'schema':'researchos.boot6-v12-root-verification.v1','seal':ref(seal),'source_manifest':ref(manifest),'base_commit':'08d63ed86356a93fe5715732cfeae0624c5cb6c9','exact6_current_and_pre_post':True,'changed_files':changes,'patch_ref':ref(B/'final-v12-six-source.patch'),'checks':checks,'verified_refs':refs,'limits':['Dangerous privilege inputs are synthetic native-LUID structures; no actual dangerous token or native bypass was exercised.','Real safe token producer/consumer tested; full privileged actual plan/arm remains unavailable.'],'independent_fix_acceptance':False,'formal_increment':0}
with(N/'C57-boot6-v12-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'refs':len(refs),'files':6,'changes':changes,'checks':checks,'formal_increment':0},ensure_ascii=False))
