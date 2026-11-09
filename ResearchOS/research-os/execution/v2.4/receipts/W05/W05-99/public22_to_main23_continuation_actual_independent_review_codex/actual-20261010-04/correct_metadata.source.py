from pathlib import Path
import copy, datetime, hashlib, json, types

R = Path(r'D:/作品集/ResearchOS/research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
A3 = D.parent/'actual-20261010-03'
PR = B/'public22_to_main23_continuation_independent_review_codex/review-20261010-04-full'
S = W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
support = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw_support = support.read_bytes()
assert len(raw_support) == 4940 and hashlib.sha256(raw_support).hexdigest() == '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s = types.ModuleType('metadata_correction_support');s.__file__ = str(support)
exec(compile(raw_support, str(support), 'exec'), s.__dict__);s.D = D

anchors = [
    s.exact_ref(A3/'HDF.json', 'aecd458d43c522874b46dababc8b292b8bd457ee16438837d88f2fb1ff8b7c36', 10690),
    s.exact_ref(A3/'MF.json', '21750bb046e0cc98eb5217f7e015bd713204e1a8418166d2371e42ec887bfd3a', 6288),
    s.exact_ref(A3/'review-decision.json', '1d91f03cbac38291fa115477c252e37f3ce54229ca71f9c1cf451435310d3125', 17666),
    s.exact_ref(PR/'HDF.json', 'ea3a33f2dba9546fbdef9376ce14a491713aab587e8ac395593980aad42af277', 14539),
    s.exact_ref(PR/'MF.json', '7d578f9d96bf8ed19540d8ce58c259543fa740b094d9f07f4c32b54191f96fb8', 6213),
    s.exact_ref(PR/'decision.json', '303a8f11bd8308e7ea0b919116163ccf3a6856771c7bade0ce90da9b3b532851', 23135),
    s.exact_ref(S/'original1233.fixed-actual.binding.root.json', 'a9985b2302fb648293c1fbb4af2b4afcb3d102197f160abc52ffca8910ede1a7', 1601),
    s.exact_ref(S/'original1233.fixed-actual.raw.root.jsonl', '9c76703cb03c0e8a52046bb1af334dc63c0516fb64cbe3fd2a34d7a38fae23a0', 26972),
]
for ref in anchors: assert s.pin(ref['path']) == ref
original_mf = json.loads((A3/'MF.json').read_bytes())
retained_members = original_mf['members']
pairs = [s.capture('2d22f7', 0, 0), s.capture('b9f7eb', 0, None), s.capture('e05990', 0, 0)]
own_refs = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file()]
refs = list({ref['path']: ref for ref in anchors + retained_members + own_refs}.values())
g = s.guard(); observations = []
def check(name, ok, detail=None):
    observations.append({'name': name, 'passed': bool(ok), 'detail': detail})
    assert ok, name
def encode(v): return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
try:
    g.acquire(refs)
    def read(p): return g.get_buffer(str(p))
    old_hdf_raw, old_decision_raw = read(A3/'HDF.json'), read(A3/'review-decision.json')
    old_hdf, old_decision = json.loads(old_hdf_raw), json.loads(old_decision_raw)
    source_hdf = json.loads(read(PR/'HDF.json'))
    good_ref = anchors[5]
    check('actual_Source04_decision_exact_pin_and_published_HDF_binding', source_hdf['source_decision_ref'] == good_ref)
    bad_ref = old_decision['source_review_refs'][2]
    check('original_bad_reference_preserved_as_metadata_defect', bad_ref['path'] == str(PR/'review-decision.json') and not Path(bad_ref['path']).exists() and bad_ref['sha256'] == good_ref['sha256'] and bad_ref['bytes'] == good_ref['bytes'] and old_hdf['source_review_refs'][2] == bad_ref)
    facts = json.loads(read(A3/'actual-review-checks.json'))
    check('retained_30_actual_checks_are_exact_successful_original_artifact', facts['count'] == facts['passed'] == 30 and facts['failure'] is None and all(x['passed'] is True for x in facts['checks']) and old_hdf['actual_check_result_ref'] == s.pin(A3/'actual-review-checks.json'))
    retained_guards = []
    for name in ('inventory-guard.closed.json', 'expansion-guard.closed.json', 'actual-review-guard.closed.json', 'seal-source-guard.closed.json'):
        v = json.loads(read(A3/name))
        assert v['verification'] == 'PASSED' and v['closed'] is True and v['retained_handles_count'] == 0 and v['failure'] is None and v['errors'] == []
        retained_guards.append(s.pin(A3/name))
    check('original_fact_guards_closed_and_oracle_facts_retained_without_replay', facts['summary']['readonly_SQLite_oracle_connections'] == 3 and facts['summary']['new_child_exits'] == [0,0,0] and facts['summary']['all_Jobs_closed'] is True and facts['summary']['returned_state_reconstructed'] is False)
    corrected_decision = copy.deepcopy(old_decision)
    corrected_decision['source_review_refs'][2] = good_ref
    inverse_decision = copy.deepcopy(corrected_decision)
    inverse_decision['source_review_refs'][2] = bad_ref
    check('exact_one_reference_decision_delta_and_full_byte_inverse', encode(inverse_decision) == old_decision_raw)
    original_io = {'raw_ref': anchors[7], 'binding_ref': anchors[6]}
