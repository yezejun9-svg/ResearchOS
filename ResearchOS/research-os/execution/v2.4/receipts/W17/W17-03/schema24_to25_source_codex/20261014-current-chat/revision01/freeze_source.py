import datetime, hashlib, json, os, pathlib, shutil, subprocess

E = pathlib.Path(__file__).parent
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path, value): path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
def pin(path):
    path = pathlib.Path(path)
    return dict(path=str(path), sha256='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
scope = read(E/'scope.json')
original_scope = read(E.parent/'scope.json')
W = pathlib.Path(scope['worktree'])
F = E/'final-freeze'
F.mkdir()
B = E/'target25-r4-build-inputs'
B.mkdir()
env = dict(os.environ, **read(E/'33-revision-backup-build'/'command.json')['environment'])
go = str(pathlib.Path(env['GOROOT'])/'bin/go.exe')
def run(name, argv, directory=B):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=W, env=env, capture_output=True)
    out, err = directory/(name+'.stdout.raw'), directory/(name+'.stderr.raw')
    out.write_bytes(proc.stdout); err.write_bytes(proc.stderr)
    write(directory/(name+'.invocation.json'), dict(argv=argv,cwd=str(W),started=started,exit=proc.returncode,stdout=pin(out),stderr=pin(err),environment={k:env[k] for k in read(E/'33-revision-backup-build'/'command.json')['environment']}))
    if proc.returncode: raise RuntimeError(name)
    return proc.stdout

raw = run('go-list',[go,'list','-mod=readonly','-deps','-json','./ops/backup','./apps/control','./ops/supervisor/recovery_root','./ops/supervisor/recovery_enrollment']).decode('utf-8')
decoder=json.JSONDecoder(); packages=[]; at=0
while at<len(raw):
    if raw[at].isspace(): at+=1; continue
    obj,at=decoder.raw_decode(raw,at); packages.append(obj)
paths={pathlib.Path(go),W/'go.mod',W/'go.sum',W/'execution/toolchains/locked.json'}
for tool in ['asm','cgo','compile','link']: paths.add(pathlib.Path(env['GOROOT'])/'pkg/tool/windows_amd64'/(tool+'.exe'))
for pkg in packages:
    for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles']:
        for item in pkg.get(key,[]): paths.add(pathlib.Path(pkg['Dir'])/item)
    mod=pkg.get('Module',{})
    if mod.get('GoMod'): paths.add(pathlib.Path(mod['GoMod']))
write(B/'compiler-inputs.json',dict(schema='researchos.fixture-compiler-inputs.v1',source_root=str(W),packages=len(packages),file_count=len(paths),inputs=[pin(p) for p in sorted(paths)]))
config=read(E/'public-handoff04.config.json')
programs=[]
for role in ['BackupProgram','ControlProgram','RootProgram','EnrollmentProgram']:
    p=pathlib.Path(config[role]['path']); programs.append(dict(role=role,**pin(p)))
    buildinfo=run('go-version-m-'+p.stem,[go,'version','-m',str(p)])
    assert b'vcs.modified=false' in buildinfo
write(B/'programs.json',programs)
identity=run('git-identity',['git','rev-parse','HEAD','HEAD^{tree}']).decode().splitlines()
assert not run('git-status',['git','status','--porcelain'])
changed=run('scope-diff',['git','diff','--name-only',scope['base_commit'],'HEAD'],F).decode().splitlines()
assert sorted(changed)==sorted(scope['paths']), (changed,scope['paths'])
run('diff-check',['git','diff','--check',scope['base_commit'],'HEAD'],F)
patch=run('source-patch',['git','diff','--binary',scope['base_commit'],'HEAD'],F)
(F/'source.patch').write_bytes(patch)
(F/'combined22.patch').write_bytes(run('combined22-patch',['git','diff','--binary',original_scope['base_commit'],'HEAD'],F))
combined=run('combined22-paths',['git','diff','--name-only',original_scope['base_commit'],'HEAD'],F).decode().splitlines()
assert sorted(combined)==sorted(original_scope['paths'])
sourcepins=[]
for rel in scope['paths']:
    dest=F/'source'/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(W/rel,dest)
    sourcepins.append(dict(relative=rel,**pin(dest),live_sha256=pin(W/rel)['sha256']))
guards=[]
for rel in original_scope['read_only_dependencies'] + [p for p in original_scope['paths'] if p not in scope['paths']]:
    if not (W/rel).is_file():
        guards.append(dict(path=rel,status='ABSENT_IN_BASE_AND_CANDIDATE' if subprocess.run(['git','cat-file','-e',scope['base_commit']+':'+rel],cwd=W,capture_output=True).returncode else 'ERROR'))
        assert guards[-1]['status']!='ERROR'; continue
    baseline=subprocess.run(['git','show',scope['base_commit']+':'+rel],cwd=W,capture_output=True,check=True).stdout
    assert hashlib.sha256(baseline).hexdigest()==pin(W/rel)['sha256'].split(':')[1],rel
    guards.append(dict(relative=rel,status='UNCHANGED',**pin(W/rel)))
write(F/'source-pins.json',sourcepins); write(F/'readonly-guards.json',guards)
ledger=read(E/'ledger.json')
assert ledger['failed_attempt_count']==4
testsummary=[]
for name in ['31-signed-stage-boundary-fixed','32-old-and-pause-regressions','37-revision-public-cli-handoff']:
    folder=E/name
    if not folder.exists():
        matches=list(E.glob(name.split('-')[0]+'-*')); assert len(matches)==1; folder=matches[0]
    records=[json.loads(line) for line in (folder/'stdout.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.startswith('{')]
    passed=[r for r in records if r.get('Action')=='pass' and r.get('Test')]
    tops=[r for r in passed if '/' not in r['Test']]
    leaves=[r for r in passed if not any(s['Package']==r['Package'] and s['Test'].startswith(r['Test']+'/') for s in passed)]
    testsummary.append(dict(capture=folder.name,top_level=len(tops),leaves=len(leaves),skipped=[r for r in records if r.get('Action')=='skip'],command=pin(folder/'command.json')))
write(F/'verification-summary.json',testsummary)
write(F/'identity.json',dict(head=identity[0],tree=identity[1],base=scope['base_commit'],scope_count=len(changed),clean=True))
print(json.dumps(dict(identity=identity,scope_count=len(changed),compiler_files=len(paths),tests=testsummary,failures=ledger['failed_attempt_count']),ensure_ascii=False))
