from pathlib import Path
import hashlib,json,shutil,subprocess,os,difflib,datetime
Q=Path(__file__).resolve().parent;A=Q.parent/'product-v1-workbench-author-revision-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fp=A/'FROZEN.json';mp=A/'EVIDENCE_MANIFEST.json'
assert sha(fp)=='ce09b6e7db586688899cab7e3653bfebb93d15e0bb3a0b45078d3f6f882cb817'
assert sha(mp)=='615e79576c69ceab915f7e1b1154f3a0bbab68f726b22e8260564ff0c3a48ef4'
f=json.loads(fp.read_text(encoding='utf-8'));m=json.loads(mp.read_text(encoding='utf-8'))
assert f['construction_frozen'] and not f['source_modification_permitted']
for e in m['files']:assert sha(A/e['path'])==e['sha256'],e['path']
assert len(m['files'])==110
prior=json.loads((Q/'stage01-manifest.json').read_text(encoding='utf-8'))
new={**f['source_sha256'],**f['test_sha256']}
assert sorted(n for n,h in new.items() if h!=prior['source_sha256_exact10'][n])==sorted(['apps/web/src/workbench.jsx','tests/ui/desktop/harness-workbench.test.mjs'])
for n,h in new.items():assert sha(A/'source-snapshot'/n)==h and sha(Path(f['worktree'])/n)==h
S=Q/'stage02';shutil.copytree(Q/'stage01',S)
for n in new:shutil.copyfile(A/'source-snapshot'/n,S/n)
out=Q/'checks03-freeze02';out.mkdir(exist_ok=False)
for n in ['apps/web/src/workbench.jsx','tests/ui/desktop/harness-workbench.test.mjs']:
 before=(Q/'stage01'/n).read_text(encoding='utf-8').splitlines(True);after=(S/n).read_text(encoding='utf-8').splitlines(True)
 (out/(Path(n).name+'.diff')).write_text(''.join(difflib.unified_diff(before,after,fromfile='freeze01/'+n,tofile='freeze02/'+n)),encoding='utf-8')
node=Path(prior['node']['path']);assert sha(node)==prior['node']['sha256']
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','MU_','PI_','CODEX_','OPENAI_','ANTHROPIC_')) and k.upper() not in ['NODE_OPTIONS','NODE_PATH']}
private=Q/'runtime';settings={'USERPROFILE':str(private/'profile'),'APPDATA':str(private/'profile/roaming'),'LOCALAPPDATA':str(private/'profile/local'),'TEMP':str(private/'tmp'),'TMP':str(private/'tmp')};env.update(settings)
commands=[('independent-draft-recheck',[str(node),'--require',str(Q/'guard.cjs'),str(Q/'draft-recheck02.mjs')]),
 ('author-changed-ui-replay',[str(node),'--require',str(Q/'guard.cjs'),str(S/'tests/ui/desktop/harness-workbench.test.mjs')])]
inputs={n:sha(S/n) for n in new}
rows=[]
for name,argv in commands:
 with (out/(name+'.stdout.raw')).open('wb') as stdout,(out/(name+'.stderr.raw')).open('wb') as stderr:
  code=subprocess.run(argv,cwd=Q,env=env,stdout=stdout,stderr=stderr,timeout=60).returncode
 row={'phase':name,'argv':argv,'cwd':str(Q),'environment_overrides':settings,'exit_code':code,'stdout_sha256':sha(out/(name+'.stdout.raw')),'stderr_sha256':sha(out/(name+'.stderr.raw'))}
 with (out/(name+'.command.json')).open('x',encoding='utf-8') as p:json.dump(row,p,ensure_ascii=False,indent=2);p.write('\n')
 rows.append(row);print(json.dumps({'phase':name,'exit_code':code}),flush=True)
assert inputs=={n:sha(S/n) for n in new}
report={'freeze_sha256':sha(fp),'manifest_sha256':sha(mp),'verified_author_evidence_files':110,'source_sha256':new,'changed_since_freeze01':f['changed_since_freeze01'],
 'unchanged_eight_reference':'stage01-manifest.json; review01 source/IPC/HTTP/journal evidence remains applicable to byte-identical eight files.',
 'commands':rows,'inputs_unchanged':True,'node':prior['node'],'no_real_gui_model_native_or_http':True,'formal_increment':0,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (Q/'stage02-manifest.json').open('x',encoding='utf-8') as p:json.dump(report,p,ensure_ascii=False,indent=2);p.write('\n')
raise SystemExit(0 if all(x['exit_code']==0 for x in rows) else 1)
