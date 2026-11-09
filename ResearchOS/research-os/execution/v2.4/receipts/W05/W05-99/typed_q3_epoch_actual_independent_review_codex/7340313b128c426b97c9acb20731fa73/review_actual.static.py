from pathlib import Path
import json,hashlib,re
R=Path('D:/作品集/ResearchOS/research-os'); B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
O=B/'typed_q3_epoch_actual_independent_review_codex/7340313b128c426b97c9acb20731fa73'
E=R/'.local/typed-q3-epoch-run-env-3c6a88ed57744a0a/typed-child-evidence'
T=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
P=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pin(p):
 p=Path(p).resolve(); data=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def save(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(p)
checks=[];checked={};mismatches=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def verify(ref):
 expected=dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
 actual=pin(expected['path']);checked[expected['path']]=actual
 if actual!=expected:mismatches.append(dict(expected=expected,actual=actual))
 return actual
def refset(refs):return {str(Path(x['path']).resolve()).casefold():(x['sha256'].removeprefix('sha256:'),x['bytes']) for x in refs}
def members(ref):
 x=read(ref['path'])['members'];return list(x.values()) if isinstance(x,dict) else x
def job_ok(x):
 c=x['result']['job_cleanup'];return not c['errors'] and c['active_processes_last_observed']==0 and all(c[n] for n in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and not x['result']['timed_out'] and x['result']['error'] is None
O.mkdir(parents=True,exist_ok=False)
canonical=[R/'execution/v2.4'/(n+'.json') for n in ('checkpoint','path_ownership','step_state','commands')]
canonical_before=[pin(p) for p in canonical]
closed=read(Q/'validation.closed.json');verify(dict(path=str(Q/'validation.closed.json'),sha256='d2fd6c15fcdb727fff91aa7bd3c53275230ebc42bd2017a544ff8f17becfb113',bytes=14766))
rootcopies=[];childcopies=[]
for folder,destination,mapping in ((Q,'root-actual-evidence',rootcopies),(E,'public-child-evidence',childcopies)):
 for source in sorted(folder.rglob('*')):
  if not source.is_file():continue
  relative=source.relative_to(folder);target=O/destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
  data=source.read_bytes()
  with target.open('xb') as f:f.write(data)
  original=pin(source);copy=pin(target);check('copy:'+destination+'/'+relative.as_posix(),original['sha256']==copy['sha256'] and original['bytes']==copy['bytes'])
  mapping.append(dict(original=original,copy=copy))
check('public child evidence file count',len(childcopies)==50,len(childcopies))
choice=read(Q/'source.integration.choice.json');overlay=read(Q/'source-overlay.json');formatted=read(Q/'formatted.source-members.json');inventory=read(Q/'actual-tagged-compiler-input-inventory.json')
parent=read(B/'integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5/formatted.source-members.json')
expected={Path(x['path']).relative_to(P).as_posix():x for x in parent};testnames=set();external=[]
for item in choice['source_components']:
 for name in ('source_handoff','source_manifest','independent_handoff','independent_manifest'):
  verify(item[name]);external.append(item[name])
 candidate=(B/item['candidate_namespace']/'candidate-root').resolve()
 for ref in members(item['source_manifest'])+members(item['independent_manifest']):verify(ref)
 for ref in members(item['source_manifest']):
  p=Path(ref['path']).resolve()
  if p.is_relative_to(candidate):
   name=p.relative_to(candidate).as_posix();expected[name]=ref
   testnames.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',p.read_text(encoding='utf-8'),re.MULTILINE))
check('43 base plus exact Source replacements produces 49',len(parent)==43 and len(expected)==49 and {k:refset([v]) for k,v in expected.items()}=={k:refset([v]) for k,v in overlay['sources'].items()})
for ref in overlay['sources'].values():verify(ref)
for ref in formatted:verify(ref)
check('formatted source set is exact overlay destination',{str((T/n).resolve()).casefold() for n in expected}==set(refset(formatted)))
check('25 parent names from selected Source equal actual scope',len(testnames)==25 and testnames==set(closed['exact_25_parent_names']))
for name in ('source_overlay_ref','formatted_source_ref','compiler_inventory_ref','compiled_test_ref'):
 verify(closed[name])
for refs in ('build_inputs','product_inventory','compiler_tool_refs'):
 for ref in inventory[refs]:verify(ref)
verify(inventory['GoRef']);verify(inventory['test2json_executable_ref'])
for item in inventory['actual_embed_files']:verify(item['ref'])
check('compiler counts',inventory['package_count']==352 and len(inventory['build_inputs'])==3726 and len(inventory['product_inventory'])==600 and len(inventory['compiler_tool_refs'])==8 and len(inventory['actual_embed_files'])==36)
rawlist=(Q/'tagged-compiler-input-list.stdout.raw').read_text(encoding='utf-8');decoder=json.JSONDecoder();pos=0;pkgs=[];listed=set();embeds=[]
fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
while pos<len(rawlist):
 while pos<len(rawlist) and rawlist[pos].isspace():pos+=1
 if pos==len(rawlist):break
 pkg,pos=decoder.raw_decode(rawlist,pos);pkgs.append(pkg.get('ImportPath'));check('package errors:'+str(pkg.get('ImportPath')),not pkg.get('Error') and not pkg.get('DepsErrors'))
 if not pkg.get('Dir'):continue
 for field in fields:
  for name in pkg.get(field,[]):
   p=Path(name);p=p if p.is_absolute() else Path(pkg['Dir'])/p;listed.add(str(p.resolve()).casefold())
   if field.endswith('EmbedFiles'):embeds.append((pkg['ImportPath'],field,str(p.resolve()).casefold()))
check('raw go list fully reproduces inventory',pkgs==inventory['packages'] and listed==set(refset(inventory['build_inputs'])) and sorted(embeds)==sorted((x['package'],x['field'],str(Path(x['ref']['path']).resolve()).casefold()) for x in inventory['actual_embed_files']))
guards={}
for name,count in (('binary',2),('candidate',50),('compiler',3918),('input',181),('runtime',29)):
 guard=read(Q/(name+'-source-guard.cleanup.actual.json'));guards[name]=guard
 check('guard closed:'+name,guard['verification']=='PASSED' and guard['closed'] and guard['retained_handles_count']==0 and not guard['errors'] and guard['failure'] is None and len(guard['entries'])==count and all(x['verified'] and x['final_path_match'] and x['closed'] for x in guard['entries']))
 for ref in guard['entries']:verify(ref)
check('candidate guard exact input set',refset(guards['candidate']['entries'])==refset(formatted+[pin(Q/'formatted.source-members.json')]))
check('compiler guard exact input set',refset(guards['compiler']['entries'])==refset(inventory['build_inputs']+inventory['product_inventory']+inventory['compiler_tool_refs']+[inventory['GoRef'],pin(Q/'actual-tagged-compiler-input-inventory.json')]))
check('binary guard exact input set',refset(guards['binary']['entries'])==refset([closed['compiled_test_ref'],inventory['test2json_executable_ref']]))
invocations=[]
for ref,exitcode in zip(closed['invocation_refs'],(0,0,0,1)):
 verify(ref);inv=read(ref['path']);invocations.append(inv);verify(inv['stdout_ref']);verify(inv['stderr_ref'])
 check('Job closure:'+Path(ref['path']).name,job_ok(inv) and inv['actual_native_exit']==exitcode and inv['result']['actual_exit']==exitcode)
check('four actual owned jobs',len(invocations)==4 and closed['all_owned_jobs_closed'])
actualenv=invocations[-1]['public_environment'];inputset=refset(guards['input']['entries']);binaryset=refset(guards['binary']['entries'])
for name in ('RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_TEST2JSON'):
 p=str(Path(actualenv[name]).resolve()).casefold();check('held runtime input:'+name,p in inputset)
check('explicit frozen official reporter',invocations[-1]['argv'][0]==actualenv['RESEARCHOS_TEST2JSON'] and actualenv['RESEARCHOS_TEST2JSON_SHA256']=='dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c')
events=[json.loads(l) for l in (Q/'typed-q3-epoch-parent-jsonl.stdout.raw').read_text(encoding='utf-8').splitlines()];starts=set();actions={};errors=[];package=[]
for event in events:
 if event.get('Package')!='researchos.local/research-os/internal/domain':errors.append('wrong package')
 name=event.get('Test');action=event['Action']
 if not name:
  if action in ('start','pass','fail','skip'):package.append(action)
  continue
 if name.split('/',1)[0] not in testnames:errors.append('out of scope:'+name)
 if action=='run':
  if name in starts:errors.append('duplicate run:'+name)
  starts.add(name)
 if action in ('pass','fail','skip'):
  if name not in starts or name in actions:errors.append('invalid terminal:'+name)
  actions[name]=action
check('parent finite event reconciliation',not errors and starts==set(actions) and actions==closed['actions'] and starts==set(closed['started_names']) and testnames.issubset(starts) and package==['start','fail'],errors)
counts={v:sum(a==v for a in actions.values()) for v in ('pass','fail','skip')};check('61 pass 6 fail zero skip',counts=={'pass':61,'fail':6,'skip':0},counts)
childsummaries=[];leafcount=0;runnerpids=[]
for directory in sorted(p for p in E.iterdir() if p.is_dir()):
 inv=read(directory/'child-invocation.json');result=read(directory/'child-result.json');verdict=read(directory/'child-event-verdict.json');parentresult=read(directory/'parent-result.json')
 stdout=(directory/'child.stdout.jsonl').read_bytes();raw=(directory/'child.stdout.raw').read_bytes();stderr=(directory/'child.stderr.raw').read_bytes()
 check('child raw copy and result hashes:'+directory.name,stdout==raw and hashlib.sha256(stdout).hexdigest()==result['stdout_hash'].removeprefix('sha256:') and len(stdout)==result['stdout_bytes'] and hashlib.sha256(stderr).hexdigest()==result['stderr_hash'].removeprefix('sha256:') and len(stderr)==result['stderr_bytes'])
 cev=[json.loads(l) for l in stdout.decode('utf-8').splitlines()];cs=[];ct={};firsterrors=[]
 for ev in cev:
  n=ev.get('Test');a=ev['Action']
  if a=='run':cs.append(n)
  if n and a in ('pass','fail','skip'):ct[n]=a
  if ev.get('OutputType')=='error':firsterrors.append(ev)
 leaves=inv['leaf_cases'];leafcount+=len(leaves);runnerpids.append(result['actual_runner_pid'])
 check('child exact failure scope:'+directory.name,set(cs)==set(leaves+[directory.name]) and len(cs)==len(set(cs)) and all(ct.get(n)=='fail' for n in cs) and cev[-1]['Action']=='fail' and 'Test' not in cev[-1])
 check('child first attach causes:'+directory.name,len(firsterrors)==len(leaves) and {e['Test'] for e in firsterrors}==set(leaves) and all('typed command session.attach:' in e['Output'] and '"status":"ACKNOWLEDGED"' in e['Output'] and '"revision":3' in e['Output'] for e in firsterrors))
 check('child fail closed:'+directory.name,result['actual_runner_exit']==1 and result['actual_native_child_exit'] is None and result['actual_native_child_pid'] is None and result['resources_stable'] and result['runner_process_created'] and not result['child_jsonl_verified'] and not result['passed_observed_scope'] and not verdict['verified'] and not parentresult['child_assertions_passed'] and actions[directory.name]=='fail')
 for resource in inv['tool_resources'].values():verify(dict(path=resource['resolved_path'],sha256=resource['sha256'],bytes=resource['bytes']))
 childsummaries.append(dict(case=directory.name,leaf_cases=leaves,runner_pid=result['actual_runner_pid'],runner_exit=1,native_child_pid=None,native_child_exit=None,first_errors=firsterrors,event_count=len(cev),parent_action=actions[directory.name]))
check('six distinct child runners eight failing leaves',len(childsummaries)==6 and len(set(runnerpids))==6 and leafcount==8)
goal={k:v for k,v in actions.items() if k.startswith('TestClientGoal')};epoch={k:v for k,v in actions.items() if k.startswith('TestClientWorkspace')}
check('Goal component observed pass only',all(v=='pass' for v in goal.values()) and goal.get('TestClientGoalSessionWriterAndSettlementGates/expired_lease')=='pass' and goal.get('TestClientGoalSessionWriterAndSettlementGates/missing_lease')=='pass')
check('epoch component observed pass only',all(v=='pass' for v in epoch.values()) and epoch.get('TestClientWorkspaceImportExactBytesReplayAndEpoch')=='pass')
mainrefs=[x for x in guards['input']['entries'] if Path(x['path']).is_relative_to(R) and not Path(x['path']).is_relative_to(R/'.local') and not Path(x['path']).is_relative_to(B)]
failure=read(Q/'failure-origin.823.json');check('original failure823 preserved',failure['observed_ordinal']==823 and failure['actual_exits']==dict(outer=1,python=1,native_parent_reporter=1,native_compiled_child=None) and failure['counter_reset'] is False)
check('Main not adopted formal not accepted',closed['Main_adopted'] is False and closed['formal_acceptance'] is False and closed['original_trial_DB_touched'] is False and closed['external_model_provider_requests']==0)
check('current CP remains357',read(canonical[0])['revision']==357)
canonical_after=[pin(p) for p in canonical];check('canonical unchanged throughout this review',canonical_before==canonical_after)
check('all exact reference hashes and sizes match',not mismatches,mismatches)
scriptcopy=O/'review_actual.static.py';scriptcopy.write_bytes(Path(__file__).read_bytes())
summary=dict(schema='researchos.independent-actual-review-checks.v1',verdict='FAILED_EXECUTION_CLOSED',checks=checks,all_static_checks_passed=all(c['passed'] for c in checks),checked_unique_file_count=len(checked),checked_files=list(checked.values()),root_evidence_copies=rootcopies,public_child_evidence_copies=childcopies,parent_counts=counts,parent_actions=actions,child_summaries=childsummaries,Goal_observed_component=goal,workspace_epoch_observed_component=epoch,canonical_before=canonical_before,canonical_after=canonical_after,Main_pinned_input_refs=mainrefs,Main_unchanged_basis='Root actual before/after assertions plus live matching original Main input pins; separate review interval snapshots. Pre-run canonical raw hashes not emitted by Root actual script.',formal_acceptance=False,Main_adopted=False,native_child_exit_directly_observed=False,external_source_refs=external)
ref=save('checks.json',summary)
print(json.dumps(dict(output=str(O),checks_ref=ref,all_static_checks_passed=summary['all_static_checks_passed'],failed_checks=[x for x in checks if not x['passed']],checked_unique_files=len(checked),parent_counts=counts,child_count=len(childsummaries),leaf_count=leafcount,root_evidence_file_count=len(rootcopies),child_evidence_file_count=len(childcopies)),ensure_ascii=False))
