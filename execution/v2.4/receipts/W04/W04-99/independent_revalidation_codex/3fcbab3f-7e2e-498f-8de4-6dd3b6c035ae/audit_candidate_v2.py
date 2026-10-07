from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,os,shutil
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/codex-w0599-command-queue'
PREFIX='execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w04-transition-fix-6a8e4fe3-32d1-4a75-b511-0645edca245a'
OLDPREFIX=PREFIX.replace('w04-transition-fix-6a8e4fe3-32d1-4a75-b511-0645edca245a','w04-transition-candidate-3d1d3c4e-2f7c-493d-b19d-40bd7147543e')
C=WT/PREFIX;COMMIT='6d5dbf2f917f37d3fe9e8cec35dbd7dc44a7c7a3'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(n,v):
 with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def need(v,s):
 if not v:raise ValueError(s)
expected={'register.py':'a7cc4305c90209271428d2c95769b515e36a949a1ae13b3d1dc7eef1756cf850','test_register.py':'17bc8c76f16ddf6d44dfbb179228260d8fac4156fce63556e243dc99f92faca5','handoff.json':'c47dc5f3df230f6391bfaffed27698dfc6789b936d0ac84c9a51b0570f3c50dd','manifest.json':'f6f33568ec2ac95ca8ca0df7d3932e655c8fee69e79af0a1c1f7c864578e99a8'}
for n,h in expected.items():need(ref(C/n)['sha256']==h,'source drift '+n)
def blobcheck(commit,paths):
 raw=subprocess.run(['git','--no-replace-objects','cat-file','--batch'],cwd=WT,input=''.join(commit+':'+p+'\n' for p in paths).encode(),capture_output=True,check=True).stdout
 pos=0;res=[]
 for p in paths:
  end=raw.index(b'\n',pos);head=raw[pos:end].split();size=int(head[2]);body=raw[end+1:end+1+size];pos=end+size+2
  need(head[1]==b'blob' and body==(WT/p).read_bytes(),'commit body '+p)
  res.append({'path':p,'sha256':sha(body),'bytes':size,'git_blob':head[0].decode()})
 need(pos==len(raw),'batch boundary');return res
paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',COMMIT],cwd=WT).decode().splitlines()
need(len(paths)==3734 and all(p.startswith(PREFIX+'/') for p in paths),'exact scope')
blobs=blobcheck(COMMIT,paths);manifest=read(C/'manifest.json')
need(len(manifest['entries'])==3733,'manifest count')
need({PREFIX+'/'+i['path'] for i in manifest['entries']}==set(paths)-{PREFIX+'/manifest.json'},'manifest coverage')
for item in manifest['entries']:need(ref(C/item['path'])['sha256']==item['sha256'],'manifest '+item['path'])
oldpaths=subprocess.check_output(['git','ls-tree','-r','--name-only','2154e341996dde9b1fbbb32ba53c889e44dec75f','--',OLDPREFIX],cwd=WT).decode().splitlines()
need(len(oldpaths)==877,'old count');oldblobs=blobcheck('2154e341996dde9b1fbbb32ba53c889e44dec75f',oldpaths)
handoff=read(C/'handoff.json');runs=[]
for control in handoff['final_current_controls']:
 ip=C/control['invocation_ref']['path'];inv=read(ip);rp=C/control['report_ref']['path'];report=read(rp)
 need(ref(ip)['sha256']==control['invocation_ref']['sha256'] and ref(rp)['sha256']==control['report_ref']['sha256'],'refs')
 for kind in ('stdout','stderr'):need(ref(ip.parent/(kind+'.raw'))['sha256']==inv[kind+'_sha256'],'raw '+kind)
 need(inv['exit_code']==0 and inv['script_sha256']==inv['script_after_sha256']==expected['register.py'] and inv['tests_sha256']==inv['tests_after_sha256']==expected['test_register.py'],'run identity')
 need(report['tests_run']==22 and report['failures']==report['errors']==report['skipped']==0,'counts')
 stderr=(ip.parent/'stderr.raw').read_text(encoding='utf-8');need('Ran 22 tests' in stderr and 'OK' in stderr.splitlines(),'raw actual count')
 runs.append({'invocation_ref':ref(ip),'report_ref':ref(rp),'actual_exit':0,'tests':22,'optimized':'-O' in inv['argv']})
target=OUT/'SYNTHETIC_HELPER_SOURCE';target.mkdir()
for n in ('register.py','test_register.py'):shutil.copyfile(C/n,target/n)
argv=[sys.executable,'-B','-X','utf8',str(target/'test_register.py'),'--repo-source',str(ROOT),'--out',str(OUT/'independent_controls')]
started=datetime.now(timezone.utc).isoformat();result=subprocess.run(argv,cwd=target,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True)
for k,b in [('stdout',result.stdout),('stderr',result.stderr)]:
 with (OUT/('helper_controls.'+k)).open('xb') as f:f.write(b)
record={'classification':'SYNTHETIC_NOT_PRODUCT','actual_argv':argv,'cwd':str(target),'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout_ref':ref(OUT/'helper_controls.stdout'),'stderr_ref':ref(OUT/'helper_controls.stderr')}
save('helper_controls.invocation.json',record)
audit={'schema':'researchos.w04.independent-helper-fix-source-audit.v1','at':datetime.now(timezone.utc).isoformat(),'candidate_commit':COMMIT,'source_refs':[ref(C/n) for n in ('register.py','test_register.py')],'handoff_ref':ref(C/'handoff.json'),'manifest_ref':ref(C/'manifest.json'),'commit_blobs':blobs,'commit_blob_count':len(blobs),'manifest_entries':len(manifest['entries']),'original_2154_preserved_blobs':oldblobs,'original_synthetic_runs':runs,'independent_synthetic_invocation_ref':ref(OUT/'helper_controls.invocation.json'),'independent_synthetic_report_ref':ref(OUT/'independent_controls/report.json') if (OUT/'independent_controls/report.json').is_file() else None,'actual_prepare_apply_recover':False,'new_product_or_provider_calls':0,'canonical_source_changes':0}
save('helper_source_audit.json',audit)
need(result.returncode==0,'independent controls exit')
ind=read(OUT/'independent_controls/report.json');need(ind['tests_run']==22 and ind['failures']==ind['errors']==ind['skipped']==0,'independent counts')
print(json.dumps({'audit':ref(OUT/'helper_source_audit.json'),'independent':ref(OUT/'independent_controls/report.json'),'exit':result.returncode},ensure_ascii=False))
