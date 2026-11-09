import datetime, hashlib, json, os, pathlib, re, subprocess, sys
E=pathlib.Path(__file__).resolve().parent
R=E.parents[6]
A=R/'execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat'
S=R/'.local/worktrees/profile-result-build-20261014'
P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(name,argv,cwd,env=None,timeout=60):
    start=now()
    try:
        p=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,capture_output=True,timeout=timeout)
        code,out,err=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as e: code,out,err=124,e.stdout or b'',e.stderr or b''
    (E/(name+'.stdout')).write_bytes(out); (E/(name+'.stderr')).write_bytes(err)
    row=dict(argv=list(map(str,argv)),cwd=str(cwd),started=start,ended=now(),native_exit=code)
    if env: row['environment']={k:v for k,v in env.items() if k in ['TEMP','TMP','RESEARCHOS_DESKTOP_WIRE_ROOT','RESEARCHOS_DESKTOP_CASE_RECEIPT','RESEARCHOS_DESKTOP_ELECTRON','GOTOOLCHAIN','GOENV']}
    put(name+'.process.json',row)
    assert code==0,(name,code,err[-500:])
    return out.decode('utf-8',errors='strict')
def audit():
    assert sha(A/'FINAL-manifest.json')=='0bedb06fbb120c69c2224f0102c2be0c0aeed158d0f62322d7a9406a83351466'
    m=read(A/'FINAL-manifest.json'); d=read(P/'apps/desktop/resources/client-wire/descriptor.json')
    pins={}; occurrences=0
    def pin(path,digest=None,size=None):
        nonlocal occurrences
        path=pathlib.Path(path); key=str(path.resolve()); h=sha(path)
        if digest: assert h==digest,(key,'digest',h,digest)
        if size is not None: assert path.stat().st_size==size,(key,'size')
        row=dict(path=key,sha256=h,bytes=path.stat().st_size)
        if key in pins: assert row==pins[key]
        pins[key]=row; occurrences+=1
    def walk(obj):
        if isinstance(obj,list):
            for x in obj:walk(x)
        elif isinstance(obj,dict):
            if isinstance(obj.get('sha256'),str):
                p=obj.get('copy') or obj.get('path')
                if p and pathlib.Path(p).is_absolute(): pin(p,obj['sha256'],obj.get('bytes'))
            for v in obj.values():walk(v)
    pin(A/'FINAL-manifest.json'); walk(m)
    raw=read(A/'raw-freeze.json'); walk(raw)
    assert raw['raw_count']==32 and raw['WORK_count']==1844 and raw['archive_count']==680
    inputs=read(A/'raw-build-receipts/inputs.before.json'); after=read(A/'raw-build-receipts/inputs.after.json')
    assert len(inputs)==len(after)==6444
    bound=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert bound==m['build']['input_digest']==d['build_input_digest']=='819e8a98f8b678928a6354663747ea2d0b7adab21bc220fe6720edf7dc20c8ce'
    assert [{k:v for k,v in row.items() if k!='current_sha256'} for row in after]==inputs
    assert all(x['sha256']==x['current_sha256'] for x in after)
    walk(inputs);walk(d)
    actual=sorted(p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file())
    assert actual==sorted(x['path'] for x in m['package']['members']) and len(actual)==58
    for x in m['package']['members']:
        f=P/x['path'];pin(f,x['sha256'],x['bytes'])
        if not x['component'].startswith('NEW_INSTALLATION'):pin(x['source'],x['sha256'],x['bytes'])
        if x['component'] in ['FRESH_BOUND_MAIN_PRELOAD_C8','PUBLIC_SOURCE_EQUAL_OLD']:pin(S/x['path'],x['sha256'],x['bytes'])
    assert len(d['exact_module_source_inventory'])==14 and len(d['compiled_React_asset_inventory'])==3
    for x in d['exact_module_source_inventory']:pin(P/'apps/desktop'/x['path'],x['sha256'])
    for x in d['compiled_React_asset_inventory']:pin(P/'apps/web/dist'/x['path'],x['sha256'],x['bytes'])
    assert sorted(int(p.name[:4]) for p in (P/'migrations/sqlite').glob('[0-9]*.sql'))==list(range(1,25))
    i=read(P/'apps/desktop/resources/control/runtime-verifier-installation.json')
    assert pathlib.Path(i['executable'])==P/'apps/desktop/resources/control/runtime-verifier.exe'
    assert i['source_commit']=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2' and i['arguments']==[]
    pin(i['executable'],i['executable_hash'].removeprefix('sha256:'))
    c=read(A/'composition.json');walk(c)
    for p in A.rglob('*'):
        if p.is_file():pin(p)
    git=run('git-identity',['git','rev-parse','HEAD','HEAD^{tree}'],S).splitlines()
    assert git==['c8b7adab9f0c15eb33f235f8d0d9eb205794e376','cd951533206a6a4545a6e55fec374e62289d2dd4']
    assert run('git-clean',['git','status','--porcelain','--untracked-files=no'],S)==''
    assert set(run('git-diff-base',['git','diff','--name-only','a7ec7ebf2d53848ea163b6115667b3e3761a6bd2','HEAD'],S).splitlines())=={'apps/desktop/main/lib/desktop-management.js','tests/ui/desktop/coding-authorization-boundary.test.mjs'}
    go=next(t['path'] for t in d['tools'] if t['name']=='go'); env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off')
    versions={}
    for name,rel,commit in [('validator','client-wire/researchos-client-wire-validator.exe',git[0]),('control','control/researchos-control.exe',i['source_commit']),('verifier','control/runtime-verifier.exe',i['source_commit'])]:
        text=run(name+'-version-m',[go,'version','-m',P/'apps/desktop/resources'/rel],S,env)
        assert 'vcs.revision='+commit in text and 'vcs.modified=false' in text
        if name=='validator':assert bound in text
        versions[name]=commit
    for k,v in m['build']['builder_invocations'].items():assert v['numeric_exit']==0
    assert len(read(A/'failed-attempts.json')['attempts'])==3
    put('inputs.before.json',list(pins.values()))
    put('audit.json',dict(status='PASS',at=now(),pins=len(pins),occurrences=occurrences,build_inputs=len(inputs),input_digest=bound,package_members=58,modules=14,react=3,raw_files=32,compiler_WORK=1844,compiler_archives=680,versions=versions,author_failure_count=3))
    print(json.dumps(read(E/'audit.json')))
