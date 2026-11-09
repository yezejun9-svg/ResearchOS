import hashlib,json,subprocess,datetime
from pathlib import Path
R=Path(r'D:/作品集/ResearchOS/research-os'); O=Path(__file__).resolve().parent
C='125ea34ca0878f18c4dce47f9259ab5e9e77c2eb'; F='fef0ee2d56351e74ceed11b0b37d3f87e9c83494'; B='396287cc5427eb125aaedb8a2b7fadf63e6b9322'
def h(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
calls=[]
def git(tag,args):
 a=['git']+args;t=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(a,cwd=R,capture_output=True)
 (O/(tag+'.stdout.raw')).write_bytes(r.stdout);(O/(tag+'.stderr.raw')).write_bytes(r.stderr)
 calls.append({'argv':a,'cwd':str(R),'at':t,'exit':r.returncode,'stdout':tag+'.stdout.raw','stdout_sha256':h(r.stdout),'stderr':tag+'.stderr.raw','stderr_sha256':h(r.stderr)})
 if r.returncode:raise RuntimeError(tag)
 return r.stdout
exact=['internal/domain/backup_upgrade.go','internal/domain/backup_migration.go','internal/domain/backup.go','internal/domain/store.go','internal/domain/backup_configuration_upgrade.go','internal/domain/backup_configuration_upgrade_test.go','internal/domain/backup_host_configuration.go','internal/domain/backup_host_configuration_test.go','internal/domain/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.domain.schema.json']
found=['migrations/sqlite/0023_host_model_configuration.sql','internal/domain/client_configuration.go','internal/domain/client_configuration_test.go','internal/domain/client_command_identity.go','internal/domain/client_command_identity_test.go']
blobs=[]
for i,path in enumerate(exact+found):
 b=git('source-%02d'%i,['show',C+':'+path]);blobs.append({'path':path,'commit':C,'sha256':h(b),'bytes':len(b),'raw':'source-%02d.stdout.raw'%i})
 for j,base in enumerate([F] if path in found else [B] if path in exact[:4] else []):
  old=git('before-%02d-%d'%(i,j),['show',base+':'+path]);blobs[-1]['before']={'commit':base,'sha256':h(old),'same':old==b}
git('production-diff',['diff',B,C,'--']+exact)
git('commit-paths',['diff-tree','--no-commit-id','--name-only','-r',C])
receipt='execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/handoff-5375496dd2b24206b5db17fc9bc358c3/'
for i,name in enumerate(['handoff.json','final_handoff.json','current_compiled_closure_audit.json','source.before_after.json','manifest.json']):git('handoff-'+str(i),['show',C+':'+receipt+name])
refs=['execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-schema-mirror-scope-r271/scope_registration.json','execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_scope_review_codex/2c7bb855-7562-41b6-8c8e-5456f9fc81dc/review.json','execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644/source_review.json']
refrows=[]
for i,path in enumerate(refs):
 p=R/path;b=p.read_bytes();(O/('authority-%d.json'%i)).write_bytes(b);refrows.append({'path':str(p),'sha256':h(b),'snapshot':'authority-%d.json'%i})
save('source_snapshot.json',blobs);save('authority_refs.json',refrows);save('static_invocations.json',calls)
save('review_plan.pending.json',{'reviewer':'codex:/root/command_queue_impl','status':'STATIC_REVIEW_IN_PROGRESS_NO_EXECUTION','upgrade_author':'codex:/root/sources_parent_impl','prior_foundation_author':'codex:/root/command_queue_impl','independence_boundary':'Independently review upgrade exact10 and pendingtest1; foundation5 compared bytewise and rely on separate c4ca independent review, no self acceptance of foundation.','candidate':C,'awaiting':'Root CP277 exact11 registration and finaltest commit/handoff before ANY executable/test run','selectors_provisional':['TestConfigurationUpgrade','TestHostConfigurationBackup','TestMigration','TestQueueUpgrade','authorized final single fresh-schema regression test exact name afterhandoff'],'review_focus':['G01 program/root matching external evidence not enforced by runtime hash alone','G02 numbered22 without additive failsbeforepublication','host-only authority startup migration refusal','complete typed3 history+globalsolejournal+schema','faultrollback/source lock throughrename and WAL limited guarantee','publicactivequeue/UNKNOWN/exactrecovertransform','protected historical unchanged/hash closure/8publicclosedDB'],'production_changes':0,'program_tests_started':0,'private_resource_reads':0,'formal_increment':0})
print(json.dumps({'out':str(O),'frozen_sources':len(blobs),'foundation_unchanged':all(x['before']['same'] for x in blobs if x['path'] in found)},ensure_ascii=True))
