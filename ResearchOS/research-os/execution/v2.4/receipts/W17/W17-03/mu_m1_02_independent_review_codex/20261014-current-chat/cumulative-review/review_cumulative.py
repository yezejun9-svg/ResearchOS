import datetime,hashlib,json,os,pathlib,subprocess,sys
E=pathlib.Path(__file__).parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/mu-m1-second-pause-20261014'
I=E.parent
A=R/'execution/v2.4/receipts/W17/W17-03/mu_m1_02_author_codex/20261014-current-chat'
B=R/'execution/v2.4/receipts/W17/W17-03/mu_m1_02_second_pause_source_codex/20261014-current-chat'
BASE='60f8c81a7529081eb51d525ab913d63102148a46'
FIRST='ff5ac2047566a52388188b84f267217d8582c571'
SECOND='36b2634bfebe6201a14b7661f2dce32b7f1a5098'
HEAD='8f50cb57ff821554aef17e9a9bd5208935489d50'
TREE='361ead86ee812d5e040fe1d2cde2a92297eb639f'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def git(*args):return subprocess.check_output(['git',*args],cwd=W)
def names(a,b):return git('diff','--name-only',a,b).decode().splitlines()
def guards():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('rev-parse','HEAD^{tree}').decode().strip()==TREE
    assert git('status','--porcelain')==b''
    sources=[]
    for p in names(BASE,HEAD):
        item=pin(W/p)
        assert item['sha256']==hashlib.sha256(git('show',HEAD+':'+p)).hexdigest(),p
        sources.append(dict(repo_path=p,**item))
    return dict(base=BASE,base_tree=git('rev-parse',BASE+'^{tree}').decode().strip(),head=HEAD,tree=TREE,clean=True,sources=sources)
def audit():
    manifests=[read(A/'source-manifest.json'),read(B/'source-manifest.json'),read(B/'revision02/source-manifest.json')]
    stage_sources=[manifests[0]['sources'],manifests[1]['source_files'],manifests[2]['source_files']]
    stages=[];pins=[]
    for start,end,sources,mf,expected in zip([BASE,FIRST,SECOND],[FIRST,SECOND,HEAD],stage_sources,[A/'source-manifest.json',B/'source-manifest.json',B/'revision02/source-manifest.json'],[17,9,2]):
        files=[x.get('repo_path',x['path']) for x in sources]
        assert sorted(files)==sorted(names(start,end)) and len(files)==expected
        for item,path in zip(sources,files):
            assert hashlib.sha256(git('show',end+':'+path)).hexdigest()==item['sha256'],path
        scope_ref=read(mf)['scope'];scope_path=pathlib.Path(scope_ref['path'])
        assert pin(scope_path)['sha256']==scope_ref['sha256']
        scope=read(scope_path)
        allowed=scope.get('allowed_source_files',scope.get('paths'))
        assert sorted(files)==sorted(allowed)
        stages.append(dict(base=start,head=end,tree=git('rev-parse',end+'^{tree}').decode().strip(),files=files,manifest=pin(mf),scope=pin(scope_path),requirements=scope['requirements']))
        for key,item in scope.items():
            if isinstance(item,dict) and 'path' in item and 'sha256' in item:
                p=pathlib.Path(item['path']);p=p if p.is_absolute() else R/p
                actual=pin(p);assert actual['sha256']==item['sha256'],str(p);pins.append(actual)
    union=set().union(*(s['files'] for s in stages))
    assert sorted(union)==sorted(names(BASE,HEAD)) and len(union)==21
    deps=[]
    for item in read(pathlib.Path(manifests[0]['scope']['path']))['dependency_source9']:
        p=W/item['path'];actual=pin(p);assert actual['sha256']==item['sha256']
        assert git('show',BASE+':'+item['path'])==git('show',HEAD+':'+item['path']);deps.append(actual)
    checked_manifests=[]
    for folder in [A,I,I/'architecture-followup',I/'architecture-budget-followup',I/'second-pause-revision01',I/'second-pause-revision02']:
        mp=folder/'evidence-manifest.json';count=0
        for item in read(mp)['files']:
            p=pathlib.Path(item['path']);p=p if p.is_absolute() else folder/p
            actual=pin(p);assert actual['sha256']==item['sha256'],str(p)
            if 'bytes' in item:assert actual['bytes']==item['bytes']
            count+=1
        checked_manifests.append(dict(manifest=pin(mp),members_verified=count))
    preserved=[pin(A/'attempt-ledger.json'),pin(B/'attempt-ledger.json'),pin(B/'revision02/attempt-ledger.json'),pin(I/'review-ledger.json'),pin(I/'second-pause-revision01/attempt-ledger.json'),pin(I/'second-pause-revision02/attempt-ledger.json'),pin(I/'second-pause-revision02/attempt-ledger-resume.json')]
    unchanged=[p for p in stages[0]['files'] if p not in set(stages[1]['files'])]
    for p in unchanged:assert git('show',FIRST+':'+p)==git('show',HEAD+':'+p)
    source=guards()
    (E/'cumulative-source.patch').write_bytes(git('diff','--binary',BASE,HEAD))
    write(E/'current-inputs.json',dict(source=source,stages=stages,cumulative_unique_files=21,stage17_9_overlap=5,unchanged_original_files=unchanged,dependencies=deps,verified_contract_refs=pins,verified_manifests=checked_manifests,preserved_ledgers=preserved,source_patch=pin(E/'cumulative-source.patch'),runtime_inputs=read(I/'second-pause-revision02/runtime-inputs.json'),formal_increment=0))
    print(json.dumps(dict(cumulative_files=21,unchanged_original_files=len(unchanged),frozen_dependencies=len(deps),verified_manifest_members=sum(x['members_verified'] for x in checked_manifests))))
def run():
    d=E/'01-current-native-queue';d.mkdir();write(d/'source-before.json',guards())
    old=read(I/'05-native-queue/command.json')
    cfg=old['environment'];assets='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01'
    cfg['PATH']=assets+os.pathsep+os.environ['PATH']
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (d/'stdout.jsonl').open('wb') as out,(d/'stderr.raw').open('wb') as err:
        proc=subprocess.run(old['argv'],cwd=W,env=dict(os.environ,**cfg),stdout=out,stderr=err)
    events=[]
    for line in (d/'stdout.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if row.get('Test') and row['Action'] in ['pass','fail','skip']:events.append(dict(test=row['Test'],action=row['Action']))
    write(d/'command.json',dict(argv=old['argv'],cwd=str(W),environment={k:v for k,v in cfg.items() if k!='PATH'},path_policy='frozen public M1 assets prepended to inherited PATH',started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=proc.returncode,stdout=pin(d/'stdout.jsonl'),stderr=pin(d/'stderr.raw'),test_results=events))
    write(d/'source-after.json',guards())
    write(E/'attempt-ledger.json',dict(attempts=[dict(name=d.name,exit=proc.returncode,command=pin(d/'command.json'),results=events)],failed_attempt_count=int(proc.returncode!=0),classification='ADDITIONAL_CURRENT_HEAD_INTEGRATION_PROOF_NOT_RECOUNT_OF_REUSED_ATTEMPTS'))
    print(json.dumps(dict(exit=proc.returncode,results=events)))
    sys.exit(proc.returncode)
if __name__=='__main__':
    audit() if sys.argv[1]=='audit' else run()
