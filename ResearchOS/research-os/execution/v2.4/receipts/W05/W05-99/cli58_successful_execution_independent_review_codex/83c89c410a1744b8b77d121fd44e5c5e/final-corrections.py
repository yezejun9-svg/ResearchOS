import json,hashlib,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent;U='0e298790cd484ec9ba319a379e7e34ed'
N=P/('integration_codex/cli58-fresh-held2-r334-v2-'+U);E=P/'cli58_fresh_compiler_executor_codex'/U;L=P/'cli58_fresh_compiler_launcher_codex'/U
T=R/'execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_codex/8f8e7259f3b8459f8de4ad05ca885c78'
C=[];REF={}
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF[str(p)]=r;return r
def pin(r):
 p=path(r['path']);a=ref(p);ck('actual pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return p
def doc(p):ref(p);return json.loads(path(p).read_bytes())
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
try:
 s=doc(N/'scope_registration.json');g=doc(path(s['new_authorization_root'])/'authorization.execute.json');e=doc(E/'result.json');ld=doc(L/'completed.json')
 m=doc(T/'root-launch.closed.manifest.json');t=doc(T/'root-launch.outer-completion.json')
 ck('exact Root manifest pin',ref(T/'root-launch.closed.manifest.json')['sha256']=='fcc7ce41a76ca517ff607453e3bd9244b0881b186b74a45bafa6d2375aba036e')
 ck('exact Root completion pin',ref(T/'root-launch.outer-completion.json')['sha256']=='8361296d8ce72579d5ed07ec0c1829df104b76934ef03b043d9d15a48d60ee5f')
 ck('Root members actual169',isinstance(m['members'],list) and len(m['members'])==169)
 for r in m['members']:pin(r)
 for k,v in t.items():
  if k.endswith('_ref') and isinstance(v,dict) and set(['path','sha256','bytes'])<=v.keys():pin(v)
 ck('source scope equality',path(t['source_scope_ref']['path'])==N/'scope_registration.json' and t['source_scope_ref']['sha256']==ref(N/'scope_registration.json')['sha256'])
 ck('grant equality',path(t['grant_ref']['path'])==path(s['new_authorization_root'])/'authorization.execute.json')
 ck('actual source and UUID',t['source_commit']==s['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7' and t['run_uuid']==U)
 ck('E payload all exact',t['actual_case_roster_original_payload']==e['case_roster'] and t['actual_case_results_original_payload']==e['cases'])
 ck('complete bounded2',len(e['cases'])==2 and t['actual_NOT_RUN_original_payload']==[] and t['native_calls']==14 and t['SDK_MODEL_external_paid']==0)
 ck('no first cause or propagation counted',t['first_cause_original_payload'] is None and t['first_origin_ref'] is None and t['last_child_original_result'] is None and t['underlying_local_failure_count']==0 and t['nested_exit_propagations_are_not_new_origins'] is True)
 ck('actual outer caller launcher inner zero',all(t[k]==0 for k in ['actual_outer_tool_exit','actual_python_caller_exit','actual_launcher_native_exit','actual_inner_python_native_exit']))
 ck('caller clean',t['caller_error'] is None and t['caller_secondary']==[])
 for k in ['separately_captured_outer_native_raw','caller_OS_lifecycle_qualification','fresh_compile_qualification','complete_current43_source_validation','complete_current58_source_validation','case_qualification','source_acceptance','automatic_retry','counter_reset','completion_live_canonical_observed']:ck('Root bounded claim '+k,t[k] is False)
 ck('Root pending independent review',t['independent_qualification']=='PENDING' and t['formal_increment']==0 and t['canonical_refs_at_completion'] is None and t['canonical_changed'] is None)
 ck('historical counter snapshot', [t['registered_origin_count'],t['known_late_pending_outside_fixed_cut'],t['observed_origin_count_at_closure']]==[532,9,541])
 obs=doc(t['tool_observation_ref']['path']);actions=obs['poll_actions'];ck('7 recorded polls',len(actions)==7)
 ck('same initial input',obs['initial_input']==t['actual_initial_input_original_payload'] and obs['initial']['chunk_id']=='ad4547' and obs['initial']['session_id']==78573)
 for i,a in enumerate(actions):
  ck('poll same owned session '+str(i),a['input']['session_id']==78573)
  if i<6:ck('nonterminal same session '+str(i),a['result'].get('session_id')==78573)
 term=actions[-1]['result'];ck('actual terminal exact',term==obs['final'] and term['chunk_id']=='5f86c6' and term['exit_code']==0 and 'session_id' not in term)
 ck('terminal action equals original',t['actual_terminal_action_original_payload']==actions[-1] and doc(t['terminal_action_input_ref']['path'])==actions[-1]['input'] and doc(t['terminal_tool_result_ref']['path'])==term)
 lines=term['output'].splitlines();reports=[json.loads(x) for x in lines if x.startswith('{')];ck('explicit Python bridge exact',lines.count('ACTUAL_PYTHON_EXIT=0')==1 and len(reports)==1)
 if len(reports)==1:ck('terminal report exact pins',reports[0]['actual_launcher_native_exit']==0 and reports[0]['caller_error'] is None and reports[0]['secondary']==[] and reports[0]['scope_sha256']==t['source_scope_ref']['sha256'] and reports[0]['grant_sha256']==t['grant_ref']['sha256'])
 cmd=obs['initial_input']['cmd'];ck('original command explicit bridge',"ACTUAL_PYTHON_EXIT=" in cmd and '$LASTEXITCODE' in cmd and '-I -S -X utf8' in cmd)
 ci=doc(t['caller_invocation_ref']['path']);ck('caller nullable outer honest',ci['actual_outer_tool_exit'] is None and ci['actual_launcher_native_exit']==0 and ci['caller_error'] is None and ci['secondary']==[] and ci['caller_OS_lifecycle_qualification'] is False)
 for k in ['stdout_ref','stderr_ref']:pin(ci[k]);ck('caller raw captured empty '+k,ci[k]['bytes']==0)
 li=doc(L/'invocation.result.json');j=li['result'];jc=j['job_cleanup'];ck('launcher original exit0 and nullable tool',li['actual_native_exit']==0 and li['actual_outer_tool_exit'] is None and j['actual_exit']==0 and j['error'] is None and j['timed_out'] is False and j['resumed'] is True)
 ck('launcher identity full precision',type(j['owned_child_pid']) is int and type(j['creation_time_100ns']) is int and j['creation_time_100ns']>2**53)
 for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']:ck('launcher cleanup '+k,jc[k] is True)
 ck('launcher no terminate no errors idle',jc['termination_requested'] is False and jc['errors']==[] and jc['active_processes_last_observed']==0)
 ck('launcher stored OS equal pointtime', (L/'python-os.before.json').read_bytes()==(L/'python-os.after.json').read_bytes())
 canonical=[]
 for v in g['canonical_copies']:
  raw=pin(v['ref']).read_bytes();p=path(v['canonical_path']);ck('live canonical equals grant '+str(p),p.read_bytes()==raw);canonical.append(ref(p))
 cp=doc(R/'execution/v2.4/checkpoint.json');ow=doc(R/'execution/v2.4/path_ownership.json');ck('live tuple',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[334,162,532])
 h=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/h[5:]).read_text().strip() if h.startswith('ref: ') else h;ck('direct Main current58 head',head==s['source_commit'])
 for n in ['audit.json','supplement.json','deep-links.json']:d=doc(O/n);ck('previous actual independent checks all passed '+n,d['failed_checks']==[])
 save('final-corrections.json',{'schema':'researchos.independent-root-closure-supplement.v1','checks':C,'failed_checks':[v for v in C if not v['passed']],'input_refs':list(REF.values()),'Root_manifest_member_count':len(m['members']),'Root_tool_observations_original_raw_claim':False,'live_canonical_refs':canonical,'current_canonical_tuple':[334,162,532],'source_commit':head,'launcher_owned_result':j,'root_snapshot_observed_count':541,'corrections_to_previous_current_cohort_audits':[],'new_failure_origins':[],'actual_candidate_calls':0,'source_acceptance':False,'formal_increment':0})
 print(json.dumps({'checks':len(C),'failed_checks':[v for v in C if not v['passed']],'ref':ref(O/'final-corrections.json')},ensure_ascii=False))
except BaseException as exc:
 save('final-corrections.failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':C,'input_refs':list(REF.values()),'target_calls':0});raise
