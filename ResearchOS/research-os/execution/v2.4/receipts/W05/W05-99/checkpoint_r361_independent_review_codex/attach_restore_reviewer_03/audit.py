import pathlib,json,hashlib,datetime,types,sys,subprocess,os,re
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=pathlib.Path(__file__).resolve().parent
N=B/'sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r361-provenance-qualified-source-ready-revision'
F=N.parent/'checkpoint-r361-provenance-qualified-source-ready'
P=N.parent/'checkpoint-r360-native-temp-failed-closed-attach-timestamp-open'
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
def refs(x):
 if isinstance(x,dict):
  if all(k in x for k in ['path','sha256','bytes']):yield {k:x[k] for k in ['path','sha256','bytes']}
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
cp=R/'execution/v2.4/checkpoint.json';ow=R/'execution/v2.4/path_ownership.json';ss=R/'execution/v2.4/step_state.json';cm=R/'execution/v2.4/commands.json'
expected=[dict(path=str(cp),sha256='27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845',bytes=4147646),dict(path=str(ow),sha256='48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',bytes=192861),dict(path=str(ss),sha256='fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',bytes=257446),dict(path=str(cm),sha256='b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',bytes=68156)]
expected+=members(read(N/'manifest.json'))+[pin(N/'handoff.json'),pin(N/'manifest.json'),pin(N/'original-root-tool-io/original-tool-io.json'),pin(R/'AGENTS.md'),pin(R/'execution/project_identity.json')]
facts=read(N/'checkpoint.execution.facts.json');reviews=[]
for item in facts['reviews']:
 expected.extend([item['handoff_ref'],item['manifest_ref']])
 for ref in [item['handoff_ref'],item['manifest_ref']]:assert verify(ref)['matched'],ref
 mf=read(item['manifest_ref']['path']);expected+=members(mf)
 reviews.append(dict(name=item['name'],handoff=read(item['handoff_ref']['path']),members=len(members(mf))))
expected += [i['origin_ref'] for i in facts['diagnostics']]+facts['actual_refs']
q=read(facts['qualification_ref']['path'])
for item in q['qualified_original_records']:expected += list(refs(item))
expected += list(refs(q['ordinal835']))+[q['old833_counterproof_ref']]
txdir=pathlib.Path(read(N/'canonical_pair.actual.json')['transaction']['transaction_journal'])
expected += [pin(p) for p in txdir.iterdir() if p.is_file()]+[pin(p) for p in F.iterdir() if p.is_file()]
oldfacts=read(P/'checkpoint.execution.facts.json')
expected += members(read(P/'manifest.json'))+[pin(P/'handoff.json'),pin(P/'manifest.json'),pin(P/'original-root-tool-io/original-tool-io.json')]
expected += [v['origin_ref'] for v in oldfacts['diagnostics']]
t7ref=oldfacts['reviews'][3]['handoff_ref'];expected += [t7ref]
readyref=facts['work_in_progress']['mu_sdk_r361_native_temp_source']['Root_T8_detached_resource_ready_ref'];ready=read(readyref['path'])
for ref in ready['invocation_refs']:
 expected += [ref];expected += list(refs(read(ref['path'])))
