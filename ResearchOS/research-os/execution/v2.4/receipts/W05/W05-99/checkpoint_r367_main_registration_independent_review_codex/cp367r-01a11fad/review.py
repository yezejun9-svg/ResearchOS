import sys
sys.dont_write_bytecode = True
import ast, copy, hashlib, json, types
from pathlib import Path
N = Path(__file__).resolve().parent
C = N.parents[1] / 'checkpoint_r367_main_registration_source_root/cp367-main-20261009'
R = Path('D:/作品集/ResearchOS/research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
pins = {}
checks = []
def pin(path):
    p = Path(path).resolve(strict=True); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def hold(ref):
    ref = dict(path=str(Path(ref['path']).resolve(strict=True)), sha256=ref['sha256'].removeprefix('sha256:'), bytes=ref['bytes'])
    assert pin(ref['path']) == ref, ref
    key = ref['path'].casefold()
    assert key not in pins or pins[key] == ref
    pins[key] = ref
    return Path(ref['path']).read_bytes()
def load(ref): return json.loads(hold(ref))
def save(name, value):
    with (N/name).open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def check(name, condition):
    assert condition, name
    checks.append(name)
h = load(dict(path=str(C/'HDF.json'), sha256='84651263879683ca2307f07a6cf477c53955ce6d2f40a127aec59aa21fabd91c', bytes=2438))
mf = load(h['manifest_ref'])
for ref in mf['members']: hold(ref)
facts = load(h['facts_ref']); scope = load(h['scope_ref']); proof = load(h['source_preview_ref'])
contract = load(facts['calling_contract_ref'])
for pair in facts['reviews']:
    load(pair['handoff_ref']); m = load(pair['manifest_ref'])
    members = m['members']; members = list(members.values()) if isinstance(members, dict) else members
    for ref in members: hold(ref)
for ref in facts['actual_refs']: hold(ref)
origins = []
for item in facts['diagnostics']:
    origin = load(item['origin_ref']); origins.append(dict(item=item, original=origin))
    # Registration rows sometimes point at the actual immutable original tool pair.
    def nested(value):
        if isinstance(value, dict):
            if set(value) == {'path','sha256','bytes'}: hold(value)
            else:
                for child in value.values(): nested(child)
        elif isinstance(value, list):
            for child in value: nested(child)
    nested(origin)
raw = [hold(ref) for ref in facts['canonical_refs']]
old_c, old_o = [json.loads(v) for v in raw[:2]]
gp = B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw = hold(dict(path=str(gp), sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', bytes=11404))
gm = types.ModuleType('cp367review_guard'); gm.__file__ = str(gp); sys.modules[gm.__name__] = gm
exec(compile(graw, str(gp), 'exec'), gm.__dict__)
guard = gm.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
guard.acquire(list(pins.values()))
try:
    writer = hold(h['writer_ref']); tree = ast.parse(writer)
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ('require','pin','read','load','facts_scope','transform')]
    ns = dict(Path=Path, hashlib=hashlib, json=json, copy=copy, TARGETS=scope['exact_targets'], KEY='c19_main_source_registry_adoption', SLICE='C19_MAIN_SOURCE_REGISTRY_ADOPTION')
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<source-selected-pure-functions>', 'exec'), ns)
    got_scope, owner, worker = ns['facts_scope'](facts)
    check('source_scope_owner_worker_real_contract_pass', got_scope == scope)
    check('source_independent_decision_non_author', load(scope['source_review_decision_ref'])['actor_id'] not in ('codex:/root','codex:/root/command_queue_impl'))
    expected_exits = [(1,None),(1,1),(1,1),(1,None),(1,1),(1,None),(1,None),(1,1),(None,None),(1,1),(1,1)]
    check('diagnostic_ordinals937_to947_once', [v['ordinal'] for v in facts['diagnostics']] == list(range(937,948)))
    check('diagnostic_literal_exit_pairs_known_original', [(v['actual_outer_exit'],v['actual_python_exit']) for v in facts['diagnostics']] == expected_exits)
    check('all_native_exits_null', all(v['actual_native_exit'] is None for v in facts['diagnostics']))
    nc,no = ns['transform'](copy.deepcopy(old_c),copy.deepcopy(old_o),facts,h['facts_ref'],old_c,old_o,owner,worker,'INDEPENDENT_SOURCE_PREVIEW')
    check('old934_semantic_exact', nc['failure_counters'][:934] == old_c['failure_counters'] and len(old_c['failure_counters']) == 934)
    check('old934_plus11_equals945_registered', len(nc['failure_counters']) == 945)
    check('new_rows_exact_original_payloads', all(row['original_payload']['immutable_origin_ref'] == item['origin_ref'] and row['original_payload']['observed_ordinal'] == item['ordinal'] and row['original_payload']['actual_outer_exit'] == item['actual_outer_exit'] and row['original_payload']['actual_python_exit'] == item['actual_python_exit'] and row['original_payload']['actual_native_exit'] is None and row['counted_once'] is True and row['counter_reset'] is False for row,item in zip(nc['failure_counters'][934:],facts['diagnostics'])))
    check('worker_append_exact', nc['workers'] == old_c['workers']+[worker])
    check('owner_append_exact', no['card_path_bindings']['W09-99']['subtasks'][ns['KEY']] == owner)
    ic,io=copy.deepcopy(nc),copy.deepcopy(no)
    for k in ('failure_counters','workers','work_in_progress','expected_previous_revision','revision','updated_at','updated_by','note'): ic[k] = copy.deepcopy(old_c[k])
    del io['card_path_bindings']['W09-99']['subtasks'][ns['KEY']]
    for k in ('revision','updated_at','updated_by'): io[k] = old_o[k]
    check('independently_computed_complete_inverse', ic==old_c and io==old_o)
    pc=load(proof['proposed_checkpoint_ref']); po=load(proof['proposed_ownership_ref'])
    for doc in (nc,no,pc,po): doc.pop('updated_at',None)
    check('independent_transform_matches_sealed_preview', nc==pc and no==po)
    check('cutoff947_next948_preserved', nc['work_in_progress']['r367_highest_observed_diagnostic_ordinal_at_cutoff']==947 and nc['work_in_progress']['r367_next_failure_ordinal_at_cutoff']==948)
    live=nc['work_in_progress']['root_next_failure_ordinal_live']; later=nc['work_in_progress']['later_diagnostics_observed_after_cutoff']
    check('P1_live_regression_counterexample_reproduced', proof['Root_live_next_at_source_prepare']==949 and proof['later948_pending'] is True and live==948 and later==[])
    # Pure in-memory negative controls use the real source facts_scope validator.
    actual_load=ns['load']
    def reject(label, target, mutate):
        changed=copy.deepcopy(target); mutate(changed)
        def fake_load(ref):
            if target is scope and ref==facts['scope_ref']: return changed
            if target is contract and ref==facts['calling_contract_ref']: return changed
            if target is decision and ref==scope['source_review_decision_ref']: return changed
            return actual_load(ref)
        ns['load']=fake_load
        try:
            ns['facts_scope'](facts)
        except (ValueError, KeyError): checks.append(label)
        else: raise AssertionError(label+' unexpectedly accepted')
        finally: ns['load']=actual_load
    decision=actual_load(scope['source_review_decision_ref'])
    reject('reject_scope_extra_key',scope,lambda d:d.update(extra=True))
    reject('reject_scope_target_order',scope,lambda d:d['exact_targets'].reverse())
    reject('reject_scope_dispatcher_true',scope,lambda d:d.update(formal_dispatcher=True))
    reject('reject_scope_formal_bool',scope,lambda d:d.update(formal_case_accepted_delta=False))
    reject('reject_owner_extra_key',contract,lambda d:d['owner_exact_field_bindings'].update(extra=True))
    reject('reject_worker_extra_key',contract,lambda d:d['checkpoint_worker_exact_field_bindings'].update(extra=True))
    reject('reject_author_self_approval',decision,lambda d:d.update(actor_id='codex:/root'))
    reject('reject_source_decision_bad_sha',decision,lambda d:d['source_manifest_ref'].update(sha256='0'*64))
    reject('reject_source_decision_bad_bytes',decision,lambda d:d['caller_ref'].update(bytes=d['caller_ref']['bytes']+1))
    check('formal_zero_parents_w05_w09',nc['work_in_progress']['construction_active_parents']==['W05','W09'] and facts['formal_acceptance'] is False and facts['work_in_progress']['formal_current_count']==0)
    check('canonical_four_still_exact', [Path(r['path']).read_bytes() for r in facts['canonical_refs']]==raw)
    save('counterexample.json',dict(status='REPRODUCED_SOURCE_P1',source_preparation_live_next=949,source_preparation_pending948=True,transformed_live_next=live,transformed_later_pending=later,sealed_cut_high=947,sealed_cut_next=948,actual_canonical_written=False))
    save('diagnostic-originals.audit.json',origins)
    save('checks.json',checks)
finally:
    cleanup=guard.close(); save('source-guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and cleanup['errors']==[] and cleanup['retained_handles_count']==0
check('all_exact_inputs_unchanged',all(pin(r['path'])==r for r in pins.values()))
save('input-pins.json',list(pins.values()))
save('result.json',dict(status='REQUEST_CHANGES',P1=1,independent_checks=len(checks),finite_exact_inputs=len(pins),old934_plus11_pass=True,complete_inverse_pass=True,scope_owner_worker_pass=True,actual_canonical_written=False,actual_Main_written=False,formal_case_accepted_delta=0,new_original_failures=[],native_Go_SQL_API_model_executed=False))
print(json.dumps(dict(status='REQUEST_CHANGES',checks=len(checks),pins=len(pins),canonical_written=False,formal_delta=0)))
