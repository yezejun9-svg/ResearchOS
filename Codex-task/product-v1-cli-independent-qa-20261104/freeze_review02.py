from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

base=Path(__file__).resolve().parent
root=base/'revision-02'
directory=base/'review02';directory.mkdir(exist_ok=False)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(base/'review01/review.json')=='e469b68c3765b4a702e1685c1f0f4a8db092839fe036d7dec3a4c42d7f050553'
assert sha(base/'review01/EVIDENCE.json')=='25e513ef220d80dbc5842cb7384cf9bcc27b98a8feb1355001777db82c14b008'
old=json.loads((base/'review01/EVIDENCE.json').read_text(encoding='utf-8'))
assert all(sha(base/row['path'])==row['sha256'] for row in old['files'])
stage=json.loads((root/'pin-stage.json').read_text(encoding='utf-8'))
readback=json.loads((root/'final-checks/result.json').read_text(encoding='utf-8'))
assert readback['all_match'] and readback['exact_scope'] and readback['commands'][0]['stdout_empty']
assert all(row['exit_code']==0 for row in readback['commands'])
assert json.loads((root/'checks-01/result.json').read_text(encoding='utf-8'))=={'exit_code':0,'input_pins_unchanged':True,'selector':'^(TestQCLI|TestS04|TestCLIPrompt(ParseExplicit|LegacyArgsUntouched|RejectInvalid|SurfaceQualifications|ExactInt64HostArguments)$)'}
assert json.loads((root/'vet-01/result.json').read_text(encoding='utf-8'))['exit_code']==0
rows=[]
for line in (root/'checks-01/stdout').read_text(encoding='utf-8-sig').splitlines():
 try: rows.append(json.loads(line))
 except ValueError: pass
