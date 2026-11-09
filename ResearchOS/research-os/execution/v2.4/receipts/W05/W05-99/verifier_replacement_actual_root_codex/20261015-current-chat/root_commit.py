"""One explicit Root commit of the already reviewed exact plan; no recovery/retry."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');I=R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_independent_observer_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert len(sys.argv)==4
plan=E/'replacement-plan-01.json';assert sys.argv[1]==sha(plan)=='8ba3ed5d6a1cc467b2e8539d3c90ff710c3038b913aea8937e3e20989393cefe'
independent=Path(sys.argv[2]).resolve();assert independent.parent==I and sha(independent)==sys.argv[3] and len(sys.argv[3])==64
amend=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp493/actual-verifier-replacement-scope-amendment01.json';assert sha(amend)=='36118c237961a1d5bea414c1ede5934316869d07deaa0f16a207312cad1a3edb'
independent_plan=I/'02-preflight-plan-review.json';assert sha(independent_plan)=='40c1f69142777a02312272e74b7fc10f7c6d226ed3479979fb88b630926a6e25'
assert read(independent_plan)['result']=='PLAN_BINDINGS_MATCH_WITH_ACTUAL_SHM_DIFFERENCE'
rootinspection=E/'02-root-plan-inspection.json';inspection=read(rootinspection);assert inspection['plan_ref']['sha256']=='sha256:'+sha(plan) and inspection['other_registration_fields_unchanged']
p=read(plan);data=Path(p['data_root']);record=data/'host/runtime-verifier-installation.json'
assert 'sha256:'+sha(record)==p['old_record_sha256']=='sha256:c5650d6fb6aa6d8bd9648aba233d75ed2f46637810f32112968e845d96f7c1c4'
exe=Path(read(E/'01-preflight.invocation.json')['argv'][0]);assert sha(exe)=='c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24'
assert 'sha256:'+sha(Path(p['manifest']))==p['manifest_sha256']
b=read(I/'01-baseline.json')
for name in ['researchos.sqlite','researchos.sqlite-wal','host\\host_state.json']:
 v=b['public_files'][name];assert sha(Path(v['path']))==v['sha256']
argv=[str(exe),'--runtime-verifier-replacement','commit','--data-root',str(data),'--plan',str(plan),'--expect-plan-sha256','sha256:'+sha(plan)]
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA'] if k in os.environ}
new(E/'03-root-explicit-commit-decision.json',{'schema':'researchos.root-explicit-commit-decision.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operator':'codex:/root','action':'COMMIT_EXACT_REVIEWED_PLAN_ONCE','plan_ref':ref(plan),'root_inspection_ref':ref(rootinspection),'independent_preflight_manifest_ref':ref(independent),'independent_plan_review_ref':ref(independent_plan),'scope_amendment_ref':ref(amend),'operation_id':p['operation_id'],'argv':argv,'cwd':str(E),'environment_allowlist':env,'exe_ref':ref(exe),'script_ref':ref(Path(__file__)),'automatic_retry':False,'automatic_recovery':False,'formal_increment':0})
with (E/'03-commit.stdout.raw.json').open('xb') as out,(E/'03-commit.stderr.raw.txt').open('xb') as err:
 result=subprocess.run(argv,cwd=E,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=45)
new(E/'03-commit.result.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_exit':result.returncode,'stdout_ref':ref(E/'03-commit.stdout.raw.json'),'stderr_ref':ref(E/'03-commit.stderr.raw.txt'),'actual_registration_ref':ref(record) if record.exists() else None,'formal_increment':0})
print((E/'03-commit.result.json').read_text(encoding='utf8'))
assert result.returncode==0
out=read(E/'03-commit.stdout.raw.json');assert out['state']=='COMMITTED' and out['outcome']=='APPLIED'
assert 'sha256:'+sha(record)==p['new_record_sha256']
