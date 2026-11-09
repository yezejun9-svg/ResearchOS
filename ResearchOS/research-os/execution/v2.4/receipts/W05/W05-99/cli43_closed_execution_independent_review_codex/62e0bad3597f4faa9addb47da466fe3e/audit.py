import pathlib,json,hashlib,datetime,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(sys.argv[1]);N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324';checks=[];seen={}
def path(x):
 p=pathlib.Path(x);return p if p.is_absolute() else R/p
def raw(p):
 p=path(p);b=p.read_bytes();seen[p]={'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def ref(p):raw(p);return seen[path(p)]
def obj(p):return json.loads(raw(p))
def check(v,label):
 checks.append({'check':label,'passed':bool(v)})
 if not v:raise ValueError(label)
def verify(v):
 a=ref(v['path']);check(a['sha256']==v['sha256'] and a['bytes']==v['bytes'],'bytes:'+v['path']);return a
def save(n,v):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 return ref(p)
try:
 check(ref(N/'registration-audit.json')['sha256']=='94cc9fdcbae13374e96033015d184f80fbcd460edb338d6167e42fff01a15bfc','new audit pin')
 check(ref(N/'manifest.json')['sha256']=='0b10086d74b207e051db7bfcf186f114857a19ca7abeeed8e1909fa2f2e4698b','new manifest pin')
 a=obj(N/'registration-audit.json');mf=obj(N/'manifest.json');p=obj(N/'prepared_refs.json');members={}
 check(mf['count']==len(mf['entries']),'manifest cardinality')
 for e in mf['entries']:
  verify(e);pp=path(e['path']);check(pp.parent==N and pp not in members,'unique current namespace member');members[pp]=e
 handoffs=[x for x in members if x.name.startswith('handoff-') and x.suffix=='.json'];check(len(handoffs)==1,'actual inventory unique handoff');h=obj(handoffs[0])
 for key in ['completed_ref','manifest_ref','grant_ref','pre_registration_review_ref','registration_review_ref','invocation_ref','intent_ref','verified_ref','source43_vector_ref','Main38_completed_ref','Main38_manifest_ref']:verify(a[key])
 check(a['before']==[323,151,425] and a['after']==[324,152,430] and a['actual_registration_exit']==0,'actual transition')
 check(a['completed_ref']==h['completed_ref']==p['pins']['cli_completed'] and a['manifest_ref']==h['manifest_ref']==p['pins']['cli_manifest'],'exact original ABS dictionaries')
 pre=obj(a['pre_registration_review_ref']['path']);check(pre['schema']=='researchos.cli43-source-import-pre-registration-review.v1' and pre['decision']=='EXACT8_SOURCE_IMPORT_EVIDENCE_CLOSED_PENDING_HEAD_REGISTRATION_AND_FRESH43_VALIDATION' and pre['post_registration_audit_ref'] is None,'prior immutable preclosure')
 rr=obj(a['registration_review_ref']['path']);check(rr['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and rr['actual_registration_executed'] is False,'nonauthor preregistration')
 inv=obj(a['invocation_ref']['path']);check(inv['actual_exit']==0 and inv['wrapper_error'] is None and inv['automatic_retry'] is False and inv['counter_reset'] is False,'actual register native0')
 check(inv['review_ref']==a['registration_review_ref'] and inv['runner_sha256']==rr['register_sha256'] and inv['wrapper_sha256']==rr['wrapper_sha256'],'review invocation code binding')
 check(ref(N/'stdout.raw')['sha256']==inv['stdout_sha256'] and ref(N/'stderr.raw')['sha256']==inv['stderr_sha256'] and raw(N/'stderr.raw')==b'','actual streams')
 check(obj(N/'stdout.raw')['current']==[324,152,430],'raw registration success tuple')
 before=[];after=[]
 for i,(old,new,live) in enumerate(zip(p['original_refs'],p['desired_refs'],h['canonical_refs'])):
  verify(old);verify(new);verify(live);check(raw(new['path'])==raw(live['path']),'current canonical exact desired '+str(i));before.append(obj(old['path']));after.append(obj(new['path']))
 check([after[0]['revision'],after[1]['revision'],len(after[0]['failure_counters'])]==[324,152,430],'actual current tuple')
 check(after[0]['failure_counters'][:425]==before[0]['failure_counters'] and after[0]['failure_counters'][425:]==p['origins'],'prefix425 append exact5')
 check(a['registered_origin_refs']==[v['evidence_ref'] for v in p['origins']],'origin refs exact')
 for v in p['origins']:verify(v['evidence_ref']);check(obj(v['evidence_ref']['path'])==v['original_payload'],'original failure payload preserved')
 check([v['actual_native_exit'] for v in p['origins']]==[None,1,None,None,None],'no fabricated native failures')
 check(a['postcut_pending_origin_refs']==h['postcut_pending_origin_refs']==[p['pins']['aftercut_pending_origin']] and a['observed_lower_bound']==431,'postcut e1bbac still pending')
 verify(p['pins']['aftercut_pending_origin'])
 check(after[2:]==before[2:] and all(raw(p['desired_refs'][i]['path'])==raw(p['original_refs'][i]['path']) for i in [2,3]),'ST CM originalbytes')
 check(after[0]['current_effective_formal_status']==before[0]['current_effective_formal_status'],'formal unchanged')
 check(after[0]['head']==a['registered_head']==h['Main_head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856','forward head registered')
 check(after[1]['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']['current_source_writer'] is None,'source writer released')
 intent=obj(a['intent_ref']['path']);verified=obj(a['verified_ref']['path']);check(verified['intent_ref']==a['intent_ref'] and verified['registered_head']==a['registered_head'],'persistent intent verified link')
 for i,row in enumerate(intent['metadata']):
  check(row['original_ref']==p['original_refs'][i] and row['desired_ref']==p['desired_refs'][i] and row['write_required']==(i<2),'intent exact metadata '+str(i))
  if i<2:
   done=obj(N/('canonical-write.'+pathlib.Path(row['path']).stem+'.done.json'));check(done['sha256']==row['desired_ref']['sha256'],'done marker '+str(i))
 gitjobs=[]
 for pp in members:
  if pp.name.endswith('.invocation.json') and not pp.name.startswith('prepare-'):
   j=obj(pp);check(j['actual_native_exit']==0 and j['wrapper_error'] is None and j['automatic_retry'] is False and j['operation']=='READONLY_GIT','actual readonly guard child '+pp.name);verify(j['stdout_ref']);verify(j['stderr_ref']);gitjobs.append(ref(pp))
 check(len(gitjobs)==18,'run3 register12 seal3 recorded children')
 check(raw(N/'seal-current-head.stdout.raw').decode().strip()==a['registered_head'],'seal actual head')
 status=raw(N/'seal-current-status.stdout.raw');check(hashlib.sha256(status).hexdigest()==p['git_status_sha256'] and len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11,'seal status13 old11D')
 check(raw(N/'seal-current-index.stdout.raw')==b'','seal empty index')
 check(a['source_acceptance'] is False and a['fresh43_validation_authorized'] is False and a['Desktop_integration_authorized'] is False and a['formal_increment']==0,'no extra qualification or grant')
 # New registration addon only; do not recurse old 6839/source runtime vectors.
 for pp,v in list(seen.items()):check(hashlib.sha256(pp.read_bytes()).hexdigest()==v['sha256'],'after unchanged:'+str(pp))
 auditref=save('read-audit.json',{'checks':checks,'passed':len(checks),'failed':0,'input_refs':list(seen.values()),'new_git_or_product_invocations':0,'prior_evidence_reused':True,'root_registration_manifest_members':len(members),'actual_guard_git_invocation_refs':gitjobs})
 review={'schema':'researchos.cli43-closed-execution-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'EXACT43_MAIN_SOURCE_INTEGRATION_EVIDENCE_CLOSED','requested_changes':[],'completed_ref':a['completed_ref'],'manifest_ref':a['manifest_ref'],'post_registration_audit_ref':ref(N/'registration-audit.json'),'root_registration_manifest_ref':ref(N/'manifest.json'),'root_registration_handoff_ref':ref(handoffs[0]),'prior_source_import_review_ref':a['pre_registration_review_ref'],'registration_source_review_ref':a['registration_review_ref'],'read_audit_ref':auditref,'independent_auditor_ref':ref(O/'audit.py'),'actual_integration_executed_by_reviewer':False,'scope':'New actual r324 registration closure addon to preserved independent source-import review; source-only unique43, not current43 product qualification.','closed_facts':{'actual_main_head':a['registered_head'],'canonical_tuple':[324,152,430],'canonical_refs':h['canonical_refs'],'old425_prefix_unchanged':True,'five_origins_registered_once':True,'postcut_pending_origin_refs':a['postcut_pending_origin_refs'],'observed_lower_bound':431,'ST_CM_unchanged':True,'source_writer':None,'actual_register_invocation_ref':a['invocation_ref'],'intent_ref':a['intent_ref'],'verified_ref':a['verified_ref'],'actual_register_native_exit':0,'registration_guard_git_children':18,'registration_guard_git_native_exits_all_zero':True,'old11_deletions_and_empty_index_at_seal':True,'unique_source_paths':43},'evidence_reuse':{'prior_source_import':{'apply_count':1,'commit_count':1,'git_children':32,'owned_python_children':2,'all_actual_native_exits_zero':True,'basis':a['pre_registration_review_ref']},'source_tree_and_6839_vector_rehashed_in_this_addon':False,'fresh_git_queries_in_this_addon':0,'earlier_source_and_job_evidence_not_reexecuted':True,'completed_and_manifest_dictionary_spelling_preserved':True},'outer_observation_limits':{'original_cli_import_tool_initial':'9ce0c5/session85762','original_cli_import_tool_final':'13b080','original_cli_import_tool_outer_exit':0,'separate_original_outer_python_native_exit':None,'original_knownfields_transcription_ref':p['pins']['outer_known_fields_transcription'],'original_outer_completion_ref':p['pins']['outer_completion'],'r324_run_conversation':'f4c3d8/session69092 -> a5085d outer0','r324_seal_conversation':'b53ec6/session81305 -> eab581 outer0','r324_sealer_separate_native_capture':None,'conversation_observation_is_not_original_native_stream':True,'actual_registration_native0_evidence':a['invocation_ref']},'open_gates':{'fresh43_compilation_and_product_validation':'NOT_AUTHORIZED_NOT_RUN_BY_THIS_REVIEW','held2':'NOT_REPLAYED','Desktop_integration_grant':False,'OS_python_resources':'POINT_IN_TIME_NOT_LIFECYCLE','source_acceptance':False,'whole_W05_acceptance':False,'formal_increment':0,'new_failure_origins':[]},'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 rv=save('review.json',review); entries=[ref(x) for x in sorted(O.iterdir()) if x.is_file()];mr=save('manifest.json',{'count':len(entries),'entries':entries,'self_excluded':True,'future_handoff_append_not_covered':True});hr=save('handoff.json',{'review_ref':rv,'manifest_ref':mr,'decision':review['decision'],'new_failure_origins':[],'actual_new_product_or_integration_execution':False,'next':'Root may use this closed source-import evidence in a separately reviewed actual Desktop scope; no execution permission conferred.'});print(json.dumps({'checks':len(checks),'registration_members':len(members),'review':rv,'manifest':mr,'handoff':hr},ensure_ascii=True))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'checks':checks,'inputs':list(seen.values()),'actual_new_product_execution':0});raise