import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys
E=pathlib.Path(__file__).parent
W=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/mu-m1-second-pause-20261014')
A=E.parent.parent.parent/'mu_m1_02_second_pause_source_codex/20261014-current-chat'
HEAD='36b2634bfebe6201a14b7661f2dce32b7f1a5098'
TREE='bea72c5cdbb341e4d67bd91331803ec6e8013e3b'
BASE='ff5ac2047566a52388188b84f267217d8582c571'
S=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp483/mu-m1-second-pause-source-scope-v3.json')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def git(*args):return subprocess.check_output(['git',*args],cwd=W).decode('utf-8').strip()
def guards():
    assert git('rev-parse','HEAD')==HEAD
    assert git('rev-parse','HEAD^{tree}')==TREE
    assert git('status','--porcelain')==''
    m=read(A/'source-manifest.json');sources=[]
    assert sorted(git('diff','--name-only',BASE,'HEAD').splitlines())==sorted(x['path'] for x in m['source_files'])
    for x in m['source_files']:
        p=pin(W/x['path']);assert p['sha256']==x['sha256'];sources.append(p)
    return dict(head=HEAD,tree=TREE,base=BASE,clean=True,sources=sources)
def audit():
    assert pin(A/'source-manifest.json')['sha256']=='b1b58c12a003dbe39395c632cedae3e100a2eefbf5bf7bf0eedd9b8ff9c59556'
    assert pin(A/'attempt-ledger.json')['sha256']=='8d950ba5f7d3548ee7ad58c175e2f6788ce8b31c88882a8564b50078d242ad14'
    assert pin(S)['sha256']=='1f418aac77ee33a0f75d91defd9466dcd961c9e0ca869319d653f7f8d6adb957'
    inputs=[];m=read(A/'source-manifest.json')
    for x in m['key_artifacts']:
        p=pin(A/x['path']);assert p['sha256']==x['sha256'];inputs.append(p)
    ledger=read(A/'attempt-ledger.json')
    for a in ledger['attempts']:
        for filename,key in [('stdout.jsonl','stdout_sha256'),('stderr.raw','stderr_sha256'),('exit.txt','exit_sha256')]:
            p=pin(A/a['id']/filename);assert p['sha256']==a[key];inputs.append(p)
        for item in a['native_artifacts']:
            p=pin(A/item['path']);assert p['sha256']==item['sha256'];inputs.append(p)
    source=guards()
    assert len(source['sources'])==9
    for item in source['sources']:
        p=pathlib.Path(item['path']);target=E/'source-snapshot'/p.relative_to(W);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    (E/'source.patch').write_bytes(subprocess.check_output(['git','diff','--binary',BASE,'HEAD'],cwd=W))
    write(E/'input-verification.json',dict(source=source,scope=pin(S),author_source_manifest=pin(A/'source-manifest.json'),author_attempt_ledger=pin(A/'attempt-ledger.json'),verified_author_inputs=inputs))
    print(json.dumps(dict(source_files=9,verified_author_inputs=len(inputs),free_bytes=shutil.disk_usage(W).free)))
def run(name,args):
    d=E/name;d.mkdir();write(d/'source-before.json',guards())
    tool=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go')
    temp='D:/作品集/ResearchOS/research-os/.local/go-tmp/mu-m1-review'
    cfg=dict(GOROOT=str(tool),GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',GOCACHE='D:/作品集/ResearchOS/research-os/.local/go-cache/mu-m1-core-20261014',GOTMPDIR=temp,TEMP=temp,TMP=temp,GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOWORK='off')
    argv=[str(tool/'bin/go.exe'),*args];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (d/'stdout.jsonl').open('wb') as out,(d/'stderr.raw').open('wb') as err:p=subprocess.run(argv,cwd=W,env=dict(os.environ,**cfg),stdout=out,stderr=err)
    events=[]
    for line in (d/'stdout.jsonl').read_text(encoding='utf-8',errors='replace').splitlines():
        try:row=json.loads(line)
        except json.JSONDecodeError:continue
        if row.get('Test') and row.get('Action') in ['pass','fail','skip']:events.append(dict(test=row['Test'],action=row['Action']))
    command=dict(argv=argv,cwd=str(W),allowlist_environment=cfg,started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=p.returncode,stdout=pin(d/'stdout.jsonl'),stderr=pin(d/'stderr.raw'),test_results=events)
    write(d/'command.json',command);write(d/'source-after.json',guards())
    lp=E/'attempt-ledger.json';ledger=read(lp) if lp.exists() else dict(attempts=[],failed_attempt_count=0)
    ledger['attempts'].append(dict(name=name,exit=p.returncode,command=pin(d/'command.json'),top_level_results=[x for x in events if '/' not in x['test']]))
    if p.returncode:ledger['failed_attempt_count']+=1
    write(lp,ledger)
    print(json.dumps(dict(name=name,exit=p.returncode,tests=[x for x in events if '/' not in x['test']]),ensure_ascii=True))
    print((d/'stdout.jsonl').read_text(encoding='utf-8',errors='replace')[-1800:]);print((d/'stderr.raw').read_text(encoding='utf-8',errors='replace')[-1800:]);sys.exit(p.returncode)
if __name__=='__main__':
    if sys.argv[1]=='audit':audit()
    else:run(sys.argv[1],sys.argv[2:])
