import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
SRC=MAIN/'.local/resources/historical22-active-queue-helper-20261015'
GO=MAIN/'.local/tools/go1.27.1/go'
ATTEMPT=sys.argv[1] if len(sys.argv)>1 else '01'
assert ATTEMPT in ('01','02','03','04','05')
TMP=MAIN/f'.local/builds/historical22-active-queue-helper-20261015/tmp-{ATTEMPT}'
EXE=MAIN/f'.local/builds/historical22-active-queue-helper-20261015/historical22-active-queue-{ATTEMPT}.test.exe'
assert SRC.is_dir() and not EXE.exists() and not TMP.exists()
TMP.mkdir(parents=True,exist_ok=False)
env=os.environ.copy()
allow={'GOROOT':str(GO),'GOTOOLCHAIN':'local','GOENV':'off','GOPATH':str(MAIN/'.local/gopath'),'GOCACHE':str(MAIN/'.local/gocache'),'GOPROXY':'off','GOSUMDB':'off','GOTMPDIR':str(TMP),'TMP':str(TMP),'TEMP':str(TMP)}
env.update(allow)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(SRC).as_posix():sha(p) for p in SRC.rglob('*') if p.is_file()}
assert len(before)==503
(OUT/f'historical-input-before-{ATTEMPT}.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
argv=[str(GO/'bin/go.exe'),'test','-c','-buildvcs=false','-o',str(EXE),'./internal/domain']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
result=subprocess.run(argv,cwd=SRC,env=env,capture_output=True)
(OUT/f'build-helper-{ATTEMPT}.stdout.raw').write_bytes(result.stdout)
(OUT/f'build-helper-{ATTEMPT}.stderr.raw').write_bytes(result.stderr)
after={p.relative_to(SRC).as_posix():sha(p) for p in SRC.rglob('*') if p.is_file()}
(OUT/f'historical-input-after-{ATTEMPT}.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
record={'actualargv':argv,'cwd':str(SRC),'allowlist_env':allow,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':result.returncode,'input_count':len(before),'input_unchanged':before==after,'helper_sha256':before['internal/domain/active_queue_fixture_child_test.go'],'go_exe_sha256':sha(GO/'bin/go.exe'),'test_exe_sha256':sha(EXE) if EXE.exists() else None}
(OUT/f'build-helper-{ATTEMPT}.invocation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
raise SystemExit(result.returncode if before==after else 2)
