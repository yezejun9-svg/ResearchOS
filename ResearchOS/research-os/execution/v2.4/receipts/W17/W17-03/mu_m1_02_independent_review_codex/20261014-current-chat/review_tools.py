import datetime, hashlib, json, os, pathlib, shutil, subprocess, sys
E=pathlib.Path(__file__).parent
W=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-core-20261014')
A=E.parent.parent/'mu_m1_02_author_codex/20261014-current-chat'
S=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp473/mu-m1-02-source-scope-v4.json')
HEAD='ff5ac2047566a52388188b84f267217d8582c571'
TREE='e5792b72e0380af65fa1cc5f8b122399c1366d9b'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj): p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def pin(p): return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def git(*args): return subprocess.run(['git',*args],cwd=W,capture_output=True,check=True).stdout
def guards():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('rev-parse','HEAD^{tree}').decode().strip()==TREE
    assert not git('status','--porcelain')
    scope=read(S); manifest=read(A/'source-manifest.json')
    assert sorted(git('diff','--name-only',scope['base_commit'],'HEAD').decode().splitlines())==sorted(scope['paths'])
    for p in manifest['sources']+manifest['frozen_dependencies_unchanged']:
        actual=pin(pathlib.Path(p['path'])); assert actual['sha256']==p['sha256'] and actual['bytes']==p['bytes'],p['path']
    return dict(head=HEAD,tree=TREE,clean=True,sources=manifest['sources'],dependencies=manifest['frozen_dependencies_unchanged'])
def audit():
    assert pin(S)['sha256']=='a3717a29e1b236e790cc5d639adf2603ddb0935c8307164f2fc2af9654b1e1f5'
    assert pin(A/'evidence-manifest.json')['sha256']=='2734959da15fcb48765ae5d62b6e782a096cb2b930ec37e5b592743eb4af0193'
    evidence=read(A/'evidence-manifest.json')
    for member in evidence['files']:
        actual=pin(A/member['path']); assert actual['sha256']==member['sha256'] and actual['bytes']==member['bytes'],member['path']
    data=guards(); data['author_evidence_members']=len(evidence['files']);data['author_manifest']=pin(A/'evidence-manifest.json');data['scope']=pin(S)
    for item in data['sources']:
        dest=E/'source-snapshot'/item['repo_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(item['path'],dest)
    (E/'source.patch').write_bytes(git('diff','--binary',read(S)['base_commit'],'HEAD'))
    write(E/'input-verification.json',data)
    print(json.dumps(dict(source_count=len(data['sources']),author_members=data['author_evidence_members']),ensure_ascii=True))
def run(name,args):
    C=E/name;C.mkdir();write(C/'source-before.json',guards())
    tool=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go')
    temp=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/go-tmp/mu-m1-review');temp.mkdir(exist_ok=True)
    cfg=dict(GOROOT=str(tool),GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',GOCACHE='D:/作品集/ResearchOS/research-os/.local/go-cache/mu-m1-core-20261014',GOTMPDIR=str(temp),TEMP=str(temp),TMP=str(temp),GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOWORK='off')
    if name == '05-native-queue':
        assets='C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01'
        cfg['RESEARCHOS_MU_BUNDLE']=assets+'/mu-worker.mjs'
        cfg['PATH']=assets+os.pathsep+os.environ['PATH']
    env=dict(os.environ,**cfg);argv=[str(tool/'bin/go.exe'),*args]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (C/'stdout.jsonl').open('wb') as out,(C/'stderr.raw').open('wb') as err:
        proc=subprocess.run(argv,cwd=W,env=env,stdout=out,stderr=err)
    command=dict(argv=argv,cwd=str(W),environment=cfg,started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit=proc.returncode,stdout=pin(C/'stdout.jsonl'),stderr=pin(C/'stderr.raw'))
    write(C/'command.json',command);write(C/'source-after.json',guards())
    ledgerfile=E/'review-ledger.json'; ledger=read(ledgerfile) if ledgerfile.exists() else dict(attempts=[],failed_attempt_count=0)
    ledger['attempts'].append(dict(name=name,exit=proc.returncode,command=pin(C/'command.json')))
    if proc.returncode: ledger['failed_attempt_count']+=1
    write(ledgerfile,ledger)
    print(json.dumps(command,ensure_ascii=True))
    print((C/'stderr.raw').read_text(encoding='utf-8',errors='replace')[-1500:])
    print((C/'stdout.jsonl').read_text(encoding='utf-8',errors='replace')[-2000:])
    sys.exit(proc.returncode)
if __name__=='__main__':
    if sys.argv[1]=='audit': audit()
    else: run(sys.argv[1],sys.argv[2:])
