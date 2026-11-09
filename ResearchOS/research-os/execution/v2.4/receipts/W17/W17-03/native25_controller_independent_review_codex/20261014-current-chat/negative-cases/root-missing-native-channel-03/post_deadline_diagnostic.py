"""Read surviving public records after fixture loss; never claim fresh SQL."""
import ast,datetime as dt,hashlib,json
from pathlib import Path
E=Path(__file__).parent;helper=E.parent/'review_negative_v2.py';tree=ast.parse(helper.read_bytes());scope={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),str(helper),'exec'),scope)
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/missing-native-channel-03');C=P/'controller';H=P/'harness'
read=scope['read'];ref=scope['ref'];hc=read(P/'harness.public.config.json');scope.update(P=P,C=C,H=H,hc=hc,case='missing-native-channel',PURPOSE='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1')
closed=read(C/'controller.closed.json');assert ref(C/'controller.closed.json')['sha256']=='sha256:6193e5491e59a6e7589e6d3685b1bda463a8e79291b2bf19553659ad9e234ba8'
iv=read(scope['check'](closed['invocation_ref']));scope['verify_job'](iv['result'],False);scope['verify_guard'](closed['source_guard_cleanup']);assert iv['result']['actual_exit']==1 and closed['job_and_guards_closed'] and not closed['harness_test_exit_zero'] and not closed['fixture_release_approval_exists']
assert len(closed['source_guard_cleanup']['entries'])==4376
native,request,out,err=scope['broker']('03-native','ControlProgram',['--private-pause-schema24-to25'],False)
line=err.decode().strip();dt.datetime.strptime(line[:19],'%Y/%m/%d %H:%M:%S');assert line[20:]=='AUTHORITY_PRIVATE_INHERITANCE_REQUIRED'
signatures={phase:scope['signature'](phase,True) for phase in ['release','grant']}
f=read(H/'fixture.public.json');assert not Path(f['root']).exists() and not Path(f['database']).exists()
assert 'Root review window ended context deadline exceeded' in Path(iv['stdout_ref']['path']).read_text(encoding='utf8')
baseline=E/'release-01-root-invoked-independent-checker/report.json';assert ref(baseline)['sha256']=='sha256:132f16dfa33c48b169de22c02caa814057f899c1dfedb63ad083889f126ae8c6'
report={'schema':'researchos.independent-native25-post-deadline-review/1','state':'NOT_ACCEPTED_NATIVE_REJECTION_RECORDED_BUT_FRESH_SQL_MISSING_AND_OUTER_FAILED','case':'missing-native-channel','case_id':'root-missing-native-channel-03','actual_recorded_native_pid':native['Result']['owned_child_pid'],'actual_recorded_native_exit':native['Result']['actual_exit'],'actual_recorded_rejection':'AUTHORITY_PRIVATE_INHERITANCE_REQUIRED','native_invocation_ref':ref(H/'03-native/invocation.json'),'public_signatures_independently_verified':signatures,'outer_test_exit':1,'outer_child_pid':iv['result']['owned_child_pid'],'outer_job_closed':True,'guards_closed':4376,'controller_closed_ref':ref(C/'controller.closed.json'),'test_invocation_ref':closed['invocation_ref'],'fixture_root_and_database_absent':True,'independent_fresh_terminal_sql_completed':False,'root_invoked_release_baseline_ref':ref(baseline),'root_invoked_baseline_is_not_independent_agent_execution':True,'independent_failed_terminal_attempt_ref':ref(E/'terminal-01-independent-agent/report.json'),'reviewer_failed_attempts':1,'temporary_public_inputs_retention_manifest_present':(P/'public-retained-inputs/retention.json').exists(),'inner_native_job_id_independently_observed':False,'formal_increment':0,'formal_accepted':'0/42','parents_open':22,'native_negative_case_accepted':False,'native_branch_complete':False,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
with (E/'POST-DEADLINE-report.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=True,indent=2);f.write('\n')
print(json.dumps({'report_ref':ref(E/'POST-DEADLINE-report.json')}))
