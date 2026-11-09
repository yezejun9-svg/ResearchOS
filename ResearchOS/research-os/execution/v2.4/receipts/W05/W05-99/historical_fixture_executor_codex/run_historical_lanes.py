"""Frozen historical source-only lanes; never executes a preserved authority DB."""
from pathlib import Path
import hashlib,json,os,subprocess,datetime,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];MAIN=Path('D:/作品集/ResearchOS/research-os')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def git(cwd,*args):return subprocess.check_output(['git',*args],cwd=cwd)
go=read(MAIN/'execution/toolchains/locked.json')['tools']['go'];assert sha(Path(go['path']))==go['sha256']
env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly -buildvcs=false',GOROOT=str(Path(go['path']).parents[1]),GOCACHE=str(MAIN/'.local/gocache'),GOPATH=str(MAIN/'.local/gopath'),RESEARCHOS_GO=go['path'])
for key in ('RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL','W16_CONTROL_PROTECTED_EVIDENCE_DIR','W16_CONTROL_EVIDENCE_DIR'):env.pop(key,None)
envkeys=['GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','GOFLAGS','GOROOT','GOCACHE','GOPATH','RESEARCHOS_GO','W16_CONTROL_EVIDENCE_DIR']
scopes=['apps/control','internal','adapters','evaluation','ops','migrations','spec/v2.0/contracts','go.mod','go.sum','execution/toolchains/locked.json']
def blobs(cwd,rev,paths):
    request=''.join(rev+':'+p+'\n' for p in paths).encode()
    data=subprocess.check_output(['git','cat-file','--batch'],cwd=cwd,input=request);out={};pos=0
    for path in paths:
        end=data.index(b'\n',pos);header=data[pos:end].decode().split();assert header[1]=='blob',header
        size=int(header[2]);pos=end+1;out[path]=data[pos:pos+size];pos+=size+1
    return out
