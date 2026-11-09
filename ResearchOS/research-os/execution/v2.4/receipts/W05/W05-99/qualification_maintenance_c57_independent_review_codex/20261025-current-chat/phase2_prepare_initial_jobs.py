import pathlib,json,re
B=pathlib.Path(__file__).parent
v=json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'));S=pathlib.Path(v['snapshot']);C=S.parent
D=pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/qualification-maintenance-c57-independent-review-20261025-tmp')
jobs=B/'PHASE2-jobs';jobs.mkdir(exist_ok=False)
tool=r'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
base={'GOOS':'windows','GOARCH':'amd64','CGO_ENABLED':'0','GOENV':'off','GOTOOLCHAIN':'local','GOFLAGS':'-mod=readonly','GOSUMDB':'off','GOPROXY':pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod/cache/download').as_uri(),'GOMODCACHE':str(C/'gomodcache'),'GOPATH':str(C/'gopath'),'GOCACHE':str(C/'go-cache'),'GOTMPDIR':str(C/'go-tmp')}
corepkgs=['adapters/runtime','internal/store','internal/qualificationmaintenancejournal','internal/host','apps/control','ops/backup','ops/supervisor/release_host']
corefiles=[i['path'] for i in v['candidate_source_files'] if i['path'].endswith('_test.go') and str(pathlib.PurePosixPath(i['path']).parent) in corepkgs]
coretests=[]
for path in corefiles:coretests+=re.findall(r'^func (Test\w+)\(', (S/path).read_text(encoding='utf-8'),re.M)
groups=[('089-phase2-core-c',corepkgs,'^('+'|'.join(sorted(set(coretests)))+')$','C_NATIVE',C/'native-c'),('090-phase2-domain-c',['internal/domain'],'^(TestHistoricalQualification.*|TestBackupSourceLease.*|TestPreparedNestedSourceLeaseCloseKeepsOuterNativeOwner|TestConfigurationUpgradeActiveQueueRecovery)$','C_NATIVE',C/'native-c'),('091-phase2-boot-c',['internal/recoveryboundary'],'^Test','C_NATIVE',C/'native-c'),('092-phase2-boot-d',['internal/recoveryboundary'],'^Test','D_NATIVE',D/'native-d')]
for tag,pkgs,pattern,cls,tmp in groups:
 env=dict(base);env['TEMP']=env['TMP']=str(tmp)
 job={'tag':tag,'class':cls,'argv':[tool,'test','-json','-count=1','-timeout=8m',*('./'+p for p in pkgs),'-run',pattern],'env':env,'supplementary_files':[]}
 (jobs/(tag+'.json')).write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
 print(tag,'packages',len(pkgs),'regex',pattern)
print('core tests',len(set(coretests)))
