import pathlib,json,hashlib,datetime,types,sys,subprocess,os
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=pathlib.Path(__file__).resolve().parent
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r360-native-temp-failed-closed-attach-timestamp-open'
def pin(p):
 p=pathlib.Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def members(m):
 a=m['members'];return list(a.values()) if isinstance(a,dict) else a
def verify(ref):
 actual=pin(ref['path']);return dict(expected=ref,actual=actual,matched=actual['sha256']==ref['sha256'].removeprefix('sha256:') and actual['bytes']==ref['bytes'])
cp=R/'execution/v2.4/checkpoint.json';ow=R/'execution/v2.4/path_ownership.json';ss=R/'execution/v2.4/step_state.json';cm=R/'execution/v2.4/commands.json'
expected=[dict(path=str(cp),sha256='685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56',bytes=4126105),dict(path=str(ow),sha256='48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',bytes=192861),dict(path=str(ss),sha256='fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',bytes=257446),dict(path=str(cm),sha256='b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',bytes=68156)]
expected+=members(read(N/'manifest.json'))+[pin(N/'handoff.json'),pin(N/'manifest.json'),pin(N/'original-root-tool-io/original-tool-io.json'),pin(R/'AGENTS.md'),pin(R/'execution/project_identity.json')]
facts=read(N/'checkpoint.execution.facts.json');reviews=[]
for item in facts['reviews']:
 expected.extend([item['handoff_ref'],item['manifest_ref']])
 for ref in [item['handoff_ref'],item['manifest_ref']]:
  assert verify(ref)['matched'],ref
 mf=read(item['manifest_ref']['path']);expected+=members(mf)
 reviews.append(dict(name=item['name'],handoff=read(item['handoff_ref']['path']),members=len(members(mf))))
