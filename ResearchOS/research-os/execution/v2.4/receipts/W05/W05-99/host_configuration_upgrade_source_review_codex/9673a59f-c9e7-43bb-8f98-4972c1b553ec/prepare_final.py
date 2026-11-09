from pathlib import Path
import json,subprocess,hashlib,os,datetime,tarfile,io,sys
sys.stdout.reconfigure(encoding='utf-8')
R=Path('D:/作品集/ResearchOS/research-os'); W=R/'.local/worktrees/codex-w0599-host-configuration-upgrade'; O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec'; C='c82f73cc6699b564f1357472e2859b90cafe6b0a'; P='execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex'; F=W/P/'test-scope-r276-180e5f4f0b424c7a8c7b8dbe1e4c52c0'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v): (O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def git(*a):return subprocess.check_output(['git','--no-replace-objects','-C',str(W),*a])
checks=[]
for file,expected in [('handoff.json','d3f345ca83c3befb5065ced30dc0b647c41ea84c613c4996fcaab575e0bb5f96'),('manifest.json','c6f29115f43f738e6541803ed2b0085badad2a04e572377732297eb3f2b14b70')]:
 b=(F/file).read_bytes();assert sha(b)==expected;checks.append({'path':str(F/file),'sha256':sha(b)})
manifest=json.loads((F/'manifest.json').read_text(encoding='utf-8-sig'));rows=manifest['files']; paths=[]
for x in rows:
 b=(W/x['path']).read_bytes();assert sha(b)==x['sha256'];assert git('show',C+':'+x['path'])==b;paths.append(x['path'])
new=git('diff-tree','--no-commit-id','--name-only','-r',C).decode().splitlines();source=[p for p in new if not p.startswith('execution/')];assert source==['internal/domain/backup_command_queue_test.go']
old=git('show','125ea34ca0878f18c4dce47f9259ab5e9e77c2eb:'+source[0]);newsrc=git('show',C+':'+source[0]);a=b'func TestClientQueueFreshNumberedSchema';z=b'func TestClientQueueBackupAllPhasesAndPendingControl';assert old[:old.index(a)]==newsrc[:newsrc.index(a)];assert old[old.index(z):]==newsrc[newsrc.index(z):]
for x in json.loads((F/'exact11_foundation5_git_blobs.json').read_text(encoding='utf-8-sig'))['rows']:
 b=git('show',C+':'+x['path']);assert sha(b)==x['sha256'];checks.append({'path':x['path'],'sha256':sha(b),'bytes':len(b)})
save('final_commit_audit.json',{'candidate':C,'manifest_entries':len(rows),'changed_blobs':len(new),'source':source,'protected_exterior_equal':True,'checks':checks,'changed_paths':new})
D=R/'.local/independent-configuration-9673a59f';D.mkdir(exist_ok=False)
top=git('ls-tree','--name-only',C).decode().splitlines();selected=[x for x in top if x in ['apps','internal','adapters','migrations','spec','packages','contracts','schemas','ops','tests','go.mod','go.sum','AGENTS.md']]
raw=git('archive',C,*selected)
with tarfile.open(fileobj=io.BytesIO(raw)) as t:t.extractall(D,filter='data')
evalfiles=git('ls-tree','-r','--name-only',C,'evaluation').decode().splitlines();public=[p for p in evalfiles if p.endswith('.go') and not p.endswith('_test.go')]
for p in public:
 dest=D/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(git('show',C+':'+p))
save('checkout.json',{'commit':C,'directory':str(D),'archive_trees':selected,'evaluation_compile_only':public,'test_data_read':False})
env=json.loads((W/P/'closure-6e184bfb0e35426ab6f38707d3eeb5eb/environment.json').read_text(encoding='utf-8-sig'));env['GOCACHE']=str(R/'.local/independent-configuration-cache-9673a59f');env['RESEARCHOS_CONFIGURATION_CURRENT_TEST_EXE']=str(O/'domain.test.exe');env['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']=str(O/'actual-fixtures');save('environment.json',env)
print(json.dumps({'manifest':len(rows),'changed':len(new),'checkout':str(D),'verified_source':len(checks)-2}))
