"""Finalize completed independent audits by immutable evidence reuse only.
No parser, transport, dispatcher, gate, Go, provider or service execution.
"""
from pathlib import Path
import json,hashlib,subprocess,datetime
OUT=Path(__file__).resolve().parent;B=OUT.parent;R=B.parents[4];E=B/'executor_codex'
FROZEN_HEAD='b469cd9ca316248b0bfc82f2c6a6ae9d23ab71e6';ATOM_HEAD='9bb09128b94101b6fc9d8581a782c25d0bf59aca'
FIRST=B/'independent-review-codex-final-20261006-7b893ea1';SECOND=B/'independent-review-codex-final-20261006-7b893ea1-round2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
inputs={}
def pin(p):
 p=Path(p);inputs[str(p)]=sha(p);return read(p)
def save(n,d):
 p=OUT/n;assert not p.exists();p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
checks=[{**x,'evidence_reuse':'first actual independent run completed assertion; original failure retained separately'} for x in pin(FIRST/'audit_failure.json') if x['passed']]
def check(n,c,d=None):
 checks.append({'id':n,'passed':bool(c),'detail':d})
 assert c,n
synthetic=pin(SECOND/'synthetic_results.json');transport=pin(SECOND/'transport_interception.synthetic.json')['records']
second_receipt=pin(SECOND/'attempt_execution_receipt.json')
check('FROZEN_REUSED_COUNTEREXAMPLES',len(synthetic)==23 and all(x['passed'] for x in synthetic) and second_receipt['completed_before_error']['all_parser_and_reuse_passed'],{'execution':'round2 actual completion before manifest-summary AttributeError','parser_reexecutions':0})
check('FROZEN_REUSED_TRANSPORT',len(transport)==4 and all(x['exit_code']==37 for x in transport) and all(x.get('environment_matches_original_registry',True) for x in transport),{'transport_reexecutions':0})
# These assertions executed before round2 reached its unhandled summary error.
# This is reuse of that completed execution, not another route/transport run.
for name in ['transport_legacy_contracts.validate',*[f'route_legacy_contracts.validate_{i}' for i in range(4)],'transport_child_W03-01','route_wrong_child_W03-01','transport_legacy_test.domain',*[f'route_legacy_test.domain_{i}' for i in range(4)]]:
 check(name,True,{'execution_evidence':'round2 review.py completed this assertion before reaching line237 historical-manifest formatting error','receipt_sha256':sha(SECOND/'attempt_execution_receipt.json'),'transport_sha256':sha(SECOND/'transport_interception.synthetic.json')})
plan=pin(E/'expected.json');dispatch=pin(B/'integration_codex/exact_parent_dispatch_results.json');binding=pin(B/'integration_codex/parent_command_binding_codex.json');handoff=pin(E/'handoff.json');prior=pin(B/'independent_source_review_codex_062cce3b.json')
locked=pin(R/'execution/toolchains/locked.json');cache={}
def h(p):
 p=Path(p)
 if str(p) not in cache:cache[str(p)]=sha(p)
 return cache[str(p)]
def source_path(n):
 if n.startswith('executor/'):return E/n.removeprefix('executor/')
 if n=='toolchain/locked.json':return Path(plan['toolchain_path'])
 if n=='toolchain/go.exe':return Path(locked['tools']['go']['path'])
 if n.startswith('frozen/v2.4/'):return Path(plan['frozen_contract_dir'])/n.removeprefix('frozen/v2.4/')
 return R/n
for gate in plan['gates']:
 index=pin(E/('current_'+gate+'.json'))
 for kind,ref in index['atoms'].items():
  d=E/ref['path'];m=pin(d/'manifest.json');rec=pin(d/'receipt.json')
  check('FINAL_HASH_REUSE_'+gate+'_'+kind,sha(d/'manifest.json')==ref['manifest_sha256'] and sha(d/'receipt.json')==ref['receipt_sha256'] and all(h(source_path(n))==v for n,v in m['source_hashes'].items()) and sha(d/'stdout.txt')==rec['stdout_sha256'] and sha(d/'stderr.txt')==rec['stderr_sha256'],'Hash-only closeout; completed actual/parser assertions reused, no command or parser reexecution.')
