"""Close independent positive case review using public artifacts only."""
import ast,datetime as dt,hashlib,json,os,sqlite3,struct,sys
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-02';C=P/'controller';H=P/'harness';A=P/'public-retained-inputs'
tree=ast.parse((E/'check_release.py').read_text(encoding='utf8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'reviewed-public-utilities','exec'))
closed=read(C/'controller.closed.json');assert ref(C/'controller.closed.json')['sha256']=='sha256:6755d284a7ddc9ab2751944958be733168b66d33a46a1eb21c626a989bbefcec'
iv=read(check(closed['invocation_ref']));assert closed['invocation_ref']['sha256']=='sha256:5c1189d731ff5268db678d87f3241af2286ed788c8f5c75b82b3ccac1883e456'
assert closed['job_and_guards_closed'] and closed['harness_test_exit_zero'] and closed['fixture_release_approval_exists'] and not closed['worker_still_alive']
assert closed['error_type'] is None and closed['worker_error_type'] is None
assert closed['job_binding_id']==iv['job_binding_id']=='dbfaee8e699447c0addd66b8b3dd7567'
res=iv['result'];job=res['job_cleanup'];guard=closed['source_guard_cleanup']
assert res['actual_exit']==0 and res['error'] is None and not res['timed_out'] and res['owned_child_pid']==60652
assert all(job[k] for k in ['assigned_before_resume','unnamed_exclusive_job','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and job['active_processes_last_observed']==0 and not job['errors']
assert guard['closed'] and not guard['errors'] and len(guard['entries'])==4376 and all(v['verified'] and v['closed'] and v['final_path_match'] for v in guard['entries'])
assert Path(check(iv['stdout_ref'])).read_bytes()==b'PASS\n' and Path(check(iv['stderr_ref'])).read_bytes()==b''
assert iv['same_owned_job_for_all_harness_pauses']
g=read(H/'02-grant.payload.json');cfg=read(P/'controller.public.config.json');temp=Path(cfg['Environment']['TEMP'])
archive=read(A/'retention.json');assert archive['copied_files']==len(archive['mapping'])==5 and archive['public_refs_only'] and archive['private_key_or_database_read'] is False
expected={str(Path(p['path'])):p for p in g['pins'] if Path(p['path']).is_relative_to(temp)}
assert len(expected)==5
mapped={}
for entry in archive['mapping']:
 old,new=entry['original_ref'],entry['archived_ref'];check(new)
 assert old['sha256']==new['sha256'] and old['bytes']==new['bytes'] and Path(new['path']).is_relative_to(A)
 assert expected[str(Path(old['path']))]['sha256']==old['sha256'] and expected[str(Path(old['path']))]['bytes']==old['bytes']
 mapped[str(Path(old['path']))]=new
assert set(mapped)==set(expected)
native_stdout=read(H/'03-native/stdout.raw');retained_receipts=read(A/'native-receipts-retention.json');assert len(retained_receipts['files'])==2
for entry in retained_receipts['files']:
 old=entry['original_ref'];new=ref(Path(entry['archived_path']));assert old['sha256']==new['sha256'] and old['bytes']==new['bytes']
 assert Path(old['path']).parent==Path(native_stdout['receipt_directory'])
intent=read(A/'migration-intent.json');native_result=read(A/'migration-result.json')
assert intent['binding']==g['binding'] and intent['status']=='PREPARED_NOT_COMMITTED'
assert native_result==native_stdout
for label in ['03-native','04-replay']:
 inv=read(H/label/'invocation.json');private=inv['Result']['private_stdin']
 for key in ['anonymous_pipe','file_type_pipe_verified','complete_input_written','writer_closed_before_launch','input_buffer_cleared','capacity_verified','empty_before_write','write_deadline_checked_before_and_after']:assert private[key]
 assert inv['NativeAuthorityAcceptance'] is False
for phase in ['release','grant']:
 p=read(C/('publish-'+phase+'.receipt.json'));assert p['phase']==phase
save('public-root-artifact-pins.json',{'files':[ref(p) for p in sorted(P.rglob('*')) if p.is_file()],'scope':'Public case receipt directory and retained encrypted/public inputs only. No private/runtime temp resource read.'})
attempts=read(E/'reviewer-attempt-history.json');assert len([a for a in attempts['attempts'] if a['exit_code']!=0])==4
report={'state':'ACCEPTED_ISOLATED_NATIVE_POSITIVE_AND_NONCE_REPLAY_ONLY','case':'positive-replay','case_id':'root-positive-replay-02','source_head':'f80955594bdd0373ae1c961cd02ab6be96f2c196','config_ref':ref(P/'controller.public.config.json'),'controller_closed_ref':ref(C/'controller.closed.json'),'test_invocation_ref':closed['invocation_ref'],'outer_owned_child_pid':60652,'outer_test_exit':0,'outer_job_closed':True,'source_guards_closed':4376,'signer_native_and_replay_jobs_closed':True,'private_stdin_pipe_cleanup_verified':True,'independent_release_review_ref':ref(E/'release-review/RELEASE-report.json'),'public_signature_and_grant_review_ref':ref(E/'grant-review-v3/GRANT-report.json'),'fresh_retained_sql_terminal_review_ref':ref(E/'terminal-review-v3/TERMINAL-report.json'),'retention_ref':ref(A/'retention.json'),'retained_native_receipts_ref':ref(A/'native-receipts-retention.json'),'public_root_artifacts_ref':ref(E/'public-root-artifact-pins.json'),'retained_temp_public_raw_files':5,'retained_native_receipt_files':2,'original_fixture_db_not_copied':True,'inner_native_job_id_independently_observed':False,'negative_native_cases_executed':0,'negative_native_cases_required':8,'native_branch_complete':False,'formal_increment':0,'formal_accepted':'0/42','open_parents':22,'case01_failure_preserved':True,'reviewer_checker_failed_attempts':4,'checker_attempt_history_ref':ref(E/'reviewer-attempt-history.json'),'reviewer_private_key_reads':0,'reviewer_product_database_reads':0,'reviewer_root_authority_actions':0,'limitations':['This accepts one isolated synthetic native positive plus actual nonce replay only. Eight native negatives remain pending.','Inner native child Job identity is not independently observed; actual Root broker owned jobs and outer held test Job closure are verified.','Fresh full SQLite reads happened while fixture retained; after Root release and test exit, temp fixture is allowed to be removed. The five public grant temp pins survive byte-identically via archive mapping.','No formal test case or parent task acceptance is derived from this result.'],'at':dt.datetime.now(dt.timezone.utc).isoformat()}
save('FINAL-report.json',report)
save('manifest.json',{'schema':'researchos.independent-public-evidence-manifest/1','files':[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='manifest.json']})
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json')}))
