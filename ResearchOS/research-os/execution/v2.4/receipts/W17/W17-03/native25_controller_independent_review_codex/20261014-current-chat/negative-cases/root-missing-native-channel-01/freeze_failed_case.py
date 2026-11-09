import datetime as dt,hashlib,json
from pathlib import Path
E=Path(__file__).parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/missing-native-channel-01');C=P/'controller';H=P/'harness'
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':'sha256:'+hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=True,indent=2);f.write('\n')
closed=read(C/'controller.closed.json');assert ref(C/'controller.closed.json')['sha256']=='sha256:8f458779c6ec7a5c59a2eb4f1d92b6b3363f46c41d9152267717f07add0452b7'
inv=read(closed['invocation_ref']['path']);assert ref(closed['invocation_ref']['path'])==closed['invocation_ref']
res=inv['result'];job=res['job_cleanup'];guard=closed['source_guard_cleanup']
assert res['actual_exit']==1 and not res['timed_out'] and res['error'] is None and res['owned_child_pid']==51456
assert closed['job_and_guards_closed'] and not closed['harness_test_exit_zero'] and not closed['worker_still_alive']
assert job['handles_closed'] and job['job_idle_confirmed'] and job['primary_exit_confirmed'] and job['active_processes_last_observed']==0 and not job['errors'] and not job['termination_requested']
assert guard['closed'] and not guard['errors'] and len(guard['entries'])==4376 and all(x['closed'] and x['verified'] and x['final_path_match'] for x in guard['entries'])
stdout=Path(inv['stdout_ref']['path']).read_text(encoding='utf8');assert '(1200.02s)' in stdout and 'Root review window ended context deadline exceeded' in stdout and stdout.endswith('FAIL\n')
assert not (C/'sign-grant.consumed.json').exists() and not (C/'sign-grant.receipt.json').exists() and not (H/'02-grant.approval.json').exists() and not (H/'03-native/invocation.json').exists()
report={'schema':'researchos.independent-native25-negative-failed-case/1','state':'NOT_ACCEPTED_HARNESS_REVIEW_DEADLINE_BEFORE_NATIVE','case':'missing-native-channel','case_id':'root-missing-native-channel-01','outer_child_pid':51456,'actual_test_exit':1,'outer_job_closed':True,'source_guards_closed':4376,'controller_closed_ref':ref(C/'controller.closed.json'),'test_invocation_ref':closed['invocation_ref'],'test_stdout_ref':inv['stdout_ref'],'release_stage_report_ref':ref(E/'release-01/report.json'),'failed_grant_attempt_report_ref':ref(E/'grant-01/report.json'),'failed_grant_traceback_ref':ref(E/'grant-01/traceback.raw.txt'),'observed_failure':'Harness 1200-second context deadline while waiting grant approval and cleanup fixture hold. Temporary backup manifest was already absent when independent grant review read snapshot evidence refs.','grant_signature_present':False,'grant_publish_approval_present':False,'actual_negative_native_invocation_present':False,'expected_rejection_reached':False,'reviewer_failed_attempts':1,'root_reported_preapproval_failure_attempts':2,'root_reported_attempts_note':'Parent reported one base64-versus-hex public signature assertion and one missing approval lookup; not reclassified as signing attempts. Root owns its raw ledger.','inner_native_job_id_independently_observed':False,'formal_increment':0,'formal_accepted':'0/42','open_parents':22,'native_branch_complete':False,'root_authority_actions_by_reviewer':0,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
write(E/'FINAL-report.json',report)
write(E/'manifest.json',{'schema':'researchos.independent-public-evidence-manifest/1','files':[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json']})
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json')}))
