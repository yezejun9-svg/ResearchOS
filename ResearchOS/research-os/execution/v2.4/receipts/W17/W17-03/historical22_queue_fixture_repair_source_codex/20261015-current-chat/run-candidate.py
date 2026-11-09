import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
WT=MAIN/'.local/worktrees/historical22-queue-fixture-repair-20261015'
GO=MAIN/'.local/tools/go1.27.1/go'
TMP=MAIN/'.local/builds/historical22-active-queue-helper-20261015/candidate-tmp-01'
SRC=WT/'internal/domain/backup_configuration_upgrade_test.go'
RECORD=OUT/'closed-source22-05.json'
assert len(sys.argv)==2 and sys.argv[1] in ('active','active2','active3','active4','active5','active6','active7','adjacent')
label=sys.argv[1]
if label.startswith('active'):
    if label=='active2': TMP=MAIN/'.local/builds/historical22-active-queue-helper-20261015/candidate-tmp-03'
    if label=='active3': TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-active3'
    if label=='active4': TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-active4'
    if label=='active5': TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-active5'
    if label=='active6': TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-active6'
    if label=='active7': TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-active7'
    assert not TMP.exists();TMP.mkdir(parents=True,exist_ok=False)
else:
    TMP=MAIN/'.local/builds/historical22-candidate-run-20261015/tmp-adjacent'
    assert not TMP.exists();TMP.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(SRC)
env=os.environ.copy()
allow={'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO),'GOPATH':str(MAIN/'.local/tools/gopath'),'GOMODCACHE':str(MAIN/'.local/tools/gopath/pkg/mod'),'GOCACHE':str(MAIN/'.local/builds/schema25-core-composition-20261015/go-cache'),'GOTMPDIR':str(TMP),'GOPROXY':'off','GOSUMDB':'off','GOFLAGS':'-buildvcs=true','GOWORK':'off','TEMP':str(TMP),'TMP':str(TMP),'RESEARCHOS_CONFIGURATION_OLD_CONTROL':str(MAIN/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/old22-control.exe'),'RESEARCHOS_CONFIGURATION_OLD_ROOT':str(MAIN/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/frozen_source'),'RESEARCHOS_CONFIGURATION_TARGET_PROGRAM':str(MAIN/'execution/v2.4/receipts/W05/W05-99/main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab/programs/main-backup23.exe'),'RESEARCHOS_HISTORICAL22_ACTIVE_RECORD':str(RECORD),'RESEARCHOS_HISTORICAL22_ACTIVE_RECORD_SHA256':'sha256:'+sha(RECORD)}
for key in ('RESEARCHOS_CONFIGURATION_OLD_CONTROL','RESEARCHOS_CONFIGURATION_OLD_ROOT','RESEARCHOS_CONFIGURATION_TARGET_PROGRAM'):
    assert Path(allow[key]).exists()
env.update(allow)
pattern='^TestConfigurationUpgradeActiveQueueRecovery$' if label.startswith('active') else '^TestConfigurationUpgrade(Frozen22ProgramLock|NativeCLI)$'
argv=[str(GO/'bin/go.exe'),'test','-mod=readonly','-json','./internal/domain','-run',pattern,'-count=1','-timeout=10m']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=WT,env=env,capture_output=True)
(OUT/f'candidate-{label}.stdout.raw').write_bytes(r.stdout);(OUT/f'candidate-{label}.stderr.raw').write_bytes(r.stderr)
after=sha(SRC)
events=[json.loads(line) for line in r.stdout.splitlines() if line.startswith(b'{')]
test_results={e['Test']:e['Action'] for e in events if e.get('Test') and e.get('Action') in ('pass','fail','skip') and '/' not in e['Test']}
record={'argv':argv,'cwd':str(WT),'allowlist_env':allow,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':r.returncode,'source_before_sha256':before,'source_after_sha256':after,'source_unchanged':before==after,'test_results':test_results,'stdout_sha256':sha(OUT/f'candidate-{label}.stdout.raw'),'stderr_sha256':sha(OUT/f'candidate-{label}.stderr.raw')}
(OUT/f'candidate-{label}.invocation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:record[k] for k in ('native_exit','source_unchanged','test_results','stdout_sha256','stderr_sha256')},ensure_ascii=False))
raise SystemExit(r.returncode if before==after else 2)