expected += [i['origin_ref'] for i in facts['diagnostics']]+facts['actual_refs']
txdir=pathlib.Path(read(N/'canonical_pair.actual.json')['transaction']['transaction_journal'])
expected += [pin(q) for q in txdir.iterdir() if q.is_file()]
main=[R/'internal/domain'/name for name in ['client_protocol.go','client_session_fence.go','backup_recovery.go','client_protocol_control_windows_test.go']]
expected += [pin(q) for q in main]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';graw=gp.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
expected += [pin(gp),pin(sys.executable)]
unique={}
for ref in expected:
 normalized=dict(path=str(pathlib.Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
 key=normalized['path'].casefold()
 if key in unique:assert unique[key]==normalized
 unique[key]=normalized
checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
v=[verify(ref) for ref in unique.values()]
save('input-pins.corrected.json',dict(refs=v,all_matched=all(x['matched'] for x in v)))
assert all(x['matched'] for x in v)
mod=types.ModuleType('cp360_readguard');mod.__file__=str(gp);sys.modules[mod.__name__]=mod;exec(compile(graw,str(gp),'exec'),mod.__dict__)
guard=mod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
guard.acquire(list(unique.values()))
try:
 def held(p):return json.loads(guard.get_buffer(str(p)))
 before=held(txdir/'0.before.json');current=held(cp);owner=held(ow);resume=held(N/'RESUME.r360.original.json');identity=held(R/'execution/project_identity.json')
 check('CP359 before pin exact',pin(txdir/'0.before.json')['sha256']=='f52e1416c81fefedde08725c3a7c9250a8e478b22e38b1e6ec1f7e42be236ecc')
 check('CP360 canonical exact and revision',current['revision']==360 and current['expected_previous_revision']==359)
 check('OW168 byte unchanged',owner['revision']==168 and guard.get_buffer(str(ow))==guard.get_buffer(str(txdir/'1.before.json'))==guard.get_buffer(str(txdir/'1.after.proposed.json')))
 check('CP proposed equals current exact',guard.get_buffer(str(cp))==guard.get_buffer(str(txdir/'0.after.proposed.json')))
 changed=[k for k in current if before.get(k)!=current[k]]
 check('six top-level keys changed only',set(changed)=={'revision','expected_previous_revision','updated_at','note','failure_counters','work_in_progress'},changed)
 oldw=before['work_in_progress'];neww=current['work_in_progress'];added=[k for k in neww if k not in oldw];modified=[k for k in oldw if oldw[k]!=neww.get(k)]
 check('prior WIP preserved; only seven additions',not modified and set(added)==set(facts['work_in_progress'])|{'r360_registered_failure_count','r360_highest_observed_diagnostic_ordinal','mu_sdk_r360_facts_ref'},dict(added=added,modified=modified))
 oldf=before['failure_counters'];allf=current['failure_counters'];appended=allf[len(oldf):]
 check('829 prefix and 836 total',len(oldf)==829 and allf[:829]==oldf and len(allf)==836)
 check('seven original diagnostics 832 through 838 once',[x['original_payload']['observed_ordinal'] for x in appended]==list(range(832,839)))
 diagchecks=[]
 for row,item in zip(appended,facts['diagnostics']):
  key=hashlib.sha256((item['origin_ref']['sha256']+'#'+str(item['ordinal'])).encode()).hexdigest()
  ok=row['origin_key']==key and sum(x.get('origin_key')==key for x in allf)==1 and row['counted_once'] is True and row['counter_reset'] is False
  ok=ok and all(row['original_payload'][k]==item[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit'])
  diagchecks.append(dict(ordinal=item['ordinal'],matched=ok,actual_outer_exit=item['actual_outer_exit'],actual_python_exit=item['actual_python_exit'],actual_native_exit=item['actual_native_exit']))
 check('origins and actual NULL exit values preserved',all(x['matched'] for x in diagchecks),diagchecks)
 check('highest ordinal 838 next839 not reset',neww['r360_registered_failure_count']==836 and neww['r360_highest_observed_diagnostic_ordinal']==838 and resume['counter_reset'] is False)
 check('permanent project identity and HEAD metadata',current['project_id']==identity['project_id']==resume['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and current['head']==resume['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
 check('six historical zero current formal',len(current['parent_tasks_accepted'])==6 and current['current_effective_formal_status']['formal_cases_accepted']==0 and current['current_effective_formal_status']['accepted_case_ids']==[])
 check('22 parent 42 formal scope preserved',neww['mu_sdk_r360_preserved']['required_parents']==22 and neww['mu_sdk_r360_preserved']['required_formal']==42 and resume['formal_required']==42)
 p=neww['mu_sdk_r360_preserved']
 check('original trial onceexpired business and finance open providerNULL',p['original_trial_business_open'] and p['original_trial_once_consumed'] and p['original_trial_clock_expired'] and not p['original_trial_DB_touched'] and p['original_trial_provider_requests'] is None and p['global_provider_requests'] is None and p['original_trial_financial_closed'] is False and p['overall_completion'] is False and p['counter_reset'] is False)
 check('four reviews restricted to scope',len(reviews)==4 and all(item['formal_acceptance'] is False for item in facts['reviews']) and reviews[0]['handoff']['decision']=='CP359_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY' and reviews[1]['handoff']['verdict']=='REQUEST_CHANGES' and reviews[2]['handoff']['status']=='REQUEST_CHANGES_SOURCE_ONLY' and reviews[3]['handoff']['decision']=='FAILED_EXECUTION_WHOLE_SQL_INSPECTION_AND_CLEANUP_COMPONENTS_ACCEPTED')
 jobs=reviews[3]['handoff']['jobs']
 check('T7 three jobs failure and closed no authority',len(jobs)==3 and all(j['closed'] and j['actual_exit']==1 for j in jobs) and not reviews[3]['handoff']['native_positive_accepted'] and not reviews[3]['handoff']['Owner_accepted'] and not reviews[3]['handoff']['original_business_accepted'])
 check('CP T7 failure state exact',neww['mu_sdk_r360_native_T7_actual']==facts['work_in_progress']['mu_sdk_r360_native_T7_actual'] and neww['mu_sdk_r360_native_T7_actual']['OwnedJobs_closed']==3 and not neww['mu_sdk_r360_native_T7_actual']['native_positive_accepted'])
 rootio=held(N/'original-root-tool-io/original-tool-io.json');results=[e['value'] for e in rootio['events'] if e['store_key'].endswith('_result')]
 check('Root actual facts and writer outer0 markedPython0',len(results)==2 and [x['chunk_id'] for x in results]==['52c1e5','5d3f05'] and all(x['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in x['output'] for x in results))
 cleanup=held(N/'source_guard.cleanup.actual.json')
 check('Root sourceguard closed with no retained handles',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
 env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0';git=[]
 for args in [['rev-parse','HEAD'],['status','--porcelain=v1','--untracked-files=no'],['diff','--cached','--name-only']]:
  z=subprocess.run(['git','-C',str(R),*args],capture_output=True,text=True,encoding='utf-8',env=env)
  git.append(dict(argv=['git','-C',str(R),*args],returncode=z.returncode,stdout=z.stdout,stderr=z.stderr))
 save('git.actual.json',git)
 check('Git read commands succeeded',all(x['returncode']==0 for x in git))
 dirty=git[1]['stdout'].splitlines()
 check('actual HEAD exact',git[0]['stdout'].strip()==current['head'])
 check('13 tracked dirty11D2M preserved',dirty==current['dirty_paths'] and len(dirty)==13 and sum(x[:2]==' D' for x in dirty)==11 and sum(x[:2]==' M' for x in dirty)==2,dirty)
 check('index empty',git[2]['stdout']=='')
 for i,ref in enumerate(unique.values()):
  q=pathlib.Path(ref['path'])
  dest=O/'public-inputs'/str(i).zfill(4)/q.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(guard.get_buffer(str(q)))
 save('review-checks.json',dict(checks=checks,all_passed=all(c['passed'] for c in checks),changed_top_keys=changed,sourceguard_refs=len(unique),reviews=reviews,diagnostics=diagchecks,root_original_tool_io_ref=pin(N/'original-root-tool-io/original-tool-io.json'),reviewer_Go_SQL_native_model_executed=False,actual_native_state_observation='PINNED_PERSISTED_CLOSURE_EVIDENCE_ONLY_NOT_LIVE_PROCESS_REPROBE'))
finally:
 closed=guard.close();save('sourceguard.close.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
after=[verify(ref) for ref in unique.values()]
save('closing-pins.json',dict(refs=after,all_unchanged=all(x['matched'] for x in after)))
print(json.dumps(dict(all_checks_passed=all(x['passed'] for x in checks),failed_checks=[x for x in checks if not x['passed']],changed_top_keys=changed,guard_entries=len(closed['entries']),guard_closed=closed['closed'],all_closing_pins_matched=all(x['matched'] for x in after)),ensure_ascii=False))

