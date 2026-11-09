import os, json, hashlib, subprocess, pathlib, datetime, sys
ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
E = pathlib.Path(__file__).parent
SOURCE = ROOT / 'execution/v2.4/receipts/W05/W05-99/qualification_projection_a_source_codex/20261015-current-chat'
CAND = ROOT / '.local/worktrees/qualification-projection-a-20261015'
BASE = ROOT / '.local/worktrees/verifier-replacement-20261014'
TEMP = ROOT / '.local/qualification-projection-independent-review-20261015'
GO = str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(name, value): (E/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(name, argv, cwd, env=None):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (E/(name+'.raw')).open('wb') as out:
        p=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
    record={'argv':argv,'cwd':str(cwd),'env_allowlist':{k:env[k] for k in ('GOCACHE','GOPATH','GOTMPDIR','TMP','TEMP','RESEARCHOS_MU_BUNDLE') if env and k in env},'native_exit':p.returncode,'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw':name+'.raw','raw_sha256':sha(E/(name+'.raw'))}
    save(name+'.command.json',record)
    with (E/'diagnostic-ledger.jsonl').open('a',encoding='utf-8') as out: out.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(name,p.returncode,flush=True)
    return (E/(name+'.raw')).read_bytes()
def git(cwd,*args): return subprocess.check_output(['git','--no-optional-locks',*args],cwd=cwd).decode('utf-8').strip()
def guards(label):
    rows={}
    for name,cwd in [('main',ROOT),('candidate',CAND),('base',BASE)]:
        raw=run(label+'-'+name+'-status',['git','--no-optional-locks','status','--porcelain=v1','-uno'],cwd)
        files=git(cwd,'diff','--name-only').splitlines()
        rows[name]={'head':git(cwd,'rev-parse','HEAD'),'tree':git(cwd,'rev-parse','HEAD^{tree}'),'index':git(cwd,'diff','--cached','--name-only'),'status':raw.decode('utf-8'),'dirty_hashes':{f:sha(cwd/f) for f in files if (cwd/f).is_file()}}
    bundle=ROOT/'.local/builds/current-chat-runtime-assets-20261012/mu-worker.mjs'
    rows['bundle']={'path':str(bundle),'sha256':sha(bundle)}
    save(label+'-guards.json',rows)
if __name__ == '__main__':
    for sub in ('tmp','cache'): (TEMP/sub).mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env.update(GOCACHE=str(TEMP/'cache'),GOPATH=str(ROOT/'.local/tools/gopath'),GOTMPDIR=str(TEMP/'tmp'),TMP=str(TEMP/'tmp'),TEMP=str(TEMP/'tmp'),RESEARCHOS_MU_BUNDLE=str(ROOT/'.local/builds/current-chat-runtime-assets-20261012/mu-worker.mjs'))
    guards('initial')
    manifest=json.loads((SOURCE/'source-manifest.json').read_text(encoding='utf-8-sig'))
    checks=[]
    for group,root in [('changed_files',CAND),('input_refs',ROOT),('receipt_files',SOURCE)]:
        for row in manifest[group]:
            p=root/row['path']; actual=sha(p)
            checks.append({'group':group,'path':str(p),'expected':row['sha256'],'actual':actual,'matches':actual==row['sha256']})
    for p,expected in [(ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp501/qualification-projection-A-independent-review-scope.json','3d4251b6d0d4821cd8c2950c2d29b5ca3f48fd18543a2192f2b57e173215f13a'),(SOURCE/'source-manifest.json','81230c4b2c13efcae5b5a1e1a05c7188c576ae32565495ef33b472b087dd09df'),(SOURCE/'SUPPLEMENT-manifest.json','9eb5ae983f1b220ed8882e3b96a465940b1f402c6477dd93d7fad4d0b9e74b29')]:
        actual=sha(p); checks.append({'path':str(p),'expected':expected,'actual':actual,'matches':actual==expected})
    save('input-hashes.json',checks)
    if not all(x['matches'] for x in checks): raise SystemExit('input hash mismatch')
    patch=run('canonical-patch',['git','--no-optional-locks','diff','--binary',manifest['base'],manifest['commit']],CAND)
    save('patch-comparison.json',{'equal':patch==(SOURCE/'source-candidate.patch').read_bytes(),'sha256':hashlib.sha256(patch).hexdigest(),'paths':git(CAND,'diff','--name-only',manifest['base'],manifest['commit']).splitlines()})
    run('reverse-patch-check',['git','--no-optional-locks','apply','--check','--reverse',str(SOURCE/'source-candidate.patch')],CAND)
    audit=json.loads((SOURCE/'formatter-restore-audit.json').read_text(encoding='utf-8-sig'))
    save('formatter-recheck.json',[{'path':r['path'],'actual':git(CAND,'hash-object','--',r['path']),'head':git(CAND,'rev-parse','HEAD:'+r['path']),'recorded':r['head_blob']} for r in audit])
    run('go-version',[GO,'version'],CAND,env)
    selection='^(TestRuntimeCoordinatorNativeQualification|TestRuntimeMuSessionToolAndIndependentAcceptance)$'
    run('candidate-regressions',[GO,'test','./internal/domain','-run',selection,'-count=1','-json'],CAND,env)
    run('base-regressions',[GO,'test','./internal/domain','-run',selection,'-count=1','-json'],BASE,env)
    command=json.loads((SOURCE/'final-targeted.command.json').read_text(encoding='utf-8-sig'))
    run('candidate-focused',command['argv'],CAND,env)
    run('candidate-build',[GO,'build','-o',str(TEMP/'control-review.exe'),'./apps/control'],CAND,env)
    guards('final')