main=[R/'internal/domain'/name for name in ['client_protocol.go','client_session_fence.go','backup_recovery.go','client_protocol_control_windows_test.go']]
expected += [pin(p) for p in main]
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';graw=gp.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
tp=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
expected += [pin(gp),pin(sys.executable),dict(path=str(tp),sha256='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9',bytes=tp.stat().st_size)]
unique={}
for ref in expected:
 normalized=dict(path=str(pathlib.Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes']);key=normalized['path'].casefold()
 if key in unique:assert unique[key]==normalized,(unique[key],normalized)
 unique[key]=normalized
checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
v=[verify(ref) for ref in unique.values()]
save('input-pins.json',dict(refs=v,all_matched=all(x['matched'] for x in v)));assert all(x['matched'] for x in v)
mod=types.ModuleType('cp361_readguard');mod.__file__=str(gp);sys.modules[mod.__name__]=mod;exec(compile(graw,str(gp),'exec'),mod.__dict__)
guard=mod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(list(unique.values()))
def failure_lexemes(raw):
 s=raw.decode('utf-8');match=re.search(r'"failure_counters"\s*:\s*\[',s);assert match
 i=match.end();out=[];decoder=json.JSONDecoder()
 while True:
  while s[i].isspace() or s[i]==',':i+=1
  if s[i]==']':return out
  _,end=decoder.raw_decode(s,i);out.append(s[i:end]);i=end
def result_objects(x):
 if isinstance(x,dict):
  if 'output' in x and 'exit_code' in x:yield x
  for v in x.values():yield from result_objects(v)
 elif isinstance(x,list):
  for v in x:yield from result_objects(v)
try:
 def raw(p):return guard.get_buffer(str(p))
 def held(p):return json.loads(raw(p))
 before=held(txdir/'0.before.json');current=held(cp);owner=held(ow);resume=held(N/'RESUME.r361.original.json');identity=held(R/'execution/project_identity.json')
 check('CP360 before exact pinned bytes',pin(txdir/'0.before.json')['sha256']=='685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56' and len(raw(txdir/'0.before.json'))==4126105)
 check('CP361 canonical revision and preceding revision',current['revision']==361 and current['expected_previous_revision']==360)
 check('OW168 exact unchanged',owner['revision']==168 and raw(ow)==raw(txdir/'1.before.json')==raw(txdir/'1.after.proposed.json'))
 check('SS and commands39 exact pins',held(cm)['revision']==39 and verify(expected[2])['matched'] and verify(expected[3])['matched'])
 check('CP proposed equals current exact',raw(cp)==raw(txdir/'0.after.proposed.json'))
 changed=[k for k in current if before.get(k)!=current[k]]
 check('six top-level keys changed only',set(changed)=={'revision','expected_previous_revision','updated_at','note','failure_counters','work_in_progress'},changed)
 oldw=before['work_in_progress'];neww=current['work_in_progress'];added=[k for k in neww if k not in oldw];modified=[k for k in oldw if oldw[k]!=neww.get(k)]
 check('prior WIP unchanged exact additions',not modified and set(added)==set(facts['work_in_progress'])|{'r361_registered_failure_count','r361_highest_observed_diagnostic_ordinal','mu_sdk_r361_facts_ref'},dict(added=added,modified=modified))
 check('new WIP equals exact facts',all(neww[k]==value for k,value in facts['work_in_progress'].items()) and neww['mu_sdk_r361_facts_ref']==pin(N/'checkpoint.execution.facts.json'))
 oldf=before['failure_counters'];allf=current['failure_counters'];appended=allf[len(oldf):]
 check('836 old count plus nine new equals845',len(oldf)==836 and len(allf)==845 and len(appended)==9)
 modified_old=[i for i,x in enumerate(oldf) if x!=allf[i]]
 modified_ordinals=[oldf[i].get('original_payload',{}).get('observed_ordinal') for i in modified_old]
 check('only old833 and835 payloads qualified',modified_ordinals==[833,835],dict(indices=modified_old,ordinals=modified_ordinals))
 oldlex=failure_lexemes(raw(txdir/'0.before.json'));newlex=failure_lexemes(raw(cp))
 check('834 unqualified old records byte exact',len(oldlex)==836 and len(newlex)==845 and sum(oldlex[i]==newlex[i] for i in range(836))==834 and all(oldlex[i]==newlex[i] for i in range(836) if i not in modified_old))
 check('all836 old outer fields preserved',all({k:v for k,v in oldf[i].items() if k!='original_payload'}=={k:v for k,v in allf[i].items() if k!='original_payload'} for i in range(836)))
 originals={x['ordinal']:x['original_canonical_record'] for x in q['qualified_original_records']}
 check('qualification embeds original two canonical records',all(oldf[i]==originals[oldf[i]['original_payload']['observed_ordinal']] for i in modified_old))
 effective={allf[i]['original_payload']['observed_ordinal']:allf[i]['original_payload'] for i in modified_old}
 p833=effective[833];old833=originals[833]['original_payload'];origin833=held(originals[833]['evidence_ref']['path']);io833=origin833['tool_io'];counterproof=held(q['old833_counterproof_ref']['path'])
 allowed833={'actual_python_exit','inferred_exits_are_not_directly_observed','diagnostic','source_reported_previous_actual_python_exit','inferred_python_exit','previous_diagnostic_reported_by_CP360','evidence_accuracy_qualification_ref'}
 diff833={k for k in set(p833)|set(old833) if p833.get(k)!=old833.get(k)}
 check('833 payload changes restricted to qualification',diff833<=allowed833 and p833['previous_diagnostic_reported_by_CP360']==old833['diagnostic'])
 check('833 effective PythonNULL sourceReported1 inferred1',p833['actual_python_exit'] is None and p833['source_reported_previous_actual_python_exit']==p833['inferred_python_exit']==1 and p833['actual_outer_exit']==1 and p833['actual_native_exit'] is None and p833['inferred_exits_are_not_directly_observed'] and p833['evidence_accuracy_qualification_ref']==facts['qualification_ref'])
 check('833 independently observed marker absent in exact original input result',io833['result']['chunk_id']=='ae5082' and io833['result']['exit_code']==1 and 'ROOT_PYTHON_EXIT' not in io833['input']['cmd'] and 'ROOT_PYTHON_EXIT' not in io833['result']['output'] and counterproof['exact_original_tool_io']==io833 and origin833['actual_Python_exit']==1)
 old835=originals[835]['original_payload'];p835=effective[835];o835=held(q['ordinal835']['original_origin_ref']['path']);harness=held(q['ordinal835']['harness_native_ref']['path']);rehearsal=held(q['ordinal835']['rehearsal_native_ref']['path'])
 hr=harness['result'];rr=rehearsal['Result'];hdecimal=str(hr['creation_time_100ns']);rdecimal=str(rr['creation_time_100ns'])
 allowed835={'effective_native_rehearsal_creation_time_100ns_decimal','effective_native_harness_creation_time_100ns_decimal','original_origin_FILETIME_fields_source_reported_inexact','evidence_accuracy_qualification_ref'}
 diff835={k for k in set(p835)|set(old835) if p835.get(k)!=old835.get(k)}
 check('835 payload only added qualification keys',diff835==allowed835 and all(p835[k]==v for k,v in old835.items()))
 check('835 precise decimal identities from Python integers',type(hr['creation_time_100ns']) is int and type(rr['creation_time_100ns']) is int and hdecimal==p835['effective_native_harness_creation_time_100ns_decimal']==q['ordinal835']['actual_harness_FILETIME_decimal']=='134359787460741284' and rdecimal==p835['effective_native_rehearsal_creation_time_100ns_decimal']==q['ordinal835']['actual_rehearsal_FILETIME_decimal']=='134359787476336016')
 check('835 inexact immutable source fields explicitly qualified',str(o835['native_harness_creation_time_100ns'])==q['ordinal835']['source_reported_harness_FILETIME_decimal']=='134359787460741280' and str(o835['native_rehearsal_creation_time_100ns'])==q['ordinal835']['source_reported_rehearsal_FILETIME_decimal']=='134359787476336020' and p835['original_origin_FILETIME_fields_source_reported_inexact'] and p835['evidence_accuracy_qualification_ref']==facts['qualification_ref'])
 check('835 both exact native failures and closed jobs preserved',hr['actual_exit']==rr['actual_exit']==p835['actual_native_exit']==1 and all(x['job_cleanup']['primary_exit_confirmed'] and x['job_cleanup']['job_idle_confirmed'] and x['job_cleanup']['handles_closed'] and not x['job_cleanup']['errors'] for x in [hr,rr]))
 diagchecks=[]
 for row,item in zip(appended,facts['diagnostics']):
  key=hashlib.sha256((item['origin_ref']['sha256']+'#'+str(item['ordinal'])).encode()).hexdigest()
  origin=held(item['origin_ref']['path']);results=list(result_objects(origin))
  if item['ordinal']==846:results+=list(result_objects(held(pathlib.Path(item['origin_ref']['path']).parent/origin['original_tool_io'])))
  failed=[x for x in results if x['exit_code']==1]
  if item['ordinal'] in [839,843,844]:
   actualouter=None;actualpy=None;actualnative=None
   sourcevalid=(item['ordinal']==839 and origin['failed_before_dispatch']) or (item['ordinal']==843 and origin['detection_outer_exit']==0 and origin['canonical_write_performed'] is False) or (item['ordinal']==844 and not origin['process_started'] and not origin['tool_execution_started'])
  else:
   actualouter=1 if failed else None;markers=[int(v) for x in failed for v in re.findall(r'ROOT_PYTHON_EXIT=(\d+)',x['output'])]
   actualpy=markers[-1] if markers else None;actualnative=None;sourcevalid=bool(failed)
  ok=row['origin_key']==key and sum(x.get('origin_key')==key for x in allf)==1 and row['counted_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False
  ok=ok and row['evidence_ref']==item['origin_ref'] and row['original_payload']['immutable_origin_ref']==item['origin_ref'] and row['original_payload']['observed_ordinal']==item['ordinal']
  ok=ok and (actualouter,actualpy,actualnative)==(item['actual_outer_exit'],item['actual_python_exit'],item['actual_native_exit']) and all(row['original_payload'][k]==item[k] for k in ['actual_outer_exit','actual_python_exit','actual_native_exit']) and sourcevalid
  diagchecks.append(dict(ordinal=item['ordinal'],matched=ok,independent_actual_outer_exit=actualouter,independent_marked_Python_exit=actualpy,independent_native_exit=actualnative,failed_result_chunks=[x.get('chunk_id') for x in failed]))
 check('nine new originals839..847 once and actual exits independently consistent',[x['ordinal'] for x in diagchecks]==list(range(839,848)) and all(x['matched'] for x in diagchecks),diagchecks)
 check('registered845 highest847 next848 without reset',neww['r361_registered_failure_count']==resume['registered_failures']==845 and neww['r361_highest_observed_diagnostic_ordinal']==resume['highest_observed_diagnostic_ordinal']==847 and resume['next_failure_ordinal']==848 and resume['counter_reset'] is False)
 check('project identity and HEAD metadata',current['project_id']==identity['project_id']==resume['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and current['head']==resume['head']=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
 check('six historical zero current formal',len(current['parent_tasks_accepted'])==6 and current['current_effective_formal_status']['formal_cases_accepted']==0 and current['current_effective_formal_status']['accepted_case_ids']==[])
 preserved=neww['mu_sdk_r361_preserved']
 check('22parent42formal original onceexpired financialOPEN providerNULL',preserved['required_parents']==22 and preserved['required_formal']==42 and preserved['original_trial_business_open'] and preserved['original_trial_once_consumed'] and preserved['original_trial_clock_expired'] and not preserved['original_trial_DB_touched'] and preserved['original_trial_provider_requests'] is None and preserved['global_provider_requests'] is None and preserved['original_trial_financial_closed'] is False and preserved['overall_completion'] is False and preserved['counter_reset'] is False)
 check('four reviews carry Source-only or rejection scopes',len(reviews)==4 and all(x['formal_acceptance'] is False for x in facts['reviews']) and all(x['handoff']['formal_acceptance'] is False for x in reviews) and reviews[0]['handoff']['decision']=='REQUEST_CHANGES_CHECKPOINT_EXIT_PROVENANCE' and reviews[1]['handoff']['decision']=='SOURCE_ONLY_APPROVE_WITH_FRESH_POSITIVE_BLOCKED' and reviews[2]['handoff']['status']=='SOURCE_ACCEPTED_WITH_EXECUTION_GATES' and reviews[3]['handoff']['decision']=='SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES')
 check('new Source adoption and actual execution not claimed',not neww['mu_sdk_r361_attach_source']['current_candidate_adopted'] and not neww['mu_sdk_r361_attach_source']['Root_native_actual_approved'] and not neww['mu_sdk_r361_legacy_source']['Root_unit_actual_done'] and not neww['mu_sdk_r361_legacy_source']['current_candidate_adopted'] and not neww['mu_sdk_r361_native_temp_source']['Go_actual_done'] and not neww['mu_sdk_r361_native_temp_source']['Root_case_started'] and not neww['mu_sdk_r361_native_temp_source']['native_positive_accepted'] and not neww['mu_sdk_r361_native_temp_source']['native9_accepted'])
 t7=held(t7ref['path']);check('T7 old three failed closed jobs preserved',len(t7['jobs'])==3 and all(x['closed'] and x['actual_exit']==1 for x in t7['jobs']) and not t7['native_positive_accepted'] and not t7['Owner_accepted'] and not t7['original_business_accepted'])
 check('ordinary and restored sharedTEXT gates remain',neww['mu_sdk_r361_legacy_source']['ordinary_upgrade'].startswith('BLOCKED_') and neww['mu_sdk_r361_attach_source']['fresh_positive'].startswith('BLOCKED') and neww['mu_sdk_r361_attach_source']['shared_TEXT_dependencies_remain'])
 rootio=held(N/'original-root-tool-io/original-tool-io.json');events={x['store_key']:x['value'] for x in rootio['events']}
 pairs=[('root_cp361_writer_actual_result','1118ee',1),('root_cp361_revision_prepare_result','a599f8',0),('root_cp361_revision_writer_result','40a83d',0),('root_t8_isolation_completion','f5468d',0)]
 check('Root failed writer and distinct successful receipts actual marked exits',all(events[k]['chunk_id']==chunk and events[k]['exit_code']==code and 'ROOT_PYTHON_EXIT='+str(code) in events[k]['output'] for k,chunk,code in pairs))
 fail847=held(F/'failure-origin.847.json');txsource=raw(tp).decode('utf-8')
 check('847 failure in transform before journal write preserved',fail847['original_result']==events['root_cp361_writer_actual_result'] and "KeyError: 'evidence_ref'" in fail847['original_result']['output'] and txsource.index('result=transform(')<txsource.index('journal.mkdir()')<txsource.index('checked(write(') and not list(F.glob('activate.transaction.*')))
 cleanup_paths=[N/'source_guard.cleanup.actual.json',F/'source_guard.cleanup.actual.json',pathlib.Path(readyref['path']).parent/'source-guard.cleanup.actual.json',pathlib.Path(readyref['path']).parent/'runtime-source-guard.cleanup.actual.json']
 check('Root sourceguard groups fully closed',all((lambda c:c['closed'] and c['retained_handles_count']==0 and not c['errors'])(held(p)) for p in cleanup_paths))
 t8jobs=[]
 for ref in ready['invocation_refs']:
  inv=held(ref['path']);result=inv['result'];c=result['job_cleanup'];t8jobs.append(dict(name=pathlib.Path(ref['path']).name,argv=inv['argv'],actual_exit=result['actual_exit'],pid=result['owned_child_pid'],creation_time_100ns_decimal=str(result['creation_time_100ns']),closed=c['primary_exit_confirmed'] and c['job_idle_confirmed'] and c['handles_closed'] and not c['errors']))
 check('T8 five Git jobs closed0 and no Source overlay',len(t8jobs)==5 and all(x['actual_exit']==0 and x['closed'] and pathlib.Path(x['argv'][0]).name=='git.exe' for x in t8jobs) and not ready['source_overlay'] and not ready['formal_acceptance'],t8jobs)
 check('six source-manifest members; RootIO separately pinned',len(members(held(N/'manifest.json')))==6 and str(N/'original-root-tool-io/original-tool-io.json').casefold() not in [str(pathlib.Path(x['path'])).casefold() for x in members(held(N/'manifest.json'))] and pin(N/'original-root-tool-io/original-tool-io.json')['sha256']=='5ef02e2bd71282a519edfc24e57ddcdf323b025a6774027527b1cbb3b6686568')
 env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0';git=[]
 for args in [['rev-parse','HEAD'],['status','--porcelain=v1','--untracked-files=no'],['diff','--cached','--name-only']]:
  z=subprocess.run(['git','-C',str(R),*args],capture_output=True,text=True,encoding='utf-8',env=env)
  git.append(dict(argv=['git','-C',str(R),*args],returncode=z.returncode,stdout=z.stdout,stderr=z.stderr))
 save('git.actual.json',git);dirty=git[1]['stdout'].splitlines()
 check('actual read-only Git HEAD status index exact',all(x['returncode']==0 for x in git) and git[0]['stdout'].strip()==current['head'] and dirty==current['dirty_paths']==ready['tracked_dirty_paths'] and len(dirty)==13 and sum(x[:2]==' D' for x in dirty)==11 and sum(x[:2]==' M' for x in dirty)==2 and git[2]['stdout']=='',dirty)
 copy_index=[]
 for i,ref in enumerate(unique.values()):
  path=pathlib.Path(ref['path']);dest=O/'public-inputs'/str(i).zfill(4)/path.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw(path))
  copy_index.append(dict(original_ref=ref,copy_ref=pin(dest)))
 save('public-copy-index.json',copy_index)
 save('review-checks.json',dict(checks=checks,all_passed=all(c['passed'] for c in checks),changed_top_keys=changed,sourceguard_refs=len(unique),reviews=reviews,diagnostics=diagchecks,qualified_old_ordinals=modified_ordinals,t8_jobs=t8jobs,root_original_tool_io_ref=pin(N/'original-root-tool-io/original-tool-io.json'),canonical_refs=[pin(p) for p in [cp,ow,ss,cm]],reviewer_Go_SQL_native_model_executed=False,native_state_observation='PINNED_PERSISTED_CLOSURE_EVIDENCE_ONLY_NOT_LIVE_PROCESS_REPROBE'))
finally:
 closed=guard.close();save('sourceguard.close.json',closed);assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
after=[verify(ref) for ref in unique.values()]
save('closing-pins.json',dict(refs=after,all_unchanged=all(x['matched'] for x in after)))
print(json.dumps(dict(all_checks_passed=all(x['passed'] for x in checks),failed_checks=[x for x in checks if not x['passed']],changed_top_keys=changed,guard_entries=len(closed['entries']),guard_closed=closed['closed'],all_closing_pins_matched=all(x['matched'] for x in after)),ensure_ascii=False))