def tests():
    env=dict(os.environ)
    case=E/'package-cases';case.mkdir();temp=case/'temp';temp.mkdir()
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(P/'apps/desktop'),RESEARCHOS_DESKTOP_CASE_RECEIPT=str(case),RESEARCHOS_DESKTOP_ELECTRON=str(R/'apps/desktop/node_modules/electron/dist/electron.exe'),TEMP=str(temp),TMP=str(temp))
    out=run('fresh-package-cases',['C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe','--test','--test-concurrency=1','--test-name-pattern=^(desktop-http|qualification-lane)/',S/'tests/ui/desktop/http-wire-boundary.test.mjs'],S,env,450)
    counts={k:int(re.findall(r'^[#ℹ]\s+'+k+r'\s+(\d+)\s*$',out,re.M)[0]) for k in ['tests','pass','fail','skipped','cancelled']}
    assert counts=={'tests':214,'pass':214,'fail':0,'skipped':0,'cancelled':0}
    put('test-summary.json',dict(at=now(),counts=counts,GUI=False,product_API=False,model_calls=0,formal_increment=0))
    print(json.dumps(counts))
def after():
    rows=read(E/'inputs.before.json');drift=[]
    for row in rows:
        p=pathlib.Path(row['path'])
        if not p.is_file() or sha(p)!=row['sha256']:drift.append(row['path'])
    put('inputs.after.json',dict(at=now(),count=len(rows),drift=drift));assert not drift,drift
    print(json.dumps({'pins':len(rows),'drift':drift}))
if __name__=='__main__':globals()[sys.argv[1]]()
