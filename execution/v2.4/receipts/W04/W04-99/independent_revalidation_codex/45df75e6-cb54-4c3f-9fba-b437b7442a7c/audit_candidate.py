"""Independent source/receipt audit; synthetic unit controls, no collection."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

OUT=Path(__file__).resolve().parent
MAIN=OUT.parents[6]
WT=MAIN/'.local/worktrees/codex-w0799'
PREFIX='execution/v2.4/receipts/W04/W04-99/executor_revalidation_codex'
HERE=WT/PREFIX
OLD=HERE.with_name('executor_codex')
COMMIT='2ab648416690625c3aa65ef6ae2a95a577fde85d'
RUN=HERE/'runs/9f534896be79477c98ea81a75234e2c9'
def require(v,s):
    if not v:raise ValueError(s)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':sha(p)}
def save(name,v):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=WT)
require(git('rev-parse','HEAD').decode().strip()==COMMIT,'candidate HEAD')
require(not git('status','--porcelain','--untracked-files=no').strip(),'candidate tracked dirt')
expected={'source-handoff.json':'66180d47faabdb63e142710aa7c46477353436b5c2828e12b7c5aa38d9041a48','qualification.json':'66a58bd2ed1d225ba590a3562c066f3c6587783266c41e5a40c667bc8e5c1ac4','source-manifest.json':'1dcde6fd2ffe1fd496b309edbaebf7805bc8de1fdfa43894c7160a3908738fd0'}
for n,h in expected.items():require(sha(RUN/n)==h,'handoff '+n)
paths=git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).decode('utf-8').splitlines()
require(len(paths)==224 and all(p.startswith(PREFIX+'/') for p in paths),'224 namespace only')
batch=subprocess.run(['git','cat-file','--batch'],cwd=WT,input=''.join(COMMIT+':'+p+'\n' for p in paths).encode(),capture_output=True,check=True).stdout
offset=0;blobs=[]
for p in paths:
    end=batch.index(b'\n',offset);header=batch[offset:end].split();require(header[1]==b'blob','blob type')
    size=int(header[2]);body=batch[end+1:end+1+size];offset=end+size+2
    require(body==(WT/p).read_bytes(),'commit/worktree blob differs '+p)
    blobs.append({'path':p,'git_blob':header[0].decode(),'sha256':digest(body),'bytes':size})
require(offset==len(batch),'batch trailing data')
scope_path=MAIN/'execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/scope_registration.json'
scope=read(scope_path);handoff=read(RUN/'source-handoff.json')
require(set(scope['executor_source_scope'])=={r['candidate']['path'] for r in handoff['sources']},'exact nine scope')
sources=[]
for r in handoff['sources']:
    p=WT/r['candidate']['path'];require(sha(p)==r['candidate']['sha256'],'source hash')
    if r['original']:
        op=WT/r['original']['path'];require(sha(op)==r['original']['sha256'],'old source hash')
        require((p.read_bytes()==op.read_bytes())==r['byte_identical'],'identity claim')
    sources.append(ref(p))
legacy=read(HERE/'frozen_inputs/legacy_entries.json');prior=read(OLD/'frozen_inputs/legacy_entries.json')
prior['registry_ref']['path']=PREFIX+'/frozen_inputs/commands-v24-r37.json'
require(legacy==prior,'legacy payload changed')
package=HERE/'frozen_inputs/package';manifest=read(package/'PACKAGE_MANIFEST.json')
require(len(manifest['files'])==147,'manifest entries')
package_expected={r['path']:r['sha256'] for r in manifest['files']};package_expected['PACKAGE_MANIFEST.json']=sha(package/'PACKAGE_MANIFEST.json')
package_actual={p.relative_to(package).as_posix():sha(p) for p in package.rglob('*') if p.is_file()}
require(package_actual==package_expected and len(package_actual)==148,'package inventory')
for n,h in package_actual.items():require(sha(OLD/'frozen_inputs/package'/n)==h,'old package '+n)
prefixes={str(root):digest((root/'execution/v2.4/formal_case_index.py').read_bytes()[:51719]) for root in (MAIN,WT)}
require(set(prefixes.values())=={'92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1'},'formal prefix')
old_before=read(RUN/'protected-old-tree-before.json')
require(old_before==read(RUN/'protected-old-tree-after.json'),'old before/after')
for n,h in old_before.items():
    p=OLD/n
    require(p.suffix.lower() not in {'.sqlite','.sqlite3','.db'} and not p.name.endswith(('-wal','-shm')),'private DB not read '+n)
    require(sha(p)==h,'old tree actual drift '+n)
actual_old={p.relative_to(OLD).as_posix() for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
require(actual_old==set(old_before),'old tree added/deleted')
rounds=[]
for run in sorted((HERE/'runs').iterdir()):
    if not run.is_dir():continue
    require(read(run/'protected-old-tree-before.json')==read(run/'protected-old-tree-after.json')==old_before,'older protected history')
    require(read(run/'candidate-source-before.json')==read(run/'candidate-source-after.json'),'round source drift')
    invocations=[]
    for p in sorted(run.glob('*.invocation.json')):
        inv=read(p)
        for key in ('stdout_ref','stderr_ref'):require(sha(Path(inv[key]['path']))==inv[key]['sha256'],'raw ref '+str(p))
        stderr=Path(inv['stderr_ref']['path']).read_text(encoding='utf-8')
        count=re.search(r'Ran (\d+) tests?',stderr)
        invocations.append({'receipt_ref':ref(p),'exit_code':inv['exit_code'],'raw_refs':[inv['stdout_ref'],inv['stderr_ref']],'unittest_count':int(count.group(1)) if count else None,'unittest_OK':bool(re.search(r'^OK$',stderr,re.M)),'skipped':bool(re.search(r'skipped[= ]',stderr,re.I))})
    rounds.append({'run':run.name,'qualification_ref':ref(run/'qualification.json'),'invocations':invocations})
require(len(rounds)==3,'three preserved rounds')
latest=next(x for x in rounds if x['run']==RUN.name)
require(all(x['exit_code']==0 for x in latest['invocations']),'latest real raw exit')
require(sorted(x['unittest_count'] for x in latest['invocations'] if x['unittest_count'] is not None)==[4,9],'actual latest rosters')
require(all(not x['skipped'] for x in latest['invocations']),'no skip')
assignment=MAIN/handoff['actor_assignment_ref']['path']
require(sha(assignment)==handoff['actor_assignment_ref']['sha256'],'real assignment')
locked=read(WT/'execution/toolchains/locked.json')
require(sha(Path(sys.executable))==locked['tools']['python']['sha256'],'review python locked')
for name in ('python','go'):require(sha(Path(locked['tools'][name]['path']))==locked['tools'][name]['sha256'],'actual tool bytes')
# Execute only the unchanged test helpers in an explicit isolated synthetic root.
# No test writes to peer WT; no actual collect/main or provider invocation.
synthetic=OUT/'SYNTHETIC_NOT_PRODUCT';new=synthetic/PREFIX;old=new.with_name('executor_codex')
for row in handoff['sources']:
    src=WT/row['candidate']['path'];dst=synthetic/row['candidate']['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for name in ('bridge.py','collect.py','test_bridge.py','parent_driver.py','evidence_module.py','expected.json','frozen_inputs/commands-v24-r37.json','frozen_inputs/legacy_entries.json'):
    target=old/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/name,target)
shutil.copytree(package,new/'frozen_inputs/package');shutil.copytree(OLD/'frozen_inputs/package',old/'frozen_inputs/package')
target=synthetic/'execution/toolchains/locked.json';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(WT/'execution/toolchains/locked.json',target)
unit_runs=[]
for name,count in [('test_collect.py',9),('test_bridge.py',4)]:
    argv=[sys.executable,'-B','-X','utf8',str(new/name),'-v'];start=datetime.now(timezone.utc).isoformat()
    env=dict(os.environ,RESEARCHOS_W04_ACTOR_ASSIGNMENT=str(assignment),PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run(argv,cwd=synthetic,env=env,capture_output=True)
    stem=name.removesuffix('.py')
    for kind,raw in [('stdout',result.stdout),('stderr',result.stderr)]:
        with (OUT/(stem+'.'+kind)).open('xb') as f:f.write(raw)
    record={'classification':'SYNTHETIC_NOT_PRODUCT','actual_argv':argv,'cwd':str(synthetic),'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout_ref':ref(OUT/(stem+'.stdout')),'stderr_ref':ref(OUT/(stem+'.stderr')),'expected_tests':count}
    save(stem+'.invocation.json',record);unit_runs.append(record)
    require(result.returncode==0 and re.search(r'Ran '+str(count)+r' tests?',result.stderr.decode()) and re.search(r'^OK$',result.stderr.decode(),re.M),'independent unit '+name)
require(all(sha(WT/p['path'])==p['sha256'] for p in blobs),'candidate changed during independent review')
audit={'schema':'researchos.w04.independent-collector-source-audit.v1','actor':'codex:/root/w05_merge_review','at':datetime.now(timezone.utc).isoformat(),'candidate_commit':COMMIT,'status':'PASS','scope_ref':ref(scope_path),'assignment_ref':ref(assignment),'handoff_ref':ref(RUN/'source-handoff.json'),'manifest_ref':ref(RUN/'source-manifest.json'),'qualification_ref':ref(RUN/'qualification.json'),'commit_blob_count':len(blobs),'blobs':blobs,'exact_sources':sources,'package_manifest_entry_count':147,'package_total_file_count':148,'old_tree_verified_files':len(old_before),'old_tree_inventory_ref':ref(RUN/'protected-old-tree-before.json'),'formal_prefix_51719':prefixes,'preserved_attempts':rounds,'independent_unit_runs':unit_runs,'actual_product_collection':False,'native_dispatches_executed':0,'private_DB_read':False,'source_canonical_edits':0}
save('audit.json',audit)
print(json.dumps({'status':'PASS','audit_ref':ref(OUT/'audit.json'),'commit_blobs':len(blobs),'independent_controls':13,'preserved_rounds':[(x['run'],[i['exit_code'] for i in x['invocations']]) for x in rounds]},ensure_ascii=False))
