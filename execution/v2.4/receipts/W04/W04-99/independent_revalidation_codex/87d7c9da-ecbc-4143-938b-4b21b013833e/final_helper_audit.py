from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,os,shutil,copy
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/codex-w0599-command-queue'
PREFIX='execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w04-transition-candidate-3d1d3c4e-2f7c-493d-b19d-40bd7147543e'
C=WT/PREFIX;COMMIT='2154e341996dde9b1fbbb32ba53c889e44dec75f'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(n,v):
 with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def need(v,s):
 if not v:raise ValueError(s)
source_expected={'register.py':'4e43adf363c78ade703fa437dcf27e494901547e52e5e523ef3a30ab26de89bd','test_register.py':'e063b336725fe3f32123de3f8be381d1b60a7d929390fffad862f9856e5acbd2','handoff.json':'0a7ba8376cd635cc63b3c30246299cef64fcfc6a52c872cda578b75f9c8a6710'}
for n,h in source_expected.items():need(ref(C/n)['sha256']==h,'source drift '+n)
paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',COMMIT],cwd=WT).decode().splitlines()
need(len(paths)==877 and all(p.startswith(PREFIX+'/') for p in paths),'exact commit scope')
batch=subprocess.run(['git','cat-file','--batch'],cwd=WT,input=''.join(COMMIT+':'+p+'\n' for p in paths).encode(),capture_output=True,check=True).stdout
offset=0;blobs=[]
for p in paths:
 end=batch.index(b'\n',offset);h=batch[offset:end].split();size=int(h[2]);body=batch[end+1:end+1+size];offset=end+size+2
 need(h[1]==b'blob' and body==(WT/p).read_bytes(),'commit body '+p)
 blobs.append({'path':p,'sha256':sha(body),'bytes':size,'git_blob':h[0].decode()})
need(offset==len(batch),'git batch boundary')
manifest=read(C/'manifest.json')
for item in manifest['files']:need(ref(WT/item['path'])['sha256']==item['sha256'],'manifest '+item['path'])
handoff=read(C/'handoff.json');runs=[]
for control in handoff['controls']:
 ip=WT/control['invocation_ref']['path'];inv=read(ip);report=read(WT/control['report_ref']['path'])
 need(ref(ip)['sha256']==control['invocation_ref']['sha256'] and ref(WT/control['report_ref']['path'])['sha256']==control['report_ref']['sha256'],'run refs')
 for kind in ('stdout','stderr'):need(ref(ip.parent/inv[kind]['path'])['sha256']==inv[kind]['sha256'],'raw '+kind)
 need(inv['exit_code']==0 and inv['source_before']==inv['source_after']=={k:source_expected[k] for k in ('register.py','test_register.py')},'run identity')
 need(report['tests_run']==15 and report['failures']==report['errors']==report['skipped']==0,'report counts')
 stderr=(ip.parent/inv['stderr']['path']).read_text(encoding='utf-8');need('Ran 15 tests' in stderr and 'OK' in stderr.splitlines(),'actual raw unit count')
 runs.append({'invocation_ref':ref(ip),'report_ref':ref(WT/control['report_ref']['path']),'actual_exit':0,'optimized':'-O' in inv['actual_argv'],'tests':15,'existing_v1_refusal_controls':control['existing_v1_refusal_controls']})
target=OUT/'SYNTHETIC_HELPER_SOURCE';target.mkdir()
for n in ('register.py','test_register.py'):shutil.copyfile(C/n,target/n)
argv=[sys.executable,'-B','-X','utf8',str(target/'test_register.py'),'--repo-source',str(ROOT),'--out',str(OUT/'independent_controls')]
started=datetime.now(timezone.utc).isoformat();result=subprocess.run(argv,cwd=target,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True)
for k,b in [('stdout',result.stdout),('stderr',result.stderr)]:
 with (OUT/('helper_controls.'+k)).open('xb') as f:f.write(b)