finally:
    closed = g.close()
    new_guard_ref = s.write('metadata-source-guard.closed.json', closed)
assert closed['verification'] == 'PASSED' and closed['closed'] is True and closed['retained_handles_count'] == 0 and closed['failure'] is None and closed['errors'] == []
assert all(x['verified'] is True and x['closed'] is True for x in closed['entries'])

decision_ref = s.write('review-decision.json', corrected_decision)
metadata_report = {
    'schema': 'researchos.public22-continuation-actual-review-metadata-correction.v1',
    'actor_id': 'codex:/root/full_w09_source_review', 'backend_actor_id': '/root/full_w09_source_review',
    'corrected_utc': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
    'original_review_refs': anchors[:3], 'corrected_decision_ref': decision_ref,
    'field': '/source_review_refs/2/path', 'before_ref': bad_ref, 'after_ref': good_ref,
    'meaning': 'Correct only the metadata spelling of the existing Source04 decision file. Its SHA256 and byte count are unchanged.',
    'checks': observations, 'passed': len(observations), 'failed': 0,
    'exact_decision_byte_inverse': True, 'all_other_decision_fields_unchanged': True,
    'retained_actual_fact_result_ref': old_hdf['actual_check_result_ref'],
    'retained_30_actual_checks_replayed': False, 'retained_three_SQLite_oracles_replayed': False,
    'retained_original_guard_refs': retained_guards, 'new_guard_ref': new_guard_ref,
    'metadata_read_hostpairs': pairs,
    'original1233': {'ordinal': 1233, 'status': 'FAILED_RETAINED_METADATA_DEFECT', 'actual_chunk_id': 'caacd8', 'actual_outer_exit': 0, 'actual_Python_exit': 0, 'actual_Native_exit': None, 'actual_Go_exit': None, 'actual_SQL_exit': None, 'actual_TP_exit': None, 'actual_RootStage_exit': None, 'actual_model_exit': None, 'original_io': original_io, 'product_failure': False, 'counter_reset': False},
    'all_guards_closed_zero': True, 'retained_handles_count': 0, 'live_Canon_handles_held': 0,
    'new_review_failures': [], 'product_calls': 0, 'execution_grant': False, 'formal_acceptance': False,
    'full20to24': 'OPEN',
}
report_ref = s.write('metadata-correction.json', metadata_report)
members = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
mf_ref = s.write('MF.json', {
    'schema': original_mf['schema'], 'actor_id': original_mf['actor_id'], 'backend_actor_id': original_mf['backend_actor_id'],
    'member_count': len(members), 'members': members,
    'member_scope': 'A4 metadata correction files; actual30 checks and three database oracles remain the original A3 facts.',
    'all_guards_closed_zero': True, 'execution_grant': False, 'formal_acceptance': False,
})
corrected_hdf = copy.deepcopy(old_hdf)
corrected_hdf['source_review_refs'][2] = good_ref
corrected_hdf['decision_ref'] = decision_ref
corrected_hdf['manifest_ref'] = mf_ref
corrected_hdf['metadata_correction_ref'] = report_ref
corrected_hdf['original_review_handoff_ref'] = anchors[0]
restored_hdf = copy.deepcopy(corrected_hdf)
restored_hdf.pop('metadata_correction_ref');restored_hdf.pop('original_review_handoff_ref')
restored_hdf['source_review_refs'][2] = bad_ref
restored_hdf['decision_ref'] = old_hdf['decision_ref'];restored_hdf['manifest_ref'] = old_hdf['manifest_ref']
assert encode(restored_hdf) == old_hdf_raw
hdf_ref = s.write('HDF.json', corrected_hdf)
print(json.dumps({'HDF_ref': hdf_ref, 'MF_ref': mf_ref, 'decision_ref': decision_ref, 'metadata_correction_ref': report_ref, 'corrected_Source04_decision_ref': good_ref, 'metadata_checks': len(observations), 'retained_actual_checks': 30, 'retained_readonly_oracles': 3, 'actual_checks_replayed': False, 'exact_HDF_byte_inverse': True, 'retained_handles_count': 0, 'verdict': 'QUALIFIED_COMPONENT_ONLY', 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