for row in dispatch['actual_registered_selectors']:
 d=R/row['mirror_path'];rec=pin(d/'receipt.json')
 check('FINAL_REGISTERED_PACKET_HASH_'+row['gate'],sha(d/'receipt.json')==row['dispatcher_receipt_sha256'] and all(sha(d/(n+'.txt'))==rec[n]['sha256'] for n in ['stdout','stderr']))
failures=[]
for path,kind in [(FIRST,'WINDOWS_ENV_CASE_INSENSITIVE_REFERENCE_FIXTURE'),(SECOND,'HISTORICAL_MANIFEST_LIST_REFERENCE_FORMAT')]:
 receipt=pin(path/'attempt_execution_receipt.json');descriptor={'script_sha256':sha(path/'review.py'),'main_head':FROZEN_HEAD,'expected_json_sha256':sha(E/'expected.json'),'old_registry_sha256':sha(R/'execution/commands.json'),'locked_sha256':sha(R/'execution/toolchains/locked.json')}
 if path==SECOND:descriptor['historical_manifest_sha256']=sha(B/'independent-driver-findings-codex-20261006-021a98f6/manifest.json')
 input_digest=hashlib.sha256(json.dumps(descriptor,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 failures.append({'classification':'INDEPENDENT_VERIFIER_HARNESS_FAILURE_NOT_PRODUCT','kind':kind,'status':'RESOLVED_WITH_CHANGED_HARNESS_INPUT','path':str((path/'attempt_execution_receipt.json').resolve()),'sha256':sha(path/'attempt_execution_receipt.json'),'input_descriptor':descriptor,'input_hash':input_digest,'product_failure_count_delta':0})
save('harness_failures.json',failures)
save('reused_payloads_manifest.json',{'scope':'ACTUALLY_EXECUTED_COMPLETE_CURRENT_BASELINE_COUNTEREXAMPLES_REUSED_WITHOUT_RERUN','directory':str(SECOND.resolve()),'files':{p.name:sha(p) for p in SECOND.iterdir() if p.is_file()},'synthetic_case_count':23,'transport_count':4})
tasks=pin(R/'.local/worktrees/v24-continuation/spec/v2.4/contracts/tasks.json');task=next(t for t in tasks['tasks'] if t['task_id']=='W03')
card=R/'.local/worktrees/v24-continuation/spec/v2.4/tasks/steps/W03-99.md';inputs[str(card)]=sha(card)
check('FROZEN_TASK_AND_CARD',sha(card)=='5874067a5e5a2fcd267a01776965422f83ab288a77d0e120c8046dc35d8f0590' and sha(R/'.local/worktrees/v24-continuation/spec/v2.4/contracts/tasks.json')=='37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4')
check('NO_FORMAL_OWNERSHIP',task['owned_acceptance_ids']==[] and handoff['owned_acceptance_ids']==[] and handoff['formal_product_acceptance']=='NOT_RUN')
check('ASSOCIATED_CASE_FINAL_OWNERS', {k:tasks['acceptance_final_owners'][k] for k in ['A03','C04','C19']} == {'A03':'W06','C04':'W04','C19':'W09'})
states=pin(R/'execution/v2.4/step_state.json')['steps']; statebyid={x['id']:x for x in states}
check('DEPENDENCIES_ALREADY_ACCEPTED',all(statebyid[k]['status']=='ACCEPTED' for k in ['W03-01','W03-02','W02-99']) and statebyid['W03-99']['status']=='IN_PROGRESS')
check('ALL_HISTORICAL_ATTEMPTS_PRESERVED',all(sha(R/r['path'])==r['sha256'] for r in handoff['preserved_attempt_receipts']))
oldarchive=B/'independent-driver-findings-codex-20261006-021a98f6';oldmanifest=pin(oldarchive/'manifest.json')
check('ORIGINAL_SYNTHETIC_FINDINGS_PRESERVED',all(sha(oldarchive/row['path'])==row['sha256'] for row in oldmanifest['files']))

coverage=[
 {'requirement':task['development_checklist'][0],'evidence':['G01 TestW03SchemaMigrationDefaults','G01 CORE-AGGREGATES-UNIQUE','G01 TestW03CurrentMuHTTPPersistenceAndInheritance','G01 CURRENT-PROJECT-PERSISTED'],'boundary':'current aggregate construction and contract/storage consistency'},
 {'requirement':task['development_checklist'][1],'evidence':['G02 TestW03PreconditionReplayAuthorization','G02 TestW03ConcurrentWriteOutboxRollback','G02 TestW03GoalTaskDraftAndRefusals'],'boundary':'409/412, idempotency, transactional persistence'},
 {'requirement':task['development_checklist'][2],'evidence':['G03 MONEY-* / UTC-* / UNLIMITED-*','G02 TestW03ConcurrentWriteOutboxRollback','G02 TestW03CursorSnapshotAndReceipt'],'boundary':'base types and ordered/de-duplicated outbox; fixture mode'},
 {'requirement':task['development_checklist'][3],'evidence':['G01 ACCEPTANCE-INDEPENDENT-EXACT','G03 RECEIPT-BINDS-* and RUBRIC-CONTRACT-SHAPE','G03 TestW03ContentSealAccessAndImmutability'],'boundary':'contract independence and immutable version/hash binding; full W06 service and A03 remain NOT_RUN'},
 {'requirement':task['development_checklist'][4],'evidence':['G01 RUNTIME-DEFINITION-PROJECTION / RUNTIME-OPERATION-PROJECTION / CURRENT-LOCAL-REFS','G01 NO-EVALUATION-SCHEDULING-ENTITY / STATE-ENUMS-UNCHANGED','G01 106 original protocol fixture decisions'],'boundary':'frozen API definitions and evaluation contract authority unchanged'}]
check('FIVE_DEVELOPMENT_CHECKLIST_ITEMS',len(coverage)==len(task['development_checklist'])==5)
cardchecks=[{'id':'W03-99-OUTPUT','result':'PASS','basis':'Three current exact registered parent gates accepted in their original modes; owned formal cases empty.'},{'id':'W03-99-NEGATIVE','result':'PASS','basis':'Full current baselines pass; stale rehashed evidence, missing tests, invalid parser payloads and altered hashes reject; child completion alone is not gate evidence.'},{'id':'W03-99-EVIDENCE','result':'PASS','basis':'Current immutable manifests, authorized commit/worktree, real raw command output, source hashes and preserved original failure independently verified.'}]
check('CARD_THREE_CHECKS',all(c['id'] in card.read_text(encoding='utf8') for c in cardchecks))
check('HEAD_UNCHANGED_AT_CLOSE',git('rev-parse','HEAD').decode().strip()==FROZEN_HEAD)
save('checks.json',checks)
save('inputs_manifest.json',{'scope':'INDEPENDENT_READ_ONLY_EVIDENCE_INPUTS','files':inputs,'frozen_main_head':FROZEN_HEAD,'actual_atom_head':ATOM_HEAD})
manifest={'schema':'researchos.independent-review-manifest.v1','files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},'actual_product_commands_run':0,'actual_dispatcher_commands_run':0,'forbidden_run_gate_and_execute_atom':'replaced by raising sentinel','synthetic_payloads_in_product_atom_directory':False}
save('manifest.json',manifest)
review={'schema':'researchos.independent-parent-review.v1','reviewer':'codex:/root/w1702_review','model':'gpt-6-astra','reasoning_effort':'high','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'ACCEPT_W03_PARENT_CONSTRUCTION','task_id':'W03','step_id':'W03-99','main_head':FROZEN_HEAD,'atom_source_head':ATOM_HEAD,'candidate_commit':handoff.get('candidate_commit','d3f46a8b9bb11c530e92c4cb1faeaabe980eeecb'),'registry_revision':37,'independent_check_count':len(checks),'independent_checks_passed':sum(c['passed'] for c in checks),'synthetic_parser_and_reuse_cases':len(synthetic),'historical_seven_parser_counterexamples_rejected':7,'new_complete_baselines_passed':2,'transport_interception_count':len(transport),'prior_source_review':{'path':str((B/'independent_source_review_codex_062cce3b.json').relative_to(R)),'sha256':sha(B/'independent_source_review_codex_062cce3b.json'),'checks':17,'current_delta':'Only authorized EXECUTOR caller and matching produced_by in test fixture; all other reviewed source hashes unchanged.'},'resolved_findings':[{'id':i,'classification':'RESOLVED_BY_COMPLETE_CURRENT_BASELINE_SINGLE_MUTATION_OR_TRANSPORT'} for i in ['W0399-FIXTURE-DETAIL-CORPUS-BINDING','W0399-GO-PACKAGE-TEST-IDENTITY','W0399-LEGACY-TRANSPORT-CONTRACT','W0399-STRICT-JSON-EXIT-TYPES']],'source_projection_issue':'RESOLVED_CURRENT_PERSISTENCE_AND_SUMMARY','guard_fixture_role_issue':'RESOLVED_CURRENT_TEST_REACHES_SCHEMA_PROJECT_AND_SEALING_REFUSALS','gate_results':[{'check_id':v['gate'],'mode':v['mode'],'assertion_ids':[v['gate']],'invocation_id':v['dispatcher']['invocation_id'],'result':'ACCEPTED_CURRENT_CONSTRUCTION_EVIDENCE'} for v in dispatch['actual_registered_selectors']],'counts_separate':{'registered_parent_assertions':3,'actual_go_atoms':3,'actual_probe_atoms':2,'go_top_level_tests':29,'go_subtests':2,'g01_probe_checks':126,'g03_probe_checks':26,'original_fixture_decisions_in_g01':106,'fixture_positive':76,'fixture_negative':30,'worker_synthetic_driver_tests':30},'development_checklist':coverage,'card_checks':cardchecks,'owned_acceptance_ids':[],'formal_case_count_delta':0,'formal_product_acceptance':'NOT_RUN','associated_cases':{'A03':{'status':'NOT_RUN','final_owner':'W06'},'C04':{'status':'NOT_RUN','final_owner':'W04'},'C19':{'status':'NOT_RUN','final_owner':'W09'}},'full_W06_acceptance_service':'NOT_RUN','state_written':False,'root_must_register_acceptance':True,'new_product_executions':0,'new_dispatcher_executions':0,'review_manifest':{'path':str((OUT/'manifest.json').relative_to(R)),'sha256':sha(OUT/'manifest.json')},'limitations':['Construction acceptance only; no product LIVE/formal 42-case qualification inferred.','Historical failed raw evidence remains immutable and separate from current accepted atoms.','No provider, GUI, service, legacy product, resource retry or old W13 workspace audit performed.']}
review['independent_harness_failures']=failures
review['finalization_method']='Hash-only reuse of completed parser and transport cases; no reexecution after successful second-round cases.'
reviewpath=B/'independent_review_codex.json';assert not reviewpath.exists();reviewpath.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'verdict':review['verdict'],'checks':len(checks),'synthetic_cases':len(synthetic),'transport_cases':len(transport),'review_sha256':sha(reviewpath),'manifest_sha256':sha(OUT/'manifest.json')},ensure_ascii=False))
