import ast
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
DRAFT=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-exact1-r312'
PINS={'register.py':'0a60043f9b5e962679a2c0b8c558363cfcf12a80ddbf936bf066bafcaa2d13ef','run.py':'807d88a1b80e76fa41a277278f83047820543e330389b0899824aafb8f8432c8','prepared_refs.json':'697cf3703f454579e79bbb21aef52539acdf81613177c4d62ef45ef076911882','audit.json':'1960f875d8113f19763ba9235d9958a2f0729202cd7fe267564f0e97f5543bbe','scope_registration.json':'31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'}
def digest(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest(b),'bytes':len(b)}
def save(n,obj):
 with (HERE/n).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def require(v,s):
 if not v:raise RuntimeError(s)
for n,h in PINS.items():require(digest((DRAFT/n).read_bytes())==h,'draft pin '+n)
prepared=json.loads((DRAFT/'prepared_refs.json').read_bytes())
scope=json.loads((DRAFT/'scope_registration.json').read_bytes())
checked=[]
for pin in prepared['verified_refs']:
 p=ROOT/pin['path']; actual=ref(p);require(actual==pin,'ref '+pin['path']);checked.append(actual)
snapshots=[]
before=[]
for i,pin in enumerate(prepared['canonical_before']):
 p=ROOT/pin['path'];b=p.read_bytes();require(ref(p)==pin,'canonical '+pin['path']);before.append(b)
 copy=HERE/f'canonical-before-{i+1}-{p.name}'
 with copy.open('xb') as f:f.write(b)
 snapshots.append(ref(copy))
