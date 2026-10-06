from pathlib import Path
import subprocess,json,hashlib,datetime,os
out=Path(__file__).resolve().parent; repo=out.parents[3]; snap=out/'snapshot-1d9d579'; env=os.environ.copy(); overrides={'GOPROXY':'off','GOSUMDB':'off','GOTOOLCHAIN':'local','VERIFIER_W09_DATA':str(out/'synthetic-data')}; env.update(overrides)
argv=[str(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'test','-count=1','-v','-run','^TestVerifierW09','./internal/domain']; start=datetime.datetime.now(datetime.timezone.utc).isoformat(); p=subprocess.run(argv,cwd=snap,env=env,capture_output=True)
for name,data in [('stdout',p.stdout),('stderr',p.stderr)]: (out/('regression-probe.'+name+'.txt')).write_bytes(data)
probes={str(path.relative_to(out)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [out/'probe_test.go.txt',out/'additional_test.go.txt']}
(out/'regression-probe-command.json').write_text(json.dumps({'argv':argv,'cwd':str(snap),'environment_overrides':overrides,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'probe_sha256':probes,'go_sha256':hashlib.sha256(Path(argv[0]).read_bytes()).hexdigest()},indent=2),encoding='utf-8')
print('EXIT',p.returncode,'raw saved in',out.name)
