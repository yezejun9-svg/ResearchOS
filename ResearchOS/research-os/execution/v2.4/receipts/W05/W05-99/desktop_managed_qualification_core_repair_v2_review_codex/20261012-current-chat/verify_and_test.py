from pathlib import Path
import pathlib, subprocess, hashlib, json, os, datetime, sys
OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[6]
WT = ROOT / '.local/worktrees/w05-desktop-managed-qualification-core-repair-v2-20261012'
AUTHOR = ROOT / 'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_core_repair_v2_codex/20261012-current-chat'
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
ASSETS = ROOT / '.local/builds/current-chat-runtime-assets-20261012'
CACHE = ROOT / 'execution/v2.4/receipts/W05/W05-99/normal_runtime_host_setup_review_codex/20261012-current-chat/cache'
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], cwd=WT, text=True).strip()
env = dict(os.environ)
for path in [OUT/'cache/go-tmp',OUT/'cache/test-temp']: path.mkdir(parents=True,exist_ok=True)
settings = {'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOPATH':str(ROOT/'.local/tools/gopath'),'GOMODCACHE':str(ROOT/'.local/tools/gopath/pkg/mod'),'GOCACHE':str(CACHE/'go-cache'),'GOTMPDIR':str(OUT/'cache/go-tmp'),'TEMP':str(OUT/'cache/test-temp'),'TMP':str(OUT/'cache/test-temp'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_MU_BUNDLE':str(ASSETS/'mu-worker.mjs'),'PATH':str(ASSETS)+os.pathsep+env.get('PATH','')}
env.update(settings)
frozen = AUTHOR/'source-bundle-final.json'
assert digest(frozen) == '7d4ce0372f6ce7e469e76cf052d5446ab205e6292bbd7d0df19f0cbfc0444d16'
bundle = json.loads(frozen.read_text(encoding='utf-8'))
assert git('rev-parse','HEAD') == bundle['candidate_commit']
assert git('rev-parse','HEAD^') == bundle['parent_commit']
assert not git('status','--porcelain')
assert set(git('diff','--name-only',bundle['parent_commit'],'HEAD').splitlines()) == {v['path'] for v in bundle['source_delta']}
checks=[]
assert set(git('diff','--name-only',bundle['cumulative_base_commit'],'HEAD').splitlines()) == {v['path'] for v in bundle['cumulative_source']}
for item in bundle['frozen_inputs']:
    assert digest(ROOT/item['path'])==item['sha256']
    checks.append({'kind':'frozen_input','path':item['path'],'sha256':item['sha256']})
for item in bundle['cumulative_source']:
    path=WT/item['path']; assert digest(path)==item['sha256'] and path.stat().st_size==item['bytes']
    committed=subprocess.check_output(['git','show','HEAD:'+item['path']],cwd=WT)
    assert hashlib.sha256(committed).hexdigest()==item['sha256']
    checks.append({'kind':'source_and_git','path':item['path'],'sha256':item['sha256']})
for item in bundle['evidence']:
    assert digest(AUTHOR/item['path'])==item['sha256']
    checks.append({'kind':'author_evidence','path':item['path'],'sha256':item['sha256']})
for item in bundle['binaries']:
    path=pathlib.Path(item['path']); assert digest(path)==item['sha256']
    info=subprocess.check_output([str(GO),'version','-m',str(path)],env=env,text=True)
    assert 'vcs.revision='+bundle['candidate_commit'] in info and 'vcs.modified=false' in info
    checks.append({'kind':'binary_metadata','path':str(path),'sha256':item['sha256'],'go_version_m':info})
(OUT/'source_verification.json').write_text(json.dumps({'candidate':bundle['candidate_commit'],'frozen_sha256':digest(frozen),'checks':checks,'passed':len(checks)},indent=2)+'\n',encoding='utf-8')
print('SOURCE_VERIFIED',len(checks),flush=True)
names=[x['Test'] for x in json.loads((AUTHOR/'attempt10-frozen-domain.summary.json').read_text(encoding='utf-8')) if x.get('Action')=='pass' and 'Test' in x and '/' not in x['Test']]
overlay=OUT/'old-review-overlay.json'
original=ROOT/'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_core_review_codex/20261012-current-chat/reviewer_shutdown_fence_windows_test.go'
assert digest(original)==bundle['review_overlay']['sha256']
(OUT/'original-reviewer-tests.go').write_bytes(original.read_bytes())
overlay.write_text(json.dumps({'Replace':{str(WT/'internal/domain/reviewer_shutdown_fence_windows_test.go'):str(OUT/'original-reviewer-tests.go')}},indent=2),encoding='utf-8')
cases=[('original-overlay',['-overlay='+str(overlay),'./internal/domain','-run','^TestReviewer']),('domain',['./internal/domain','-run','^('+'|'.join(names)+ '|TestRuntimeMuUnknownNeverRetries|TestRuntimeMuLocalModelDoesNotForwardSDKOrBrokerHeaders)$']),('verifier',['./internal/verifier']),('host',['./internal/host','-run','^(TestDesktopManagementStrictFrames|TestDesktopManagementActualParentIdentityAndPipeOnly|TestManagedRequestFilePrivateACLAndStrictJSON|TestDesktopManagementActualControlLifecycle|TestDesktopManagementSyntheticQualification|TestDesktopManagementLostReplySettlesOriginalEffect|TestManagedLocalQualificationRootRevocation)$','-args','-local-runtime-assets-dir='+str(ASSETS),'-local-runtime-verifier-executable='+next(v['path'] for v in bundle['binaries'] if Path(v['path']).name=='runtime-verifier.exe'),'-local-runtime-control-executable='+next(v['path'] for v in bundle['binaries'] if Path(v['path']).name=='researchos-control.exe')])]
for name,args in cases:
    argv=[str(GO),'test','-mod=readonly','-count=1','-json','-timeout=240s']+args
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result=subprocess.run(argv,cwd=WT,env=env,capture_output=True,timeout=300)
    (OUT/(name+'.stdout')).write_bytes(result.stdout); (OUT/(name+'.stderr')).write_bytes(result.stderr)
    (OUT/(name+'.invocation.json')).write_text(json.dumps({'argv':argv,'cwd':str(WT),'started':start,'ended':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':result.returncode,'environment':settings,'real_model_calls':0},indent=2)+'\n',encoding='utf-8')
    events=[]
    for line in result.stdout.splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    terminal=[{k:e[k] for k in ['Action','Package','Test','Elapsed'] if k in e} for e in events if e.get('Action') in ['pass','fail','skip']]
    (OUT/(name+'.summary.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'case':name,'exit':result.returncode,'parents':sum(x.get('Action')=='pass' and 'Test' in x and '/' not in x['Test'] for x in terminal),'subtests':sum(x.get('Action')=='pass' and 'Test' in x and '/' in x['Test'] for x in terminal),'fail_skips':[x for x in terminal if x.get('Action') in ['fail','skip']]}),flush=True)
    if result.returncode: sys.exit(result.returncode)
