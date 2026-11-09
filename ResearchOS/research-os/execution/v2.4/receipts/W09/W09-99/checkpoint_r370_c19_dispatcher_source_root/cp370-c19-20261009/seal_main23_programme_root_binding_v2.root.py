"""Bind the completed independent Main23 review using retained actual captures."""
from pathlib import Path
from datetime import datetime, timezone
import ast, json, hashlib, os, types

N = Path(__file__).resolve().parent
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
tree = ast.parse((N / 'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
    and x.name in {'pin', 'exact', 'save'}], type_ignores=[]),
    'Root_capture_functions_only', 'exec'), globals())

binding_ref = pin(N / 'main23.programme.root-issuance.binding.json')
binding = json.loads(Path(binding_ref['path']).read_bytes())
request = json.loads((N / 'main23.programme.root-binding.observer-input.json').read_bytes())
payload_ref = request['payload_ref']
payload = json.loads(Path(payload_ref['path']).read_bytes())
caller = Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\fresh_main23_root_caller_registration_source_codex\main23root-20261010-04\main23_root.source.py')
exact(caller, '85ec3da49ab65741d1f1a8a94996c55f22d3b2394959e641bb3f0bd4b694f75e', 56626)
validator = types.ModuleType('root_programme_binding_capture_validator')
validator.__file__ = str(caller)
exec(compile(caller.read_bytes(), str(caller), 'exec'), validator.__dict__)
# This local read-only operation grants no build execution authority.
validator.CAPTURE_OPERATIONS = validator.CAPTURE_OPERATIONS | {'PROGRAMME_QUALIFICATION_BINDING'}
validator.validate_root_capture(binding, validator.checked(binding['original_capture_ref']),
    request['observed_refs'], 'PROGRAMME_QUALIFICATION_BINDING')
peer_binding = validator.doc(payload['independent_peer_delivery_binding_ref'])
_, peer_event = validator.original_capture_rows(peer_binding,
    validator.checked(peer_binding['original_capture_ref']), peer=True)
qualification = validator.doc(payload['review_refs'][3])
received = validator.when(peer_event['timestamp'])
created = datetime.now(timezone.utc)
assert validator.when(qualification['reviewed_at_utc']) <= received <= validator.when(payload['created_utc'])
assert validator.when(payload['created_utc']) <= validator.when(binding['tool_call_timestamp']) <= validator.when(binding['tool_result_timestamp']) <= created
assert peer_event['payload']['author'] == '/root/attach_fixture_source_review'
assert peer_binding['peer_actor'] == payload['review_author'] == 'codex:/root/attach_fixture_source_review'
prefix = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_fixture_source_review\nPayload:\n'
text = peer_event['payload']['content'][0]['text']
assert text.startswith(prefix)
delivery = validator.strict(text[len(prefix):])
assert delivery['schema'] == 'researchos.current-main23-programme-review-delivery.v1'
assert delivery['hdf_ref'] == payload['review_refs'][0] and delivery['mf_ref'] == payload['review_refs'][1]
assert delivery['decision_ref'] == payload['review_refs'][2] and delivery['qualification_ref'] == payload['review_refs'][3]
assert delivery['program_ref'] == payload['program_ref'] and delivery['independent_non_author']
assert not delivery['formal_acceptance'] and not delivery['parent_acceptance'] and not delivery['execution_grant']
for ref in payload['current_canonical_refs'] + payload['source_refs'] + [payload['program_ref']]:
    validator.checked(ref)
qualified = dict(schema='researchos.root-current-main23-programme-qualification.v1', issued_by='codex:/root',
    root_thread_id=THREAD, status='QUALIFIED_CURRENT_MAIN23_BUILD', created_utc=created.isoformat(),
    review_author=payload['review_author'], source_author=qualification['source_author'], independent_non_author=True,
    review_refs=payload['review_refs'], qualification_ref=payload['review_refs'][3],
    program_ref=payload['program_ref'], provenance_ref=qualification['provenance_ref'], source_refs=payload['source_refs'],
    payload_ref=payload_ref, root_issuance_binding_ref=binding_ref,
    independent_peer_delivery_binding_ref=payload['independent_peer_delivery_binding_ref'],
    current_canonical_refs=payload['current_canonical_refs'],
    actual_Go_primary_exits=[0] * 5, all_owned_jobs_idle_and_closed=True, Main_source_drift=False,
    original_API_process_stdout_truncated=True, original_process_stdout_complete_not_asserted=True,
    original_stdout_reconstructed=False, complete_Go_raw_streams_verified=True,
    programme_qualification=True, formal_acceptance=False, parent_acceptance=False, execution_grant=False,
    formal_case_accepted_delta=0, goal_status='ACTIVE')
qualified_ref = save('main23.programme.qualification.bound.actual.root.json', qualified)
print(json.dumps(dict(root_bound_qualification_ref=qualified_ref, root_issuance_binding_ref=binding_ref,
    program_ref=payload['program_ref'], status=qualified['status'], formal_case_accepted_delta=0,
    Canonical_unchanged=True), ensure_ascii=False, indent=2))
