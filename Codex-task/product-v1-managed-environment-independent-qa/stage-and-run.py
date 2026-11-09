from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,os
Q=Path(__file__).resolve().parent
A=Q.parent/'product-v1-managed-environment-author'
R=Path('D:/作品集/ResearchOS/research-os')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fp=A/'FROZEN.json';mp=A/'EVIDENCE_MANIFEST.json'
assert sha(fp)=='516db4d831df24bb74d59eed7f4e33f0fec62635e88d2048f00733db7314cbb4'
assert sha(mp)=='5c4671b9fced75938e8c4115bfbf664d69377fb5bcf2914901f6b6820b721a64'
freeze=json.loads(fp.read_text(encoding='utf-8'));manifest=json.loads(mp.read_text(encoding='utf-8'))
for item in manifest['files']:assert sha(A/item['path'])==item['sha256'],item['path']
assert len(freeze['source_sha256'])==2
S=Q/'stage';S.mkdir(exist_ok=False)
pins={}
def cp(src,n,kind):
 dst=S/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 assert sha(src)==sha(dst);pins[n]={'sha256':sha(dst),'origin':str(src),'kind':kind}
for n,h in freeze['source_sha256'].items():
 assert sha(Path(freeze['worktree'])/n)==h and sha(A/'source'/n)==h
 cp(A/'source'/n,n,'FROZEN_AUTHOR_SOURCE')
for src in (R/'apps/desktop/main/lib').iterdir():
 n=src.relative_to(R).as_posix()
 if src.is_file() and src.suffix in ['.js','.mjs'] and n not in pins:cp(src,n,'UNCHANGED_BASELINE_DEPENDENCY')
cp(R/'tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','UNCHANGED_BASELINE_TEST')
scope=R/'execution/product-v1/receipts/single-harness-20261104/managed-environment/scope.json'
lock=json.loads((R/'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'));node=lock['tools']['node'];assert sha(Path(node['path']))==node['sha256']
with (Q/'stage-manifest.json').open('x',encoding='utf-8') as f:json.dump({'freeze_sha256':sha(fp),'manifest_sha256':sha(mp),'scope_sha256':sha(scope),'source_sha256':freeze['source_sha256'],'node':node,'files':pins},f,ensure_ascii=False,indent=2);f.write('\n')
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','PI_','MU_','CODEX_','OPENAI_','ANTHROPIC_')) and k.upper() not in ['NODE_OPTIONS','NODE_PATH']}
private=Q/'runtime';settings={'USERPROFILE':str(private/'profile'),'APPDATA':str(private/'profile/roaming'),'LOCALAPPDATA':str(private/'profile/local'),'TMP':str(private/'tmp'),'TEMP':str(private/'tmp')}
for p in settings.values():Path(p).mkdir(parents=True,exist_ok=True)
env.update(settings)
out=Q/'checks01';out.mkdir(exist_ok=False)
commands=[('independent',[node['path'],'--require',str(Q/'guard.cjs'),str(Q/'independent.mjs')]),
 ('author-replay',[node['path'],'--require',str(Q/'guard.cjs'),str(S/'tests/ui/desktop/managed-environment.test.mjs')]),
 ('baseline-boundary',[node['path'],'--require',str(Q/'guard.cjs'),str(S/'tests/ui/desktop/desktop-management-boundary.test.mjs')]),
 ('syntax',[node['path'],'--check',str(S/'apps/desktop/main/lib/desktop-management.js')])]
rows=[]
for name,argv in commands:
 with (out/(name+'.stdout.raw')).open('wb') as stdout,(out/(name+'.stderr.raw')).open('wb') as stderr:
  result=subprocess.run(argv,cwd=Q,env=env,stdout=stdout,stderr=stderr,timeout=90)
 row={'phase':name,'argv':argv,'cwd':str(Q),'environment_overrides':settings,'exit_code':result.returncode,'stdout_sha256':sha(out/(name+'.stdout.raw')),'stderr_sha256':sha(out/(name+'.stderr.raw'))}
 with (out/(name+'.command.json')).open('x',encoding='utf-8') as f:json.dump(row,f,ensure_ascii=False,indent=2);f.write('\n')
 rows.append(row);print(json.dumps({'phase':name,'exit_code':result.returncode}),flush=True)
unchanged=all(sha(S/n)==v['sha256'] for n,v in pins.items())
assert unchanged
with (out/'results.json').open('x',encoding='utf-8') as f:json.dump({'commands':rows,'stage_inputs_unchanged':unchanged,'source_sha256':freeze['source_sha256'],'formal_increment':0},f,ensure_ascii=False,indent=2);f.write('\n')
raise SystemExit(0 if all(r['exit_code']==0 for r in rows) else 1)
