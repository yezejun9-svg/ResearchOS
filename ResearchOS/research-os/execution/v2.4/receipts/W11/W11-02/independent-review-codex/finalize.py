import datetime,hashlib,json,pathlib,shutil,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
I=R/'execution/invocations/027d43b4-3d93-41fc-bd25-3fb05843eb90'
dispatch=read(I/'receipt.json');stdout=read(I/'stdout.txt');P=pathlib.Path(stdout['receipt']);report=read(P);D=P.parent
before=read(D/'before.json');commands=read(D/'commands.json');index=read(D/'evidence-index.json')
checks=[]
def check(id,ok,detail):
 checks.append({'id':id,'status':'PASS' if ok else 'FAIL','detail':detail});assert ok,id
check('MAIN-SOURCE',all(sha(R/p)==h.removeprefix('sha256:') for p,h in before['source_hashes'].items()),len(before['source_hashes']))
check('MAIN-EVIDENCE',all(sha(D/x['path'])==x['sha256'].removeprefix('sha256:') for x in index['files']),len(index['files']))
rows=[json.loads(x[len('W11_ASSERTION '):]) for x in (D/'negative-fixture.stdout.log').read_text().splitlines() if x.startswith('W11_ASSERTION ')]
ids=sorted(x['assertion_id'] for x in rows)
check('MAIN-40-UNIQUE',len(ids)==len(set(ids))==40 and rows==report['assertions'] and ids==stdout['assertion_ids']==dispatch['assertion_ids'] and all(x['status']=='PASS' and x['expected']==x['actual'] for x in rows),len(ids))
check('MAIN-EXPECTED-BLOCK',report['status']=='BLOCKED' and report['fixture_status']=='PASS' and dispatch['status']=='COMMAND_FAILED' and dispatch['exit_code']==1 and dispatch['child_exit_code']==2,{'dispatcher':dispatch['status'],'dispatcher_exit':1,'child_exit':2})
check('COMMAND-EXITS',len(commands)==3 and all(c['exit_code']==0 for c in commands),commands)
check('MIRROR',all((I/f).read_bytes()==(B/'registered-dispatch'/I.name/f).read_bytes() for f in ('receipt.json','stdout.txt','stderr.txt')),I.name)
check('DISPATCH-RAW-HASH',all(sha(R/dispatch[k]['path'])==dispatch[k]['sha256'] for k in ('stdout','stderr')),True)
reg=read(R/'execution/v2.4/commands.json');bind=read(B/'integration_codex/binding_after.json');old=read(B/'integration_codex/binding_before.json')
check('REGISTRY-PRESERVED',all(reg['commands'].get(k)==v for k,v in old['old_command_decoded_values'].items()) and sha(R/'execution/commands.json')==old['legacy_sha256'],len(old['old_command_decoded_values']))
check('REGISTRY-EXACT',reg['revision']==33 and reg['commands']['test.jev.live']==bind['entry'] and dispatch['registered_command_revision']==sha(R/'execution/v2.4/commands.json') and dispatch['selectors']=={'task_id':'W11','check_id':'W11-02','case_id':''},33)
check('LEGACY-PIN',sha(R/'tests/jev/admit_frozen_live.py')=='efafca4f69077d52ef04360ebd30e4744bd3b5ef740861559391801eef495b3e',True)
probe=report['resource_probe'];resources=read(R/'execution/v2.4/qualification/W11-02/resources_round2.json')
check('PROVENANCE',probe['service_query']=='NOT_REPEATED_NO_NEW_STATE' and probe['current_summary'] is None and probe['new_provider_calls']==0 and probe['formal_label_body_accessed'] is False and probe['credential_status']=='NOT_PROBED_NO_NEW_PROVIDER_AUTHORIZATION' and resources['per_full_key_minimum']['applies_when']=='IF_AUTOMATION_REQUESTED',probe['service_state'])
archive=probe['archive'];check('ARCHIVE-PIN',sha(R/archive['path'])==archive['sha256'].removeprefix('sha256:'),archive['sha256'])
check('SOURCE-FREEZE',before['source_revision']==dispatch['code_revision']=='ebb19e80a9d025a0cff80899482aac300a938bfc' and read(O/'source-before.json')==read(O/'source-after.json'),before['source_revision'])
tmp=(O/'tmp').resolve();assert tmp.parent==O.resolve()
if tmp.exists():shutil.rmtree(tmp)
save(O/'main-evidence-checks.json',{'status':'PASS_IN_SCOPE','checks':checks,'formal_acceptance':False})
save(O/'handler-mutation-command.json',{'argv':[sys.executable,'-B','-X','utf8',str(O/'handler_mutations.py')],'cwd':str(R),'exit_code':0,'real_subprocesses_in_mutations':0,'synthetic_mutations':10})
spec=R/'.local/worktrees/v24-continuation/spec/v2.4'
review={
 'schema':'researchos-v24-independent-construction-review/1','step_id':'W11-02','reviewer_id':'codex:/root/w1702_review','producer_id':'codex:/root/w1102_impl',
 'model':'gpt-6-astra','reasoning_effort':'high','model_provenance':'Root confirmed actual spawn gpt-6-astra/high; same reviewer reused for this distinct W11 security/architecture review.',
 'decision':'BLOCKED_NO_LIVE_QUALIFICATION','technical_review':'PASS_IN_SCOPE','construction_acceptance_recommendation':'DO_NOT_ACCEPT_CARD',
 'tested_source_commit':before['source_revision'],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'New pure descriptive per-key automation eligibility audit, exact W11-02 handler and legacy-selector compatibility only. No domain grant changes, new LIVE run, service refresh, provider inference, formal label/body access, old W13 workspace audit or GUI.',
 'summary':'The bounded implementation and evidence checks pass. A real nonfinite-cost serialization defect was reproduced on original b0d63bc2 source and repaired on the frozen main source. Full W11-02 remains BLOCKED because the requested reuse_selection real evaluation, independent labels and new-run authorization are not established, with recorded existing-service control access denied. Fixtures do not complete the card.',
 'card_checks':[
  {'check_id':'W11-02-OUTPUT','status':'BLOCKED','reason':'No new reuse_selection provider run or independent labeled cases; new-purpose authorization/model/rubric/budget not frozen. Existing service was recorded STOPPED with start denied code5; no fresh service measurement was made. Credentials remain NOT_PROBED.'},
  {'check_id':'W11-02-NEGATIVE','status':'PASS_IN_SCOPE','mode':'FIXTURE','reason':'40 exact unique audit assertions, 13 independent boundaries including 64 confusion matrices, and explicit original/fixed nonfinite counterexample prove bounded numerical/source/key refusals and NONE authority. This does not constitute real provider execution of reuse_selection negative cases.'},
  {'check_id':'W11-02-EVIDENCE','status':'PASS_IN_SCOPE','reason':'Current source/tool/raw hashes, exact registry dispatch, nonzero blocked exit and immutable mirror verified. 12 forwarding fixtures and 10 handler mutations are synthetic tests, counted separately from product assertions.'}],
 'closed_findings':[{'id':'W1102-REVIEW-NONFINITE-JSON','original_commit':'b0d63bc2cf985b5ee54f742f89d13379f19ed246','original_exit_code':1,'repaired_exit_code':0,'status':'CLOSED_VERIFIED','reason':'NaN/+Inf/-Inf rejected but were retained in ActualCost and prevented JSON encoding. Fixed audit outputs null and retains invalid-metrics reason. Same independent counterexample reproduces all three old failures and passes current source.'}],
 'open_implementation_findings':[],
 'assertion_accounting':{'audit_fixture':40,'independent_boundary':13,'confusion_matrices_within_one_boundary':64,'legacy_forwarding_synthetic':12,'handler_mutations_synthetic':10,'main_readonly_checks':len(checks),'note':'Counts describe separate checks; no synthetic test is a formal labeled/provider sample.'},
 'interpretation':[
  'Initial real evaluation uses total >=60 development + >=30 independent holdout, with >=15 holdout per language. A completed failed real evaluation with safe ADVISORY downgrade may complete a case/card; auto eligibility is not a prerequisite to such completion.',
  'Per full task_type/language/provider/model/rubric key >=60/30 applies IF_AUTOMATION_REQUESTED. Historical evidence-validity per-language 30/15 is insufficient for auto promotion but is not by itself the reason this card is blocked.',
  'AuditQualification is descriptive. Self-reported independence/mode/coverage booleans cannot prove provenance. Even REVIEWABLE returns ADVISORY/NONE and has no domain acceptance capability.',
  'Requested and observed full keys compare exactly; bounded integer arithmetic checks totals, class/action consistency, critical zero, false-accept and disagreement thresholds without changing denominators. Unknown cost remains null.',
  'Existing aggregate archive is pinned public historical evidence, not current LIVE measurement. Rejection/action counts remain in aggregate_input and development metrics remain separate from holdout metrics.',
  'AUTO resolution now selects v2.4 test.jev.live. Old valid tuples/default and argv preserve legacy historical admission via unchanged pinned handler; mixed/new-invalid selectors refuse. Compatibility was tested only with subprocess stand-ins.',
  'Observed root dispatcher COMMAND_FAILED exit1 wraps intentional child BLOCKED exit2 and 40 actual assertion IDs; it is not a fabricated PASS or an unexplained product regression.'
 ],
 'commands':read(O/'commands.json')+[read(O/'handler-mutation-command.json')],
 'main_dispatch':{'path':str(I/'receipt.json'),'sha256':sha(I/'receipt.json'),'exit_code':1,'child_exit_code':2},
 'main_report':{'path':str(P),'sha256':sha(P),'source_count':len(before['source_hashes']),'evidence_count':len(index['files'])},
 'frozen_inputs':{p:sha(spec/p) for p in ['tasks/steps/W11-02.md','05_WBS.md','06_ACCEPTANCE_TESTS.md','11_EVALUATION_AND_INTEGRATION.md']},
 'independent_evidence_hashes':{p.relative_to(R).as_posix():sha(p) for p in O.rglob('*') if p.is_file()},
 'resource_status':resources['card_blocking_reasons'],'credential_status':'NOT_PROBED','formal_cases_accepted':[],'parent_accepted':False,'card_accepted':False,'new_provider_calls':0,'service_refresh_executed':False,'real_legacy_admission_executed':False,'formal_label_body_accessed':False,'automatic_authority':'NONE'
}
save(B/'independent_review_codex.json',review)
print(json.dumps({'technical_review':review['technical_review'],'decision':review['decision'],'review_sha256':sha(B/'independent_review_codex.json'),'main_checks':len(checks)}))
