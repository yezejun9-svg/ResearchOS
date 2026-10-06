from pathlib import Path
import hashlib,json,os,subprocess,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];MAIN=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
go=read(MAIN/'execution/toolchains/locked.json')['tools']['go'];assert sha(Path(go['path']))==go['sha256']
env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',GOPROXY='off',GOSUMDB='off',GOROOT=str(Path(go['path']).parents[1]),GOCACHE=str(MAIN/'.local/gocache'),GOPATH=str(MAIN/'.local/gopath'),RESEARCHOS_GO=go['path'])
env.pop('RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL',None)
envkeys=['GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','GOROOT','GOCACHE','GOPATH','RESEARCHOS_GO','RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL']
binary=ROOT/'.local/historical-fixtures-current/domain.test.exe';binary.parent.mkdir(parents=True,exist_ok=True)
def run(name,argv,cwd,extra=None):
    d=HERE/name;d.mkdir(exist_ok=False);e=dict(env);e.update(extra or {})
    write(d/'command.json',{'argv':argv,'cwd':str(cwd),'environment':{k:e[k] for k in envkeys if k in e},'exe':ref(Path(argv[0])),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'source_file':ref(ROOT/'internal/domain/backup_upgrade_test.go'),'started':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with (d/'stdout.raw').open('wb') as out,(d/'stderr.raw').open('wb') as err:code=subprocess.run(argv,cwd=cwd,env=e,stdout=out,stderr=err).returncode
    write(d/'result.json',{'exit_code':code,'stdout':ref(d/'stdout.raw'),'stderr':ref(d/'stderr.raw'),'ended':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(json.dumps({'run':name,'exit':code}),flush=True);return code,d
code,d=run('selector-dependencies',[go['path'],'list','-deps','-test','-json','./internal/domain'],ROOT);assert code==0
raw=(d/'stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();pos=0;paths=set();missing=[]
while pos<len(raw):
    if raw[pos:].strip()=='':break
    pos+=len(raw[pos:])-len(raw[pos:].lstrip());v,n=dec.raw_decode(raw,pos);pos=n
    for key in ('GoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles'):
        for name in v.get(key,[]):
            p=Path(name) if Path(name).is_absolute() else Path(v.get('Dir',''))/name
            if p.is_file():paths.add(p.resolve())
            else:missing.append({'package':v.get('ImportPath'),'kind':key,'file':str(p)})
for p in ROOT.glob('go.*'):paths.add(p)
for base in (ROOT/'migrations/sqlite',ROOT/'spec/v2.0/contracts',ROOT/'internal/api/contracts'):
    paths.update(p for p in base.rglob('*') if p.is_file())
paths.add(MAIN/'execution/toolchains/locked.json')
before=[ref(p) for p in sorted(paths)];write(HERE/'selector-inputs-before.json',{'files':before,'generated_or_absent_package_files':missing})
code,_=run('selector-build',[go['path'],'test','-c','-o',str(binary),'./internal/domain'],ROOT);assert code==0
write(HERE/'selector-test-binary.json',ref(binary))
artifact=MAIN/'.local/bin/researchos-remote.exe';assert sha(artifact)=='aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032'
wrong=HERE/'wrong-artifact.bin';wrong.write_bytes(b'explicit invalid historical artifact fixture\n')
results=[]
for name,path,expected,reason in [('valid-artifact',artifact,0,'REAL-PRODUCT-14-AUTHENTICATED-READ'),('missing-artifact',HERE/'not-existing-artifact.exe',1,'historical schema14 artifact read:'),('wrong-hash-artifact',wrong,1,'historical schema14 artifact hash mismatch')]:
    code,d=run(name,[go['path'],'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',str(binary),'-test.v','-test.run=^TestW17UpgradeCLI$','-test.count=1','-test.timeout=180s'],ROOT/'internal/domain',{'RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL':str(path)})
    raw=(d/'stdout.raw').read_text(encoding='utf-8');events=[json.loads(line) for line in raw.splitlines() if line.strip()];texts=''.join(e.get('Output','') for e in events)
    tests={a:[e.get('Test') for e in events if e.get('Action')==a and e.get('Test')] for a in ('pass','fail','skip')}
    assertions=[]
    for line in texts.splitlines():
        if 'W17_ASSERTION ' in line:
            try:assertions.append(json.loads(line.split('W17_ASSERTION ',1)[1]))
            except ValueError:pass
    okay=code==expected and reason in texts and not tests['skip'] and ((tests['pass']==['TestW17UpgradeCLI'] and not tests['fail']) if expected==0 else tests['fail']==['TestW17UpgradeCLI'])
    outcome={'run':name,'actual_exit':code,'expected_exit':expected,'expected_marker':reason,'expectation_met':okay,'events':tests,'original_assertions':assertions,'test_binary':ref(binary)}
    write(d/'assessment.json',outcome);results.append(outcome)
    if not okay:break
after=[ref(p) for p in sorted(paths)];write(HERE/'selector-inputs-after.json',{'files':after,'generated_or_absent_package_files':missing})
write(HERE/'selector-report.json',{'classification':'NARROW_CURRENT_UPGRADE_CLI_WITH_FIXED_HISTORICAL14_TARGET_NOT_CURRENT22_CONTROL','status':'PASS' if len(results)==3 and all(r['expectation_met'] for r in results) and before==after else 'FAIL','source_vector_equal':before==after,'dependency_count':len(before),'tests':results,'fixed_artifact':ref(artifact),'product_or_parent_acceptance':False,'Q10_closed':False,'four_original_failures_retained':True})
assert len(results)==3 and all(r['expectation_met'] for r in results) and before==after
