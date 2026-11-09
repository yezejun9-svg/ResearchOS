"""Root's single actual preflight invocation. Never commits or starts services."""
import datetime,hashlib,json,os,subprocess,uuid
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); E=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
scope=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp492/actual-verifier-replacement-scope.json'
assert sha(scope)=='036a859495a8d377fd61f0a328521a31d9c82da69cf2a745e3f77a5ceac29f29'
baseline=R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_independent_observer_codex/20261015-current-chat/01-baseline.json'
assert sha(baseline)=='0a9b31d28c29a757d2e268a17c2229190eda077fd0f94d94806a06fc36369be2'
b=json.loads(baseline.read_text(encoding='utf8'));assert b['global_census']==[0,0,0,0] and b['schema_version_summary']==[24,24,1]
data=Path(b['data_root']);record=data/'host/runtime-verifier-installation.json'
package=Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
exe=package/'apps/desktop/resources/control/researchos-control.exe';manifest=exe.parent/'runtime-verifier-installation.json'
assert sha(exe)=='c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24'
assert sha(record)=='c5650d6fb6aa6d8bd9648aba233d75ed2f46637810f32112968e845d96f7c1c4'
assert sha(manifest)=='74ca846daf8f6ad82692b43dcd3b664fe2970247072546495d05519b01358609'
for v in b['public_files'].values():assert sha(Path(v['path']))==v['sha256']
operation=uuid.uuid4().hex;plan=E/'replacement-plan-01.json';assert not plan.exists()
argv=[str(exe),'--runtime-verifier-replacement','preflight','--data-root',str(data),'--manifest',str(manifest),'--expect-record-sha256','sha256:'+sha(record),'--expect-manifest-sha256','sha256:'+sha(manifest),'--operation-id',operation,'--out',str(plan)]
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA'] if k in os.environ}
new(E/'01-preflight.invocation.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operator':'codex:/root','scope_ref':ref(scope),'baseline_ref':ref(baseline),'argv':argv,'cwd':str(E),'environment_allowlist':env,'operation_id':operation,'exe_ref':ref(exe),'manifest_ref':ref(manifest),'old_record_ref':ref(record),'script_ref':ref(Path(__file__)),'formal_increment':0})
with (E/'01-preflight.stdout.raw.json').open('xb') as out,(E/'01-preflight.stderr.raw.txt').open('xb') as err:
 result=subprocess.run(argv,cwd=E,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=40)
new(E/'01-preflight.result.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':result.returncode,'stdout_ref':ref(E/'01-preflight.stdout.raw.json'),'stderr_ref':ref(E/'01-preflight.stderr.raw.txt'),'plan_ref':ref(plan) if plan.exists() else None,'registration_unchanged':sha(record)==b['public_files']['host\\runtime-verifier-installation.json']['sha256'],'formal_increment':0})
print((E/'01-preflight.result.json').read_text(encoding='utf8'))
assert result.returncode==0
out=json.loads((E/'01-preflight.stdout.raw.json').read_text(encoding='utf8'));assert out['state']=='PREFLIGHT' and out['outcome']=='NOT_APPLIED'