def run(lane,name,argv,cwd,extra=None):
    d=lane/name;d.mkdir(exist_ok=False);e=dict(env);e.update(extra or {})
    write(d/'command.json',{'argv':argv,'cwd':str(cwd),'environment':{k:e[k] for k in envkeys if k in e},'executable':ref(Path(argv[0])),'runner':ref(Path(__file__)),'started':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with (d/'stdout.raw').open('wb') as out,(d/'stderr.raw').open('wb') as err:code=subprocess.run(argv,cwd=cwd,env=e,stdout=out,stderr=err).returncode
    write(d/'result.json',{'exit_code':code,'stdout':ref(d/'stdout.raw'),'stderr':ref(d/'stderr.raw'),'ended':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(json.dumps({'lane':lane.name,'command':name,'exit':code}),flush=True)
    return code,d
results=[]
for version in (14,20):
    lane=HERE/('schema'+str(version));lane.mkdir(exist_ok=False)
    snapshot=ROOT/('.local/historical-fixtures-lanes/schema'+str(version)+'/source');snapshot.mkdir(parents=True,exist_ok=False)
    if version==14:
        origin=MAIN/'.local/releases/schema14-09a6a5e';rev='09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0'
        paths=git(MAIN,'ls-tree','-r','--name-only',rev,'--',*scopes).decode().splitlines();original=blobs(MAIN,rev,paths)
        provenance=[{'path':p,'sha256':digest(original[p]),'basis':'exact historical git blob '+rev,'preserved_release_exists':(origin/p).is_file(),'preserved_release_matches':(origin/p).is_file() and sha(origin/p)==digest(original[p])} for p in paths]
        assert all(p['preserved_release_matches'] for p in provenance if p['preserved_release_exists'])
    else:
        origin=MAIN/'.local/worktrees/control-business-proof';rev=git(origin,'rev-parse','HEAD').decode().strip()
        prior=read(MAIN/'execution/receipts/W16/current-control-admission/attempt-10-first-evaluation/actual-build.json');inputs=prior['source_provenance']['files']
        paths=git(origin,'ls-files','--',*scopes).decode().splitlines();original={p:(origin/p).read_bytes() for p in paths};frozen=blobs(origin,rev,paths)
        assert set(inputs).issubset(paths)
        assert git(origin,'ls-files','--others','--exclude-standard','--',*scopes).strip()==b''
        provenance=[]
        for p in paths:
            if p in inputs:
                assert 'sha256:'+digest(original[p])==inputs[p],p
                basis='actual-build.json recorded206 production inputs'
            else:
                assert original[p]==frozen[p],p
                basis='additional original source/test/helper/embed exact git blob '+rev
            provenance.append({'path':p,'sha256':digest(original[p]),'basis':basis})
        assert sha(origin/'internal/domain/evolution_control_test.go')=='8a578b7c3fa35a639fafc976998b4b1442606bbb002029f84bd02744426145ea'
    for p,raw in original.items():
        target=snapshot/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    source_before=[ref(snapshot/p) for p in sorted(paths)]
    observed=[p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()]
    assert set(observed)==set(paths)
    sql=[p for p in paths if re.match(r'migrations/sqlite/\d{4}_.*\.sql$',p)]
    assert sorted(int(Path(p).name[:4]) for p in sql)==list(range(1,version+1))
    write(lane/'snapshot-provenance.json',{'origin':str(origin),'historical_version':version,'source_identity':'git09a' if version==14 else 'actual-build206 plus explicit additional git blobs; not HEAD-only','files':provenance,'source_only':True,'existing_DB_private_or_receipt_copied':False,'numbered_migrations':sql,'extras':sorted(set(observed)-set(paths)),'source_before':source_before})
    code,d=run(lane,'dependencies',[go['path'],'list','-deps','-test','-json','./internal/domain','./apps/control'],snapshot);assert code==0
    raw=(d/'stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();pos=0;dependencies=set();missing=[]
    while raw[pos:].strip():
        pos+=len(raw[pos:])-len(raw[pos:].lstrip());v,pos=dec.raw_decode(raw,pos)
        for key in ('GoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles'):
            for name in v.get(key,[]):
                p=Path(name) if Path(name).is_absolute() else Path(v.get('Dir',''))/name
                if p.is_file():dependencies.add(p.resolve())
                else:missing.append({'package':v.get('ImportPath'),'kind':key,'path':str(p)})
    compiled_source=[p for p in dependencies if p.is_relative_to(snapshot)]
    assert all(p.relative_to(snapshot).as_posix() in paths for p in compiled_source)
    deps_before=[ref(p) for p in sorted(dependencies)];write(lane/'dependencies-before.json',{'files':deps_before,'generated_or_absent':missing})
    binroot=snapshot.parent/'bin';binroot.mkdir();testbin=binroot/'domain.test.exe';control=binroot/'control.exe'
    code,_=run(lane,'test-build',[go['path'],'test','-c','-o',str(testbin),'./internal/domain'],snapshot);assert code==0
    if version==20:
        code,_=run(lane,'control-reference-build',[go['path'],'build','-o',str(control),'./apps/control'],snapshot);assert code==0
    selection='^TestW17UpgradeActiveRecovery$' if version==14 else '^(TestW16ControlReplayNative|TestW16ControlBusinessNoGain)$'
    evidence=lane/'new-public-evidence';evidence.mkdir()
    code,d=run(lane,'original-tests',[go['path'],'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',str(testbin),'-test.v','-test.run='+selection,'-test.count=1','-test.timeout=240s'],snapshot/'internal/domain',{'W16_CONTROL_EVIDENCE_DIR':str(evidence)} if version==20 else {})
    events=[json.loads(l) for l in (d/'stdout.raw').read_text(encoding='utf-8').splitlines() if l.strip()];text=''.join(e.get('Output','') for e in events)
    counts={a:[e['Test'] for e in events if e.get('Action')==a and e.get('Test')] for a in ('pass','fail','skip')}
    marker='W17_UPGRADE_ASSERTION ' if version==14 else 'W16_CONTROL_ASSERTION '
    assertions=[json.loads(l.split(marker,1)[1]) for l in text.splitlines() if marker in l]
    required=({'REAL-FENCE-COUNTS','COSTS-CURSORS-PRESERVED','SOURCE-RELOCATED-SEALED-BYTES','UNKNOWN-EFFECT-BLOCKS-REPLAY','OLD-OBSERVATION-REJECTED','FRESH-OBSERVATION-SAME-RUN','FENCE-NO-PRIVATE-READ'} if version==14 else {'REAL-EXE-NON-APPCONTAINER-REFUSED','SAME-CONTROL-REAL-API-CORRECT','SAME-CONTROL-NO-GAIN','PRIVATE-CONTROL-SAME-BUILD-NO-GAIN','NORMAL-TASK-RUN-EXPERIMENT-ACCEPTANCE','NO-GAIN-CANDIDATE-REJECTED','STABLE-RETAINED-NO-SWITCH-EFFECT'}|{'PROOF-REFUSES-'+k for k in ('exe','protocol','snapshot','source','calculator','receipt')})
    source_after=[ref(snapshot/p) for p in sorted(paths)];deps_after=[ref(p) for p in sorted(dependencies)]
    write(lane/'source-after.json',source_after);write(lane/'dependencies-after.json',{'files':deps_after,'generated_or_absent':missing})
    okay=code==0 and len(counts['pass'])==(1 if version==14 else 2) and not counts['fail'] and not counts['skip'] and assertions and all(a['status']=='PASS' for a in assertions) and required.issubset({a['assertion_id'] for a in assertions}) and source_before==source_after and deps_before==deps_after
    result={'version':version,'status':'PASS_HISTORICAL_CONTRACT_ONLY' if okay else 'FAIL','actual_exit':code,'tests':counts,'assertions':assertions,'required_assertions':sorted(required),'test_binary':ref(testbin),'control_reference_binary':ref(control) if version==20 else None,'snapshot_file_count':len(paths),'actual_dependency_count':len(deps_before),'source_vector_equal':source_before==source_after,'dependency_vector_equal':deps_before==deps_after,'formal_or_parent_acceptance':False,'Q10_closed':False}
    if version==20 and (evidence/'public-control-native-proof.json').exists():
        proof=read(evidence/'public-control-native-proof.json');result['actual_public_control_proof_hashes']={k:v for k,v in proof.items() if 'hash' in k.lower() and isinstance(v,str)}
        result['control_reference_matches_actual_proof']=proof.get('baseline_hash')=='sha256:'+sha(control) and proof.get('candidate_hash')=='sha256:'+sha(control)
    write(lane/'report.json',result);results.append(result)
    print(json.dumps({'lane':version,'status':result['status'],'assertions':len(assertions),'pass':counts['pass'],'fail':counts['fail'],'skip':counts['skip']}),flush=True)
    if not okay:break
write(HERE/'historical-lanes-report.json',{'lanes':results,'Q10_closed':False,'four_original_main_failures_retained':True,'counter_reset':False,'current22_qualification':False})
assert len(results)==2 and all(r['status']=='PASS_HISTORICAL_CONTRACT_ONLY' for r in results)
