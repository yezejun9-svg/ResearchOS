"""IO/AST source review evidence only; no candidate/helper/Node imports."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;P13=HERE.parents[1]
OLD=P13/'fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4'
R=P13/'fresh58_desktop169_go3_independent_source_review_codex/14818767d60a485885f7c5e0e36135cd'


def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}


def put(n,v):
    with (HERE/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())


checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})


index=json.loads((HERE/'inverse-index.json').read_bytes())
for record in index['files']:
    base=Path(record['baseline_ref']['path']).read_bytes();p=Path(record['candidate_ref']['path']);raw=p.read_bytes()
    check('candidate-pin:'+p.name,ref(p)==record['candidate_ref'])
    backward=raw
    for e in reversed(record['edits']):
        a,b=e['old'].encode(),e['new'].encode()
        check('unique-inverse:'+p.name+':'+str(len(checks)),backward.count(b)==e['occurrences'])
        backward=backward.replace(b,a)
    check('full-byte-inverse:'+p.name,backward==base)
    ast.parse(raw)
scope=json.loads((HERE/'scope.v2.proposed.json').read_bytes())
oldscope=json.loads((OLD/'scope.proposed.json').read_bytes())
normalized=dict(scope)
for k in ['controller_ref','launcher_ref','debug_helper_ref','fixture_evaluator_ref']:normalized[k]=oldscope[k]
for k in ['controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']:
    check('future-NULL:'+k,normalized.pop(k) is None)
check('scope-exact-authorized-delta',normalized==oldscope)
check('authority-resource-scope-NOT_BOUND',scope['authorization_verifier_ref'] is None and scope['resource_catalog_ref'] is None and scope['expected_registration'] is None)
for k in ['inner_seconds','outer_seconds','builder_seconds']:check('total-budget-still-NULL:'+k,scope[k] is None)
controller=Path(scope['controller_ref']['path']).read_text(encoding='utf-8')
helper=Path(scope['debug_helper_ref']['path']).read_text(encoding='utf-8')
evaluator=Path(scope['fixture_evaluator_ref']['path']).read_text(encoding='utf-8')
launcher=Path(scope['launcher_ref']['path']).read_text(encoding='utf-8')
for name,value in [
 ('per-request-identity',"rid in requests" in evaluator and "pid not in seen_pids" in evaluator),
 ('exact-full-lifecycle',"all(item[k] is not None for k in ['body','finish','close'])" in evaluator),
 ('premature-close-refusal',"event['finished'] is True" in evaluator and "event['reader_complete'] is True" in evaluator),
 ('assertion-separate-from-transport',"state['source_assertions_passed']=True" in controller and "'transport_qualification':'OPEN'" in evaluator),
 ('failed-verdict-before-need',controller.index("save(case/'fixture-verdict.json',evaluation)")<controller.index("need(evaluation['qualified']")),
 ('caller-phase-reserve',"reserve=25+scope['cleanup_seconds']+scope['controller_evidence_reserve_seconds']" in controller),
 ('helper-absolute-deadline-passed',"absolute_deadline=helper_deadline" in controller),
 ('helper-normal-finalizer-clamped',"min(time.monotonic() + 25.0, absolute_deadline)" in helper),
 ('helper-cleanup-clamped',"min(time.monotonic() + 5.0, absolute_deadline)" in helper),
 ('helper-tail-never-late-qualified',"deadline_check(absolute_deadline, 'helper final owned-handle closure')" in helper),
 ('outer-phase-composition',"s['outer_seconds']>s['inner_seconds']+25+5+s['launcher_evidence_reserve_seconds']" in launcher),
 ('no-prebuilt-alias-change',scope['alias_roster_ref']==oldscope['alias_roster_ref'] and scope['instrumented_test_ref']==oldscope['instrumented_test_ref']),
 ('observer-byte-unchanged',scope['network_observer_ref']==oldscope['network_observer_ref']),
 ('original169-roster-unchanged',scope['roster_ref']==oldscope['roster_ref']),
 ('old6a-immutable',scope['owned_helper_ref']==oldscope['owned_helper_ref'])]:check(name,value)
before=json.loads((HERE/'inputs.before.json').read_bytes())['files']
check('own-input-after-zero-drift',[ref(Path(x['path'])) for x in before]==before)
oldmf=json.loads((OLD/'manifest.json').read_bytes())
for r in oldmf['entries']:check('old-prefix:'+Path(r['path']).name,ref(Path(r['path']))==r)
prior_origins=[ref(OLD/n) for n in ['failure-origin.1622f8.json','failure-origin.ef37a8.json']]
prior_origins += [ref(R/n) for n in ['failure-origin.058eb9.json','failure-origin.b27bd3.json']]
for p in HERE.glob('*.py'):ast.parse(p.read_bytes())
put('static-audit.json',{'checks':checks,'failed':sum(not x['passed'] for x in checks),
    'source_inverses':4,'candidate_imports':0,'helper_Dll_Node_Go_SQL_HTTP_models':0,
    'assertion_or_trace_tests_executed':False,'new_failure_origins':[],'prior_origin_refs_preserved_not_recounted':prior_origins})
assert all(x['passed'] for x in checks)
put('tool-observations.json',{'observations':[
    {'tool_chunk':x,'actual_outer_exit':0,'actual_native_exit':None,'kind':'Read-only source/catalog or own metadata IO/AST'}
    for x in ['a27c22','b17b43','986140','cbdc6c','4b2e85','c74e76','b3c0b1','b372c6','3f94c9','250fa3','dba190']],
    'prepare_tool_result_ref':ref(HERE/'prepare.tool-result.json'),'new_failure_origins':[],
    'note':'a27c22 text display was truncated; no JSON parsing failure or fabricated nonzero. Full review bytes are independently pinned.'})
put('handoff.json',{'schema':'researchos.desktop58-169-go3-source-revision-handoff.v1',
    'author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED',
    'old_request_ref':ref(R/'review.json'),'old_request_handoff_ref':ref(R/'handoff.json'),'old_request_manifest_ref':ref(R/'manifest.json'),
    'selected_refs':{k:scope[k] for k in ['controller_ref','launcher_ref','debug_helper_ref','fixture_evaluator_ref','network_observer_ref']},
    'scope_ref':ref(HERE/'scope.v2.proposed.json'),'contract_ref':ref(HERE/'contract-revision.json'),
    'inverse_ref':ref(HERE/'inverse-index.json'),'audit_ref':ref(HERE/'static-audit.json'),
    'controls_ref':ref(HERE/'future-controls.NOT_RUN.json'),'old_manifest_ref':ref(OLD/'manifest.json'),
    'findings_addressed':['D169-R01','D169-R02'],'all_four_whole_inverses':True,
    'original_observer_assertions_roster_aliases_unchanged':True,'old_manifest_members_rechecked':len(oldmf['entries']),
    'static_checks':len(checks),'static_failed':0,'actual_runtime_controls':'NOT_RUN',
    'new_failure_origins':[],'prior_origins_preserved':prior_origins,
    'source_acceptance':False,'formal_increment':0,'candidate_imported':False,'candidate_executed':False,
    'open':['Root authority adapter','Actual same-head fresh CLI2 qualification','Root actual public resource/runtime/graph closure',
       'Root numerical inner/outer/builder and two evidence IO reserve budgets','Independent source review and Root finite scope/grant',
       'All169+3 runtime controls; no expected-abort transport exception authorized'],
    'limits':['Per-request completion is source-only; no new HTTP lifecycle was observed.',
      'Absolute deadline checks reject late success but cannot preempt a blocking kernel call; Root outer-owned execution remains mandatory.',
      'Only original assertions PASS may set source_assertions_passed; transport remains separately false/OPEN on incomplete lifetime.']})
entries=[ref(p) for p in sorted(HERE.iterdir()) if p.is_file()]
put('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','self_excluded':True,'count':len(entries),'entries':entries})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'manifest':ref(HERE/'manifest.json'),'checks':len(checks),
                  'selected':{k:scope[k] for k in ['controller_ref','launcher_ref','debug_helper_ref','fixture_evaluator_ref']}},ensure_ascii=False))
