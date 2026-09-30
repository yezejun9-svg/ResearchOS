from pathlib import Path
import subprocess,json,hashlib,os,time
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];SNAP=OUT/'source-checkout'
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'));go=Path(lock['tools']['go']['path']);assert hashlib.sha256(go.read_bytes()).hexdigest()==lock['tools']['go']['sha256']
env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off',GOWORK='off',GOFLAGS='-mod=readonly',INDEPENDENT_S2_EVIDENCE=str(OUT))
args=[str(go),'test','-overlay',str(OUT/'overlay.json'),'-count=1','-v','-timeout=90s','./adapters/runtime','./internal/domain','-run','^(TestVerifierBridgeUntrustedFrames|TestRuntimeCoordinatorTypedBroker)$']
start=time.monotonic()
with (OUT/'stdout.log').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:r=subprocess.run(args,cwd=SNAP,env=env,stdout=stdout,stderr=stderr,timeout=120)
(OUT/'command.json').write_text(json.dumps({'argv':args,'cwd':str(SNAP),'exit_code':r.returncode,'seconds':time.monotonic()-start,'go_sha256':hashlib.sha256(go.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps({'exit_code':r.returncode,'seconds':time.monotonic()-start}))
