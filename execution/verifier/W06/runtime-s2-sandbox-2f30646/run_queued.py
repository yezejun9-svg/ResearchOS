from pathlib import Path
import subprocess,os,json,hashlib,datetime,time
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
overlay=json.loads((OUT/'overlay.json').read_text());overlay['Replace'][str(ROOT/'ops/experiment_sandbox/independent_s2_queued_test.go')]=str(OUT/'queued_write_test.go');(OUT/'overlay-queued.json').write_text(json.dumps(overlay,indent=2)+'\n')
lock=json.loads((ROOT/'execution/toolchains/go.json').read_text(encoding='utf-8-sig'));exe=Path(lock['executable']);assert hashlib.sha256(exe.read_bytes()).hexdigest()==lock['executable_sha256']
env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',INDEPENDENT_S2_EVIDENCE=str(OUT/'native'))
args=[str(exe),'test','-json','-count=1','-timeout=20s','-overlay='+str(OUT/'overlay-queued.json'),'./ops/experiment_sandbox','-run','^TestIndependentS2QueuedWriteDeadline$']
start=time.monotonic()
with (OUT/'queued.stdout.jsonl').open('wb') as stdout,(OUT/'queued.stderr.log').open('wb') as stderr:proc=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=35)
receipt={'argv':args,'cwd':str(ROOT),'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'go_executable_sha256':lock['executable_sha256']};(OUT/'queued-command.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));print((OUT/'queued.stdout.jsonl').read_text());print((OUT/'queued.stderr.log').read_text())
