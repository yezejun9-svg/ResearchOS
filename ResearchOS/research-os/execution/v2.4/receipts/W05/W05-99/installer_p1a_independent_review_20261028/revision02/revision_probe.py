import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys
from types import SimpleNamespace
R=pathlib.Path(__file__).resolve().parent;W=pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\installer-p1a-20261028');REPO=pathlib.Path(r'D:\作品集\ResearchOS\research-os');sys.dont_write_bytecode=True
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
scope=REPO/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp571/Installer-P1a-exact2-scope-revision.json'
author=REPO/'execution/v2.4/receipts/W05/W05-99/installer_p1a_source_codex/20261028/revision02/FINAL-MANIFEST.json'
assert sha(scope)=='0fb34731c538311bc485702df165ef69304ff2463e323de700ff50b043cdc72a';assert sha(author)=='3d2a94993228095674484df4590054e30c0b16f6978aaf31ca0a5693ab841ff4'
a=json.loads(author.read_bytes());s=json.loads(scope.read_bytes());git=['git','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(W)]
def g(*args):
 p=subprocess.run(git+list(args),capture_output=True);assert p.returncode==0,p.stderr;return p.stdout
assert g('rev-parse','HEAD').decode().strip()==a['commit'];assert g('rev-parse','HEAD^{tree}').decode().strip()==a['tree'];assert not g('status','--porcelain=v1').strip()
diff=g('diff','--name-status',a['base_commit'],a['commit']).decode().splitlines();assert sorted(diff)==sorted('M\t'+p for p in s['allowed_source_paths'])
for f in a['changed_source']+a['unchanged_source']:
 assert sha(W/f['path'])==f['sha256'];assert hashlib.sha256(g('show','HEAD:'+f['path'])).hexdigest()==f['sha256']
save('binding.json',{'scope_sha256':sha(scope),'author_sha256':sha(author),'head':a['commit'],'tree':a['tree'],'clean':True,'diff':diff,'changed':a['changed_source'],'unchanged':a['unchanged_source']})
(R/'source.diff').write_bytes(g('diff',a['base_commit'],a['commit'],'--',*s['allowed_source_paths']))
for name,rel in [('candidate-build.py','ops/release/product_installer/build.py'),('candidate-tests.py','tests/release/product_installer_build_test.py')]:shutil.copyfile(W/rel,R/name)
locked=json.loads((W/'execution/toolchains/locked.json').read_bytes())['tools'];assert sha(locked['python']['path'])==locked['python']['sha256'];save('python-toolchain.json',locked['python'])
scratch=R/'scratch';scratch.mkdir();env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TEMP':str(scratch),'TMP':str(scratch)}
def run(label,argv):
 p=subprocess.run([str(x) for x in argv],env=env,cwd=R,capture_output=True);(R/(label+'.stdout.raw')).write_bytes(p.stdout);(R/(label+'.stderr.raw')).write_bytes(p.stderr);save(label+'.command.json',{'argv':[str(x) for x in argv],'cwd':str(R),'exit':p.returncode});return p
assert run('python-regressions',[locked['python']['path'],'-B',W/'tests/release/product_installer_build_test.py']).returncode==0
spec=importlib.util.spec_from_file_location('candidate_builder',W/'ops/release/product_installer/build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
assert b.bound_roots(str(scope),s and a['scope_sha256'])==(s['artifact_root'],s['receipt_root'])
positive=[]
for tag,schema in [('a','researchos.installer-p1a-exact4-revision-scope.v1'),('b','researchos.installer-p1a-exact2-scope-admission-revision.v1')]:
 art=scratch/('art-'+tag);rec=scratch/('receipts-'+tag);art.mkdir();rec.mkdir()
 doc={'schema':schema,'owner':b.SCOPE_OWNER,'worktree':str(W),'artifact_root':str(art),'receipt_root':str(rec)}
 raw=b.encode(doc);path=R/('trusted-'+tag+'.json');path.write_bytes(raw);pin=hashlib.sha256(raw).hexdigest()
 actual=b.bound_roots(str(path),pin);assert actual==(str(art),str(rec));positive.append({'scope':path.name,'external_fixture_pin':pin,'selected_roots':actual})
 if tag=='a':
  duplicate=R/'trusted-a-another-location.json';duplicate.write_bytes(raw);assert b.bound_roots(str(duplicate),pin)==actual
  source=scratch/'source';source.mkdir();base_doc=doc;artifact=art;receipts=rec
negative=[]
variants=[('empty-pin',base_doc,''),('bad-pin',base_doc,'0'*64),('wrong-schema',{**base_doc,'schema':'unrecognized'},None),('wrong-owner',{**base_doc,'owner':'other'},None),('wrong-worktree',{**base_doc,'worktree':str(R)},None),('missing-root',{k:v for k,v in base_doc.items() if k!='artifact_root'},None),('nonstring-root',{**base_doc,'receipt_root':1},None),('dotdot-root',{**base_doc,'artifact_root':str(artifact/'..'/'escape')},None),('overlap-roots',{**base_doc,'receipt_root':str(artifact)},None),('absent-root',{**base_doc,'artifact_root':str(scratch/'absent')},None)]
for tag,doc,pin in variants:
 path=R/(tag+'.json');raw=b.encode(doc);path.write_bytes(raw);pin=pin if pin is not None else hashlib.sha256(raw).hexdigest()
 args=SimpleNamespace(scope=str(path),scope_sha256=pin,candidate=str(source),output=str(artifact/'candidate'),receipts=str(receipts/'run'),go=locked['go']['path'])
 try:b.build(args);raise AssertionError('accepted '+tag)
 except (ValueError,FileNotFoundError) as e:
  assert not b.write_owned_failure(args,e);assert not list(artifact.iterdir()) and not list(receipts.iterdir());negative.append({'case':tag,'error':str(e),'writes':0})
# Verify hash comparison precedes JSON interpretation even for malformed bytes.
bad=R/'invalid-json.json';bad.write_bytes(b'{not json')
try:b.bound_roots(str(bad),'0'*64);raise AssertionError('bad scope accepted')
except ValueError as e:assert str(e)=='scope bytes differ from external SHA-256 pin';negative.append({'case':'hash-before-json','error':str(e),'writes':0})
# CLI admission has no hidden hardcoded scope path; a valid fixture scope reaches source validation.
cli=run('explicit-scope-cli',[locked['python']['path'],'-B',W/'ops/release/product_installer/build.py','--candidate',source,'--output',artifact/'candidate','--receipts',receipts/'run','--go',locked['go']['path'],'--scope',R/'trusted-a.json','--scope-sha256',positive[0]['external_fixture_pin']])
assert cli.returncode==1 and b'installed-product.json' in cli.stderr and b'scope' not in cli.stderr.lower();assert not list(artifact.iterdir()) and not list(receipts.iterdir())
missing=run('missing-pin-cli',[locked['python']['path'],'-B',W/'ops/release/product_installer/build.py','--candidate',source,'--output',artifact/'candidate','--receipts',receipts/'run','--go',locked['go']['path'],'--scope',R/'trusted-a.json'])
assert missing.returncode==2 and b'--scope-sha256' in missing.stderr;assert not list(artifact.iterdir()) and not list(receipts.iterdir())
art=pathlib.Path(a['artifact']);prior=json.loads((author.parent.parent/'revision01/FINAL-MANIFEST.json').read_bytes());refs=[]
for filename,key in [('payload-manifest.json','payload_manifest_sha256'),('finalizer.exe','finalizer_sha256')]:
 actual=sha(art/filename);assert actual==a[key]==prior[key];refs.append({'path':str(art/filename),'sha256':actual,'same_as_revision01':True})
build_result=author.parent/'build01/result.json';build_exit=author.parent/'build01-exit.json';save('author-build-refs.json',{'files':[{'path':str(p),'sha256':sha(p),'content':json.loads(p.read_bytes())} for p in [build_result,build_exit]],'independent_build_repeated':False})
save('observations.json',{'status':'PASS_TARGETED_SCOPE_ADMISSION','positive_scopes':positive,'same_bytes_new_path_accepted':True,'negative_cases':negative,'valid_cli_reached_frozen_source_validation_without_writes':True,'missing_pin_cli_exit':missing.returncode,'r2_r3_regressions':'PASS in 7 Python tests including junction and byte-preserving existing receipts','unchanged_artifacts':refs,'product_native_runs':0,'full_go_suite_repeated':False,'payload_copy_or_relocation_repeated':False})
print('PASS: R4 independent admission; R2/R3 regressions; immutable references')
