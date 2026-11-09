import collections,datetime,hashlib,json,pathlib,subprocess

receipt=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
work=repo/'.local/worktrees/verifier-replacement-20261014'
def git(*args):
    return subprocess.check_output(['git',*args],cwd=work)
def digest(p):
    raw=p.read_bytes()
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
scope=json.loads((repo/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp484/runtime-verifier-replacement-source-scope.json').read_text('utf-8'))
head=git('rev-parse','HEAD').decode().strip()
changed=git('diff','--name-only',scope['base_commit'],head).decode().splitlines()
assert sorted(changed)==sorted(scope['allowed_source_files'])
assert not git('status','--porcelain=v1').strip()
patch=git('diff','--binary','--full-index',scope['base_commit'],head)
(receipt/'source.patch').write_bytes(patch)
tests={}
for filename in ['08-control-host-regression.log','09-final-focused.log','11-managed-synthetic.log','12-domain-managed.log','14-final-regression.log']:
    events=[]
    for line in (receipt/filename).read_text('utf-8').splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    counts=collections.Counter(e['Action'] for e in events if e.get('Test') and '/' not in e['Test'] and e['Action'] in ['pass','fail','skip'])
    allcounts=collections.Counter(e['Action'] for e in events if e.get('Test') and e['Action'] in ['pass','fail','skip'])
    tests[filename]={'top_level':dict(counts),'including_subtests':dict(allcounts),'skips':[e['Test'] for e in events if e['Action']=='skip'],'failures':[e.get('Test','PACKAGE') for e in events if e['Action']=='fail']}
early=[{'ordinal':1,'kind':'compile-setup-failure','exit_code':1,'argv':['go','test','./internal/host','./apps/control','-run','^TestRuntimeVerifierReplacement','-count=1'],'cwd':str(work),'observed_error':'Sparse checkout omitted evaluation/holdout/jev, evaluation/evolution, evaluation/skills; missing module packages. Expanded only build inputs.','evidence_level':'tool transcript; not acceptance test, no standalone raw log was saved'}, {'ordinal':2,'kind':'compile-failure','exit_code':1,'argv':['go','test','./internal/host','./apps/control','-run','^TestRuntimeVerifierReplacement','-count=1'],'cwd':str(work),'observed_error':'undefined: windows.FILE_ALL_ACCESS; corrected to the actual FILE_ALL_ACCESS mask 0x001f01ff.','evidence_level':'tool transcript; not acceptance test, no standalone raw log was saved'}]
(receipt/'EARLY-FAILURES.json').write_text(json.dumps(early,ensure_ascii=False,indent=2),'utf-8')
summary={'schema':'researchos.runtime-verifier-replacement-source-evidence/1','state':'CANDIDATE_FOR_INDEPENDENT_REVIEW','source_commit':head,'source_tree':git('rev-parse','HEAD^{tree}').decode().strip(),'base_commit':scope['base_commit'],'base_tree':scope['base_tree'],'scope_exact_files':changed,'tests':tests,'formal_increment':0,'remaining_verification':['Native foreign-owner rejection test SKIP: token lacks WRITE_OWNER; current owner, null/inherited/extra DACL negatives executed.','Seven managed Mu synthetic leaf cases failed because provided M1 candidate build metadata is not the legacy LoadRuntimeSetupAssets contract; no metadata altered.','Non-Windows dispatcher exact-source harness executed on Windows; entire non-Windows control build is already unsupported by baseline Windows-only DataRootLease.','Real Windows process termination is covered; power loss/storage hardware durability is not claimed.'],'observed_failures_preserved':['EARLY-FAILURES.json','03-host-focused.log','05-focused-all.log','06-race-diagnostic.log','11-managed-synthetic.log'],'product_execution':False,'acceptance_authority':'independent reviewer only'}
(receipt/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
manifest={'schema':'researchos.runtime-verifier-replacement-source-manifest/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':head,'source_tree':summary['source_tree'],'base_commit':scope['base_commit'],'base_tree':scope['base_tree'],'source_files':{name:digest(work/name) for name in changed},'diff':digest(receipt/'source.patch'),'go':digest(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'control_fixture_binary':{'path':str(repo/'.local/tmp/verifier-replacement-20261014/control-final.exe'),**digest(repo/'.local/tmp/verifier-replacement-20261014/control-final.exe')},'receipt_files':{p.name:digest(p) for p in sorted(receipt.iterdir()) if p.is_file() and p.name!='FINAL-manifest.json'},'formal_increment':0}
(receipt/'FINAL-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'commit':head,'tree':summary['source_tree'],'diff':manifest['diff'],'manifest':digest(receipt/'FINAL-manifest.json'),'tests':tests},ensure_ascii=False,indent=2))
