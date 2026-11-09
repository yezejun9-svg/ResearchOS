import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
SRC=MAIN/'.local/resources/historical22-active-queue-helper-20261015'
EXE=MAIN/'.local/builds/historical22-active-queue-helper-20261015/historical22-active-queue-05.test.exe'
ATTEMPT=sys.argv[1] if len(sys.argv)>1 else '01'
assert ATTEMPT in ('01','02','03','04','05')
DB=MAIN/f'.local/builds/historical22-active-queue-helper-20261015/closed-source22-{ATTEMPT}.sqlite'
RECORD=OUT/f'closed-source22-{ATTEMPT}.json'
TMP=MAIN/f'.local/builds/historical22-active-queue-helper-20261015/run-tmp-{ATTEMPT}'
assert EXE.is_file() and not DB.exists() and not RECORD.exists() and not TMP.exists()
TMP.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();allow={'RESEARCHOS_HISTORICAL22_FIXTURE_OUT':str(DB),'RESEARCHOS_HISTORICAL22_RECORD_OUT':str(RECORD),'RESEARCHOS_HISTORICAL22_WORKSPACE':str(MAIN/f'.local/builds/historical22-stable-workspace-20261015/workspace-{ATTEMPT}'),'TMP':str(TMP),'TEMP':str(TMP)};env.update(allow)
argv=[str(EXE),'-test.run','^TestHistorical22ActiveQueueFixtureChild$','-test.v']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=SRC/'internal/domain',env=env,capture_output=True)
(OUT/f'run-helper-{ATTEMPT}.stdout.raw').write_bytes(r.stdout);(OUT/f'run-helper-{ATTEMPT}.stderr.raw').write_bytes(r.stderr)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inv={'actualargv':argv,'cwd':str(SRC/'internal/domain'),'allowlist_env':allow,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':r.returncode,'test_exe_sha256':sha(EXE),'closed_db_sha256':sha(DB) if DB.exists() else None,'record_sha256':sha(RECORD) if RECORD.exists() else None}
(OUT/f'run-helper-{ATTEMPT}.invocation.json').write_text(json.dumps(inv,indent=2)+'\n',encoding='utf-8')
print(json.dumps(inv,ensure_ascii=False))
raise SystemExit(r.returncode)