terminal=[row for row in rows if row.get('Test') and row.get('Action') in ['pass','fail','skip']]
assert len(terminal)==132 and all(row['Action']=='pass' for row in terminal)
pins={row['path']:row['sha256'] for row in stage['exact3']}
wt=Path(stage['worktree'])
assert all(sha(wt/name)==digest==sha(root/'source-snapshot'/name) for name,digest in pins.items())
diagnostics=[
 {'unique_origin':'CLI-RUN_STARTED-NULLABLE-SNAPSHOT','classification':'PRODUCT_P2','finding_id':'CLI-QA-001','status':'RESOLVED_IN_FREEZE02','source_tool_origins':['05f9b2','3357f5','e043f4'],'detail':'Root schema-valid null snapshot counterexample failed freeze01; matching positive control passed. The same case and author wrong-task/status/run/omitted-field negatives pass freeze02. Parent/subtest failure events are one origin.'},
 {'unique_origin':'CLI-QA-READ-DISCOVERY','classification':'READONLY_DISCOVERY_DIAGNOSTIC','status':'RESOLVED','source_tool_origins':['3e6f0b','14fd23'],'detail':'No CLI subdirectory AGENTS matched; a symbol read initially printed the long embedded schema and was truncated. Narrow immutable source reads followed. No QA fixture or source assertion was misclassified.'},
]
report={
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','at':datetime.now(timezone.utc).isoformat(),'scope_id':'PRODUCT_V1_S04_CLI_HARNESS',
 'scope_sha256':stage['scope_sha256'],'base_head':stage['base_head'],'worktree':stage['worktree'],
 'author_source_manifest':{'path':str(root/'author-evidence/final-02/source-manifest.json'),'sha256':stage['author_manifest_sha256']},
 'author_freeze_sha256':'f610c711c16d5ce60db99e8d9470c11db1dc5b79f6d5d49c673ac596351b182b',
 'interface_sha256':stage['interface_sha256'],'source_sha256':pins,'exact3':True,
 'independent_tests':{'exit_code':0,'pass_events':132,'fail_events':0,'skip_events':0,'top':25,'sub':107,'independent_events':29,'author_S04_events_replayed':71,'existing_pure_Mu_events_replayed':32,'raw_stdout':'revision-02/checks-01/stdout','raw_stderr':'revision-02/checks-01/stderr','command':'revision-02/checks-01/command.json','tool_origin':'e043f4'},
 'independent_vet':{'exit_code':0,'raw_directory':'revision-02/vet-01','tool_origin':'47d987'},
 'independent_format':{'exit_code':0,'diff_empty':True,'raw_directory':'revision-02/final-checks','tool_origin':'45ac9b'},
 'independent_git':{'diff_check_exit':0,'status_exit':0,'exact3':True,'raw_directory':'revision-02/final-checks','tool_origin':'45ac9b'},
 'coverage':{
  'contract':'Exact Root rev2 pin and22 closed definitions; raw duplicate/escaped duplicate/trailing/UTF8/unknown/alias/numeric precision negatives.',
  'native_credentials':'Fake native refusal cannot fall back to environment bearer; author current/renewal/foreign binding fixtures replayed; known synthetic credentials absent from output.',
  'host_and_http':'Invalid Host URL forms and failed identity verification reject before authority transfer; actual owned loopback proxy/redirect traps and poisoned global transport receive no authority.',
  'mutation':'Captured actual POST byte SHA, stable request id and original prompt/workspace lookup matching; no automatic POST retry. Cancel recovery only reads original task and never refences a new Run.',
  'precision':'Nullable queued Run pair and exact active revision/epoch strings through int64 max; stale/conflicting fences reject.',
  'compatibility':'Existing pure Mu32 events pass; main entry changes remain scoped to Harness help/dispatch.'},
 'resolved_findings':['CLI-QA-001'],'pending_blockers':[],'diagnostic_events':diagnostics,
 'previous_review':{'path':str(base/'review01/review.json'),'sha256':sha(base/'review01/review.json'),'decision':'REQUIRES_CHANGES','all49_evidence_pins_unchanged':True},
 'author_diagnostics':['author-evidence/diagnostics.json','revision-02/author-evidence/diagnostics-02.json'],
 'root_diagnostic_carryforward':{'origin':'72ad13','count_again':False},
 'observations':[{'classification':'INFORMATIONAL','detail':'Valid INTERNAL_ERROR500 is reported REJECTED without automatic POST retry. The probe is not proof that no server commit occurred.'}],
 'limits':['Source/fixture approval only; no actual CLI, native pipe, user credential/config, old DB or model run.', 'Host filesystem ownership/ACL/pipe enforcement and actual owned Job/stream cancellation were not runtime-qualified.', 'No Windows product package or real user-journey acceptance is conferred.'],
 'go_test_execution_mode':'In-process command functions with injected fake Native and only owned loopback HTTP; no real CLI application entry invocation.',
 'source_writes':0,'real_cli_invocations':0,'native_or_model_runs':0,'user_auth_config_or_old_db_reads':0,'old_probe_replays':0,
 'formal_increment':0,'product_acceptance_increment':0,'native_execution_authorized':False,'business_acceptance':False,'pending_processes':[],
}
(directory/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selected={base/row['path'] for row in old['files']}
selected.update({base/'review01/EVIDENCE.json',base/'stage_revision02.py',base/'freeze_review02.py',base/'review02-readme.md',directory/'review.json'})
for name in ['revision-02/source-snapshot','revision-02/author-evidence','revision-02/checks-01','revision-02/vet-01','revision-02/final-checks']:
 selected.update(path for path in (base/name).rglob('*') if path.is_file())
for name in ['revision-02/pin-stage.json','revision-02/overlay.json','revision-02/scope.json','revision-02/harness.v1.interface.rev2.json','revision-02/run_independent.py','revision-02/independent_cli_test.go','revision-02/final_readback.py']:
 selected.add(base/name)
archive={'root':str(base),'files':sorted(path.relative_to(base).as_posix() for path in selected)+['ARCHIVE_FILES.json','review02/EVIDENCE.json'],
         'excludes':['cache','tmp','home','appdata','localappdata','programdata','executables','full Git baseline'],
         'semantics':'Selected immutable review01 failures and final snapshot3/raw only; original C folders retained.'}
(base/'ARCHIVE_FILES.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selected.add(base/'ARCHIVE_FILES.json')
files=[{'path':path.relative_to(base).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(selected)]
(directory/'EVIDENCE.json').write_text(json.dumps({'files':files,'file_count':len(files),'review_sha256':sha(directory/'review.json'),'archive_file_list_sha256':sha(base/'ARCHIVE_FILES.json')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':report['decision'],'review_sha256':sha(directory/'review.json'),'evidence_sha256':sha(directory/'EVIDENCE.json'),'archive_sha256':sha(base/'ARCHIVE_FILES.json'),'files':len(files),'exact3':pins}))
