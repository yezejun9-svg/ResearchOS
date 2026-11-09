"""Incremental immutable preparation for Source04 GEN02 actual component review."""
from pathlib import Path
import ast,copy,datetime,json,re,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;OLD=D.parent/'actual-20261010-01'
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
REVIEW=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-04-full'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('support');s.__file__=str(HELPER);exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
refs=[s.pin(__file__),s.pin(HELPER),s.pin(D/'actual_review_intake.source.py'),
    *[s.pin(OLD/name) for name in ('HDF.json','MF.json','actual-input-contract.json')],
    *[s.pin(N/name) for name in ('HDF.json','MF.json','public22_to23_root.source.py','root-calling-contract.source.json','source-inputs.json')],
    *[s.pin(REVIEW/name) for name in ('HDF.json','MF.json','decision.json')]]
g=s.guard();checks=[];failure=None;output=None
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise ValueError(name)
try:
    g.acquire(refs)
    oldh=json.loads(g.get_buffer(str(OLD/'HDF.json')));oldmf=json.loads(g.get_buffer(str(OLD/'MF.json')))
    before=json.loads(g.get_buffer(str(OLD/'actual-input-contract.json')))
    sh=json.loads(g.get_buffer(str(N/'HDF.json')));contract=json.loads(g.get_buffer(sh['calling_contract_ref']['path']))
    review=json.loads(g.get_buffer(str(REVIEW/'HDF.json')));decision=json.loads(g.get_buffer(str(REVIEW/'decision.json')))
    source_refs=[s.pin(N/'HDF.json'),sh['manifest_ref'],sh['caller_ref'],sh['calling_contract_ref']]
    review_refs=[s.pin(REVIEW/'HDF.json'),review['manifest_ref'],review['source_decision_ref']]
    check('exact_Source04_and_accepted_review_pins',source_refs[0]['sha256']=='aab92e1de8bfa85bec7968ac649d4946723b528daf54a8832eab8658d4555469'
        and source_refs[1]['sha256']=='210a674b138719f9d64736296755ea3d147ea987162090cd9f82deb858a0e91d'
        and source_refs[2]['sha256']=='5c368ebfae7c494712c880044925c32b4ede0aca75e00be9aa97e4ed3c02079c'
        and source_refs[3]['sha256']=='720fec8ef352f9fe993aabff7f5e355de86f153b38f6004fd040c316c1fe0358'
        and review_refs[0]['sha256']=='ea3a33f2dba9546fbdef9376ce14a491713aab587e8ac395593980aad42af277'
        and review_refs[1]['sha256']=='7d578f9d96bf8ed19540d8ce58c259543fa740b094d9f07f4c32b54191f96fb8'
        and review_refs[2]['sha256']=='303a8f11bd8308e7ea0b919116163ccf3a6856771c7bade0ce90da9b3b532851'
        and decision['decision']=='ACCEPTED_SOURCE_ONLY' and decision['execution_grant'] is False
        and decision['runtime_closure_reviewed'] is True and oldh['manifest_ref']==s.pin(OLD/'MF.json')
        and oldh['input_contract_ref']==s.pin(OLD/'actual-input-contract.json') and oldh['input_contract_ref'] in oldmf['members'])
    mapping={tuple(ref[key] for key in ('path','sha256','bytes')):new for ref,new in zip(before['accepted_Source_refs'],source_refs)}
    mapping.update({tuple(ref[key] for key in ('path','sha256','bytes')):new for ref,new in zip(before['accepted_Source_review_refs'],review_refs)})
    source_raw=g.get_buffer(sh['caller_ref']['path']);tree=ast.parse(source_raw)
    functions={node.name:node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    def rebase(value):
        if type(value) is dict:
            if set(value)=={'path','sha256','bytes'}:
                return copy.deepcopy(mapping.get(tuple(value[key] for key in ('path','sha256','bytes')),value))
            item={key:rebase(child) for key,child in value.items()}
            if item.get('ref')==sh['caller_ref'] and item.get('function') in functions:
                node=functions[item['function']];item.update(line=node.lineno,end_line=node.end_lineno)
            return item
        if type(value) is list:return [rebase(child) for child in value]
        return value
    current=rebase(before)
    current['accepted_Source_refs']=source_refs;current['accepted_Source_review_refs']=review_refs
    current['purpose']='Prepare the existing component review input contract for Source04 GEN02. No future actual fact or acceptance is inferred.'
    literals={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in ('KEY','SLICE','MODE','STATE','PREDECESSOR'):
                    literals[target.id]=ast.literal_eval(node.value)
    check('GEN02_literals_and_exact_existing_seven_input_layout',literals['KEY']=='public22_to_main23_continuation_gen02'
        and literals['SLICE']=='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02'
        and literals['MODE']=='PUBLIC22_TO_MAIN23_CONTINUATION_ONLY'
        and set(contract['actual_request_required_fields'])==set(current['Root_execute']['actual_request_required_fields'])
        and current['Root_execute']['expected_success_status']=='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW')
    current['generation']=dict(key=literals['KEY'],slice_id=literals['SLICE'],state=literals['STATE'],mode=literals['MODE'],
        predecessor_scope_ref=literals['PREDECESSOR']['scope_ref'],predecessor_failed_case_ref=literals['PREDECESSOR']['actual_failed_case_ref'],
        original1201_result='FAILED_RETAINED',original1201_native_children=0,
        predecessor_archive_is_not_current_authority=True,fresh_Root_scope_and_lease_required=True,
        exact_before_failure_counters_and_next_preserved=True,dynamic_current_four_required=True,
        predecessor_source=dict(ref=sh['caller_ref'],function='predecessor_generation',line=functions['predecessor_generation'].lineno,end_line=functions['predecessor_generation'].end_lineno))
    current['Root_registration']['generation_binding']=dict(KEY=literals['KEY'],SLICE=literals['SLICE'],MODE=literals['MODE'],STATE=literals['STATE'],
        fresh_before_current4='Root actual current4 when new registration is issued; CP386/OW190 archives cannot supply current counters or authority.',
        consumed_old_generation_scope_for_execution=False)
    current['Root_execute']['truncated_stdout_rule']='Retain every actual initial/completion pair and raw output unchanged. Parse the complete immutable case.closed.json for full state; never reconstruct a truncated JSON body. Verify Root exact Source04 execute argv, actual request/preentry, observed terminal host/Python exits and markers as actually captured. A separately complete returned state may be supplied, with only the Source-defined closed_receipt_ref timing difference.'
    current['Root_execute']['returned_vs_saved_rule']='Use the full immutable case.closed.json as primary state. If a complete returned state exists, compare it with only the Source-defined closed_receipt_ref timing difference. If external stdout was truncated, preserve truncation and record returned state unavailable rather than synthesize it.'
    current['new_child_evidence']['original1201_exclusion']='Original1201 was closed/failed before Native. Its old case proves predecessor failure only and cannot satisfy any new GEN02 child or accepted case.'
    current['database_oracle']['working22_Source04_compatibility']=dict(source=dict(ref=sh['caller_ref'],function='validate_working22',
        line=functions['validate_working22'].lineno,end_line=functions['validate_working22'].end_lineno),
        requirements=['All retained table observations equal.','Workcopy SHA256 and byte count equal retained22.','All three ledger vectors exactly 1..22.',
            'Full Native schema SHA matches sealed full rows and manifest.schema_hash.','Historical non-internal schema SHA remains bound without rewriting retained observations.'])
    current['cleanup_and_acceptance']['original1201_result']='FAILED_RETAINED'
    current['cleanup_and_acceptance']['future_actual_result']=None;current['cleanup_and_acceptance']['future_actual_verdict']=None
    for key in ('actual_request_ref','registration_facts_ref','registration_result_ref','execute_preentry_audit_ref','execute_initial_host_capture_ref','execute_completed_host_capture_ref','case_closed_ref','actual_returned_state_ref'):
        current['future_delivery'][key]=None
    current['current_preparation']['actual_component_accepted']=False
    current['current_preparation']['actual_scope_issued']=False
    current['current_preparation']['actual_native_children']=0
    current['reuse']['Source04_runtime_review']=dict(evidence_ref=decision['runtime_closure_evidence_ref'],manifest149=True,actual_public144=True,
        replay=False,future_Root_current_entry_observation_required=True,future_Runtime_qualification_issued=False)
    intake=s.inert(D/'actual_review_intake.source.py',g.get_buffer(str(D/'actual_review_intake.source.py')))
    pending=intake.prepare(current)
    check('prepared_null_inputs_and_no_automatic_actual_acceptance',pending['status']=='PREPARED_PENDING_ACTUAL'
        and pending['actual_component_review_performed'] is False and pending['execution_grant'] is False
        and all(value is None for value in pending['future_inputs'].values())
        and current['three_phase_oracles']==rebase(before['three_phase_oracles']))
    draft=copy.deepcopy(current);draft['future_delivery']['case_closed_ref']=literals['PREDECESSOR']['actual_failed_case_ref']
    rejected=None
    try:intake.prepare(draft)
    except ValueError as exc:rejected=str(exc)
    check('old_failed_case_cannot_be_preaccepted_by_prepare',rejected=='ACTUAL_FACTS_REQUIRE_SEPARATE_REVIEW')
    contract_ref=s.write('actual-input-contract.json',current)
    calling_ref=s.write('root-calling-contract.source.json',dict(schema='researchos.public22-continuation-review-intake-calling-contract.v1',
        actor_id=intake.ACTOR,backend_actor_id=intake.BACKEND,review_author='codex:/root/full_w09_source_review',status='PREPARED_PENDING_ACTUAL',
        caller_ref=s.pin(D/'actual_review_intake.source.py'),input_contract_ref=contract_ref,
        prepare_argv=['LOCKED_PYTHON','-I','-S','-B','-X','utf8',str(D/'actual_review_intake.source.py'),'prepare','contract.path','contract.sha256','contract.bytes'],
        modes=['prepare'],future_seven_actual_ref_fields=list(intake.FIELDS),
        future_actual_inputs={key:None for key in intake.FIELDS},accepted_Source04_review_refs=review_refs,
        actual_review_execution='Await Root fresh GEN02 registration and complete three-phase bundle. This intake performs only preparation/input layout and cannot issue actual qualification or formal acceptance.',
        execution_grant=False,formal_acceptance=False,parent_acceptance=False))
    output=dict(input_contract_ref=contract_ref,calling_contract_ref=calling_ref,caller_ref=s.pin(D/'actual_review_intake.source.py'),
        source_refs=source_refs,Source04_review_refs=review_refs,old_preparation_hdf_ref=s.pin(OLD/'HDF.json'),old_preparation_manifest_ref=s.pin(OLD/'MF.json'),
        prior_input_contract_ref=s.pin(OLD/'actual-input-contract.json'),reuse_runtime149_144=True,actual_inputs=None,
        actual_component_review_performed=False,actual_component_accepted=False,product_calls=0)
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc));raise
finally:
    guard_ref=s.write('preparation-source-guard.closed.json',g.close())
    result_ref=s.write('preparation-result.json',dict(checks=checks,count=len(checks),passed=sum(item['passed'] for item in checks),failure=failure,
        source_guard_ref=guard_ref,held_count=len(refs),actual_inputs=None,actual_component_accepted=False,product_calls=0,
        execution_grant=False,formal_acceptance=False))
if output is not None:s.write('preparation-context.json',output)
print(json.dumps(dict(status='PREPARED_PENDING_ACTUAL' if failure is None else 'PREPARATION_FAILED',count=len(checks),
    passed=sum(item['passed'] for item in checks),result_ref=result_ref,source_guard_ref=guard_ref,actual_inputs=None,
    execution_grant=False,formal_acceptance=False),ensure_ascii=False))
