from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
stage=json.loads((root/'pin-stage.json').read_text(encoding='utf-8'))
directory=root/'review01';directory.mkdir(exist_ok=False)
def counts(name):
 rows=[]
 for line in (root/name).read_text(encoding='utf-8-sig').splitlines():
  try: rows.append(json.loads(line))
  except ValueError: pass
 named=[row for row in rows if row.get('Test')]
 return {'pass':sum(row.get('Action')=='pass' for row in named),'fail':sum(row.get('Action')=='fail' for row in named),'skip':sum(row.get('Action')=='skip' for row in named),'failed_tests':[row['Test'] for row in named if row.get('Action')=='fail']}
full=counts('checks-02-v1-suite/stdout')
assert full['pass']==59 and full['fail']==2 and full['skip']==0
assert json.loads((root/'vet-01-v1/result.json').read_text(encoding='utf-8'))['exit_code']==0
replay=json.loads((root/'checks-01-counterexample/overlay.json').read_text(encoding='utf-8'))
virtual=str(Path(stage['worktree'])/'apps/cli/independent_productv1_qa_test.go')
replay['Replace'][virtual]=str(root/'checks-01-counterexample/independent_cli_test.go')
(root/'checks-01-counterexample/replay-overlay.derived.json').write_text(json.dumps({'Replace':replay['Replace']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
finding={'id':'CLI-QA-001','severity':'P2','classification':'PRODUCT_CONTRACT_INTEROPERABILITY','unique_origin':'CLI-RUN_STARTED-NULLABLE-SNAPSHOT','status':'REQUIRES_CHANGES_IN_FREEZE01','path':'apps/cli/productv1.go','function':'validateCLIHarnessEvents/RUN_STARTED','problem':'Current Root rev2 Event schema and RUN_STARTED semantic rule permit payload.task=null. CLI adds a required snapshot condition and rejects the otherwise valid event page.','proof':'Same envelope first passes the exact pinned EventsResponse schema. Matching snapshot positive control passes actual runCLIHarness; null snapshot returns exit1 REJECTED/HOST_REPLY_UNCONFIRMED with one GET.','raw':'checks-01-counterexample/stdout','raw_sha256':sha(root/'checks-01-counterexample/stdout'),'fixture':'checks-01-counterexample/independent_cli_test.go','fixture_sha256':sha(root/'checks-01-counterexample/independent_cli_test.go'),'fix_scope':'Allow absent RUN_STARTED snapshot while retaining all existing validation when a snapshot is present. No weaker identity/run/status or closed-field checks.'}
report={'decision':'REQUIRES_CHANGES','at':datetime.now(timezone.utc).isoformat(),'author_manifest_sha256':stage['author_manifest_sha256'],'base_head':stage['base_head'],'source_sha256':{row['path']:row['sha256'] for row in stage['exact3']},'source_pins_verified_at_initial_capture':True,'later_live_source_state':'Root-authorized author revision02 after this finding; review01 continues only immutable C snapshot3 overlay.','findings':[finding],'pending_blockers':['CLI-QA-001'],'independent_tests':{'exit_code':1,'pass_events':59,'fail_events':2,'skip_events':0,'failure_origins':1,'includes_existing_pure_Mu_events':32,'raw':'checks-02-v1-suite/stdout','tool_origin':'3357f5'},'independent_vet':{'exit_code':0,'raw':'vet-01-v1','tool_origin':'9105a3'},'author_tests':{'exit_code':0,'pass_events':96,'independent_acceptance_inferred':False},'observations':[{'classification':'INFORMATIONAL_NOT_A_NEW_BLOCKER','detail':'A valid INTERNAL_ERROR500 mutation response is surfaced REJECTED with one POST/no automatic retry. No claim of no server commit is made by this review; the probe only records current behavior.'}],'diagnostic_events':[{'unique_origin':'CLI-QA-001','classification':'PRODUCT_P2','tool_origins':['05f9b2','3357f5'],'not_two_issues':'Top/subtest fail events are one underlying origin.'},{'unique_origin':'CLI-QA-READ-DISCOVERY','classification':'READONLY_DISCOVERY_OUTPUT','tool_origins':['3e6f0b','14fd23'],'detail':'No CLI subdirectory AGENTS file matched; source symbol discovery initially printed the long embedded schema line and was truncated. Narrow source reads followed; no source changed.'}],'original_author_diagnostics':'author-evidence/diagnostics.json','root_origin_72ad13_count_again':False,'formal_increment':0,'product_acceptance_increment':0,'real_cli_native_model':0,'source_writes':0,'independent_runtime_or_business_acceptance':False,'pending_processes':[]}
(directory/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selected={root/'pin-stage.json',root/'scope.json',root/'author-source-manifest.json',root/'harness.v1.interface.rev2.json',root/'stage_frozen.py',root/'capture_author_evidence.py',root/'run_independent.py',root/'freeze_review01.py',directory/'review.json'}
for name in ['source-snapshot','author-evidence','checks-01-counterexample','checks-02-v1-suite','vet-01-v1']:
 selected.update(path for path in (root/name).rglob('*') if path.is_file())
files=[{'path':path.relative_to(root).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(selected)]
(directory/'EVIDENCE.json').write_text(json.dumps({'files':files,'file_count':len(files),'excludes':['cache','tmp','home','appdata','localappdata','programdata','executables'],'review_sha256':sha(directory/'review.json')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'review_sha256':sha(directory/'review.json'),'evidence_sha256':sha(directory/'EVIDENCE.json'),'files':len(files),'decision':report['decision']}))
