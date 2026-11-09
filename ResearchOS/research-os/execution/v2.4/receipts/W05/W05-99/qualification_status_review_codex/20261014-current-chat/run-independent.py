import pathlib,json,subprocess,os,hashlib,datetime,shutil,sys
R=pathlib.Path(__file__).resolve().parent
S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
C='5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456';B='c465d1356480d6e6a90da84656724f9fc02b31c7';T='bfade6fd49897f53e2ec629c71691405be2f2fbe'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
 p=subprocess.run(['git',*args],cwd=S,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError({'args':args,'exit':p.returncode,'stderr':p.stderr.decode('utf8')})
 return p.stdout
assert git('rev-parse','HEAD').decode().strip()==C
assert git('rev-parse','HEAD^{tree}').decode().strip()==T
assert git('status','--porcelain=v1')==b''
assert git('rev-parse',C+'^').decode().strip()==B
scope=json.loads((R/'cp456-source-scope.json').read_text(encoding='utf-8-sig'))
assert sorted(git('diff','--name-only',B,C).decode().splitlines())==sorted(scope['paths'])
F=S/'.local/final';manifest=json.loads((F/'manifest.json').read_text(encoding='utf-8-sig'))
assert h(F/'manifest.json')=='a0b173943c70387628c36396c601ff4d49b30c880be3495421fbf8a77faa7c6e'
assert h(F/'REPORT.md')=='2a738acb96027176ad1a2905ed058432f8a65715c9481a9cf1c66694e32b98ba'
checks=[]
for e in manifest['files']:
 p=(F/e['path']).resolve();assert p.is_relative_to(F.resolve());assert p.stat().st_size==e['bytes'] and h(p)==e['sha256'];checks.append(e)
census=json.loads((F/'input-census.json').read_text(encoding='utf-8-sig'))
for e in census['candidate_inputs']:
 p=S/e['path'];assert p.stat().st_size==e['bytes'] and h(p)==e['sha256']
node=pathlib.Path(census['node']['path']);assert h(node)==census['node']['sha256']
expected={e['path']:e['sha256'] for e in census['candidate_inputs'] if e['path'].startswith('apps/desktop/main/lib/')}
(R/'source-bind-expected.json').write_text(json.dumps(expected,indent=2),encoding='utf8')
(R/'inputs').mkdir(exist_ok=True)
for name in ['manifest.json','REPORT.md','input-census.json','commands.json','source.patch','web-dependencies-census.json']:
 shutil.copyfile(F/name,R/'inputs'/name)
(R/'candidate.diff').write_bytes(git('diff','--no-ext-diff','--binary',B,C,'--',*scope['paths']))
state={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_root':str(S),'head':C,'tree':T,'base':B,'changed_paths':scope['paths'],'working_tree_clean':True,'author_manifest_members_verified':len(checks),'source_inputs_verified':len(census['candidate_inputs']),'node':census['node'],'gitdir':git('rev-parse','--absolute-git-dir').decode().strip(),'common_dir':git('rev-parse','--git-common-dir').decode().strip(),'metadata_probe_note':'Initial PowerShell unquoted HEAD^{tree} parsed incorrectly; superseded by this successful subprocess argv probe; no repository change.'}
(R/'input-validation.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
env=os.environ.copy();env['REVIEW_SOURCE_ROOT']=str(S);env['REVIEW_BIND_LOG']=str(R/'source-bind');env['REVIEW_BIND_EXPECTED']=str(R/'source-bind-expected.json')
tmp=R/'fixture-temp';tmp.mkdir(exist_ok=True);env['TEMP']=str(tmp);env['TMP']=str(tmp)
argv=[str(node),'--require',str(R/'source-bind.cjs'),'--test','--test-reporter=tap',*[str(S/p) for p in scope['paths'] if p.endswith('.test.mjs')]]
(R/'test-command.json').write_text(json.dumps({'argv':argv,'cwd':str(S),'temp':str(tmp),'source_binding':'preloaded require resolver enforces source root and captured file hash'},ensure_ascii=False,indent=2),encoding='utf8')
with (R/'tests.raw.txt').open('xb') as stream:
 p=subprocess.run(argv,cwd=S,env=env,stdout=stream,stderr=subprocess.STDOUT)
(R/'tests.exit.json').write_text(json.dumps({'native_exit':p.returncode}),encoding='utf8')
assert git('status','--porcelain=v1')==b''
for e in census['candidate_inputs']:assert h(S/e['path'])==e['sha256']
state['post_test_source_inputs_unchanged']=True;state['post_test_worktree_clean']=True;state['remaining_temp_entries']=[str(p.relative_to(tmp)) for p in tmp.rglob('*')]
(R/'post-test-validation.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
if not any(tmp.iterdir()):tmp.rmdir()
print(json.dumps({'test_native_exit':p.returncode,'metadata':'verified','source_inputs':len(census['candidate_inputs']),'manifest_members':len(checks)}))
sys.exit(p.returncode)