record={'classification':'SYNTHETIC_NOT_PRODUCT','actual_argv':argv,'cwd':str(target),'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout_ref':ref(OUT/'helper_controls.stdout'),'stderr_ref':ref(OUT/'helper_controls.stderr')}
save('helper_controls.invocation.json',record)
need(result.returncode==0,'independent controls exit')
independent=read(OUT/'independent_controls/report.json');need(independent['tests_run']==15 and independent['failures']==independent['errors']==independent['skipped']==0,'independent controls counts')
audit={'schema':'researchos.w04.independent-helper-source-audit.v1','at':datetime.now(timezone.utc).isoformat(),'candidate_commit':COMMIT,'source_refs':[ref(C/n) for n in ('register.py','test_register.py')],'handoff_ref':ref(C/'handoff.json'),'manifest_ref':ref(C/'manifest.json'),'commit_blobs':blobs,'commit_blob_count':877,'manifest_entries':len(manifest['files']),'original_synthetic_runs':runs,'independent_synthetic_invocation_ref':ref(OUT/'helper_controls.invocation.json'),'independent_synthetic_report_ref':ref(OUT/'independent_controls/report.json'),'actual_prepare_apply_recover':False,'new_product_or_provider_calls':0,'canonical_source_changes':0}
save('helper_source_audit.json',audit)
# Resume registry audit: original strict check correctly exposed real revision metadata.
base=ROOT/'execution/v2.4/receipts/W04/W04-99/integration_codex/command-registry-candidate-17a8c4c045da40b6a1acb433998c9243'
old=read(base/'commands-r39.original.json');new=read(base/'commands-r40.candidate.json');wanted=copy.deepcopy(old)
metadata={k:{'before':old.get(k),'after':new.get(k)} for k in old if k!='commands' and old.get(k)!=new.get(k)}
need(set(metadata)=={'revision','revision_note','updated_at'} and old['revision']==39 and new['revision']==40,'exact registry metadata')
for k in metadata:wanted[k]=new[k]
changed=('test.context','test.domain','package.validate');prefix='execution/v2.4/receipts/W04/W04-99/executor_codex/';newprefix=prefix.replace('executor_codex','executor_revalidation_codex')
for k in changed:
 for f in ('argv','expected_artifacts'):wanted['commands'][k][f]=[v.replace(prefix,newprefix) if isinstance(v,str) else v for v in wanted['commands'][k][f]]
need(wanted==new,'unexpected registry command changes')
need(len(set(old['commands'])-set(changed))==29,'unchanged count')
need(ref(ROOT/'execution/v2.4/commands.json')['sha256']==ref(base/'commands-r39.original.json')['sha256'],'live r39 CAS')
for k in changed:
 for name in new['commands'][k]['expected_artifacts']:need((ROOT/name).is_file(),'new target missing')
save('registry_scope_review.json',{'schema':'researchos.w04.independent-registry-candidate-scope-review.v1','reviewer_id':'codex:/root/w05_merge_review','issued_at':datetime.now(timezone.utc).isoformat(),'decision':'EXACT_SCOPE_READY_PENDING_ROOT_HELPER_SOURCE_READY','change_plan_ref':ref(base/'change-plan.json'),'old_ref':ref(base/'commands-r39.original.json'),'candidate_ref':ref(base/'commands-r40.candidate.json'),'live_ref':ref(ROOT/'execution/v2.4/commands.json'),'actual_metadata_changes':metadata,'actual_command_diff':'Only old→new executor namespace within argv and expected_artifacts of three named entries. Every selector/env/limit/other command field unchanged; all29 remaining entries unchanged.','changed_commands':list(changed),'unchanged_other_entries':29,'target_files_exist':True,'conditions':['Candidate helper is currently NEEDS_FIX; do not apply registry yet.','Root serial CAS actual r39 raw/revision immediately before atomic apply; preserve complete original/candidate.','Fresh MAIN source/registry freeze and11 actual native dispatches afterward; this scope review is not product proof.','r40 makes prior A05 exact registry applicability stale; retain old proof/review and revalidate final stable vector.'],'prior_audit_attempts':'history_and_registry_audit.raw failed only because its first walker omitted mapped input_hashes; attempt2 verified history then rejected unlisted top-level updated_at/revision_note. Both originals retained; this audit explicitly records those metadata deltas.','source_registry_canonical_changes':0,'formal_acceptance_delta':0})
print(json.dumps({'helper_audit':ref(OUT/'helper_source_audit.json'),'registry_review':ref(OUT/'registry_scope_review.json'),'independent_controls':15,'actual_exit':result.returncode},ensure_ascii=False))