cp,ow=json.loads(before[0]),json.loads(before[1])
require([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[311,139,384],'revisions')
keys=[r.get('origin_key') for r in prepared['origins']]
require(len(keys)==len(set(keys))==2,'unique new origins')
require(not set(keys)&{r.get('origin_key') for r in cp['failure_counters']},'already imported')
require(prepared['origins']==json.loads((DRAFT/'audit.json').read_bytes())['new_origins'],'audit origins')
require(prepared['origins']==json.loads((DRAFT/'failure-origins.cut.json').read_bytes())['origins'],'cut origins')
require(prepared['origins'][0]['actual_native_case_exit']==0 and prepared['origins'][1]['actual_native_exit'] is None,'origin classification')
require(scope['exact_paths']==['internal/api/v2_sessions_test.go'] and not Path(scope['worktree']).exists(),'exact1/new WT')
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes())['tools']
for name in ['python','git']:require(digest(Path(lock[name]['path']).read_bytes())==lock[name]['sha256'],'tool '+name)
git=lock['git']['path']
git_observations=[]
def query(args,cwd=ROOT):
 r=subprocess.run([git,*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 idx=len(git_observations)+1
 for kind,raw in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (HERE/f'git-{idx:02d}.{kind}.raw').open('xb') as f:f.write(raw)
 git_observations.append({'argv':[git,*args],'cwd':str(cwd),'actual_exit':r.returncode,'stdout_ref':ref(HERE/f'git-{idx:02d}.stdout.raw'),'stderr_ref':ref(HERE/f'git-{idx:02d}.stderr.raw')})
 require(r.returncode==0,'git readonly query failed')
 return r.stdout
head=query(['rev-parse','HEAD']).decode().strip()
status=query(['status','--porcelain=v1','--untracked-files=no'])
require(head==prepared['head']==cp['head'],'HEAD')
require(digest(status)==prepared['git_status_sha256'],'status')
require(len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11,'13status/11D')
require(query(['diff','--cached','--name-only'])==b'','index')
g2=ROOT/'.local/worktrees/codex-w0599-provider-g2-finite-r307'
require(query(['rev-parse','HEAD'],g2).decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9','G2 HEAD')
require(query(['status','--porcelain=v1'],g2)==b'','G2 status')
source=query(['show',scope['base_commit']+':internal/api/v2_sessions_test.go'])
domain=query(['show',scope['base_commit']+':internal/domain/client_protocol_sessions.go'])
old=query(['show','22752a6a41732c8c158d7d7e1b8932ec958f8cb8:internal/api/v2_sessions_test.go'])
require(digest(source)=='e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0','base test')
require(digest(domain)=='7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3','base domain')
require(len(old)==14633 and digest(old)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1','old body')
for name in ['register.py','run.py']:
 raw=(DRAFT/name).read_bytes();ast.parse(raw,filename=name)
 with (HERE/('reviewed-'+name)).open('xb') as f:f.write(raw)
for name in ['prepared_refs.json','audit.json','scope_registration.json','source_before.json','failure-origins.cut.json']:
 with (HERE/('reviewed-'+name)).open('xb') as f:f.write((DRAFT/name).read_bytes())
after=[]
for pin,b in zip(prepared['canonical_before'],before):
 p=ROOT/pin['path'];require(p.read_bytes()==b,'canonical moved');after.append(ref(p))
for n,h in PINS.items():require(digest((DRAFT/n).read_bytes())==h,'draft moved')
audit={'verified_refs_count':len(checked),'verified_refs':checked,'ordered_canonical_before':prepared['canonical_before'],'after':after,'git_observations':git_observations,
 'drafts_parsed_only_not_imported_or_executed':True,'code_tests_SQL_models':0,'new_failure_origins':[],
 'source_base_test_bytes':len(source),'protected_old_body_bytes':len(old),'protected_old_body_sha256':digest(old),
 'static_transaction_review':[
 'Wrapper pins reviewer/decision/four draft hashes/ordered four byte-identical snapshots before launching isolated unoptimized pinned Python.',
 'Registrar pins four canonical originals, HEAD/status/empty index, all18 refs, newWT absence and two distinct origins. It only appends old384 and new failure-chain; no old failure reset.',
 'Checkpoint/ownership desired files and all four original snapshots are persisted before mutation; intent describes own-original/desired forward-only recovery.',
 'Every os.replace rechecks all four current expected bytes and HEAD/status. expected_live and cached READS are updated immediately, preventing stale handoff refs.',
 'After both writes, verifies312/140/386, old384 prefix, step_state/commands bytes, formal status and HEAD/status; done/exception journal preserve partial transaction state.',
 'No automatic recovery is run; future recovery requires exact own original/desired plus unchanged other state. Root remains sole writer.',
 'Scope grants only test path at freshWT, preserves domain/old14633/Rootassert/oldDBsidecars. Fourteen fresh fixture cases require fresh compiler/exe, max224 localHTTP; no SDK/model/Node/external/private.',
 'CLI221 update records finite union while source-ready flags remain false; no Main/product/formal acceptance. Existing Desktop and unrelated W05 bindings are untouched by inspected mutation statements.'
 ],
 'wrapper_limit':'Popen/prelaunch exceptions are not converted into a wrapper invocation.json by this wrapper; no canonical write can occur before launch, and registrar owns durable intent/partial-write journal. Actual outer tool/raw must remain authoritative for such failures.'}
save('audit.json',audit)
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],'actual_registration_executed':False,
 'expected_before':[311,139,384],'expected_after':[312,140,386],
 'register_sha256':PINS['register.py'],'wrapper_sha256':PINS['run.py'],'prepared_refs_sha256':PINS['prepared_refs.json'],'audit_sha256':PINS['audit.json'],
 'canonical_before':prepared['canonical_before'],'copied_canonical_before_refs':snapshots,
 'reviewed_at':datetime.now(timezone.utc).isoformat(),'scope_ref':ref(DRAFT/'scope_registration.json'),'independent_audit_ref':ref(HERE/'audit.json'),
 'conditions':['Root alone executes pinned reviewed wrapper exactly once against unchanged four canonical pins/HEAD/status.','New exact1 implementation remains separately nonauthor-reviewed; this registration review accepts neither test correction source nor product/Main/formal outcome.'],
 'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]}
save('review.json',review)
files=[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file()]
save('manifest.json',{'entries':files,'count':len(files)})
save('handoff.json',{'review_ref':ref(HERE/'review.json'),'manifest_ref':ref(HERE/'manifest.json'),'independent_audit_ref':ref(HERE/'audit.json'),'actual_registration_executed':False,'new_failure_origins':[]})
print(json.dumps({'review':ref(HERE/'review.json'),'manifest':ref(HERE/'manifest.json'),'handoff':ref(HERE/'handoff.json'),'refs_verified':len(checked),'git_actual_exit':[x['actual_exit'] for x in git_observations]},ensure_ascii=False,indent=2))
