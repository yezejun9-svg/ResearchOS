"""Save additive continuation evidence; never write canonical or product files."""
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]

def ref(relative):
    p = ROOT / relative
    raw = p.read_bytes()
    return {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref((OUT / name).relative_to(ROOT).as_posix())

before = [p.read_bytes() for p in CANON]
cp, ow = [json.loads(raw) for raw in before[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [324, 152, 430]
assert cp['head'] == 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
assert cp['current_effective_formal_status']['formal_cases_accepted'] == 0
pending = [
    ('execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_preparation_codex/7bf10c8e8cc54412ba7bb89b53f5a622/failure-origin.e1bbac.json', '31476b8568f1e2e7b8e9b80200f7ec3c81e3e91e7d13d2c8c9060fb23b67ba34'),
    ('execution/v2.4/receipts/W13/W13-03/desktop15_source_import_suitability_independent_review_codex/d2215541c83c463db77326ffb2077dd7/failure-origin.c527ee.json', '3af61608e971242c99ec4829671157d5c0fe02072e8f0ab197c9f93d0fa58f8b'),
    ('execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39/failure-origin.8861e3.json', 'a813aefb3c674c1ed982e37a7874affb40b71828b3b0b1029647583a8d0cd501'),
]
pending_refs = []
for name, expected in pending:
    item = ref(name)
    assert item['sha256'] == expected
    pending_refs.append(item)
links = {
    'actual_registration_audit': 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324/registration-audit.json',
    'actual_registration_manifest': 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324/manifest.json',
    'source_import_final_review': 'execution/v2.4/receipts/W05/W05-99/cli43_closed_execution_independent_review_codex/62e0bad3597f4faa9addb47da466fe3e/review.json',
    'fresh_cli_preparation_review': 'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_static_independent_review_codex/5c8ee5e41f66448c808512ae793d960c/review.json',
    'go_provider_documentation_observation': 'execution/v2.4/receipts/W05/W05-99/resource_lookup_codex/opencode-go-docs-20261007/observation.json',
}
audit = save('audit.json', {
    'schema': 'researchos.additive-root-continuation-evidence.v1', 'actor': 'codex:/root',
    'goal_status': 'ACTIVE', 'current': [324, 152, 430], 'head': cp['head'],
    'canonical_refs': [ref(p.relative_to(ROOT).as_posix()) for p in CANON],
    'closed_source_import_paths': 8, 'unique_combined_source_paths': 43,
    'refs': {key: ref(value) for key, value in links.items()},
    'postcut_pending_origin_refs': pending_refs, 'pending_count': 3, 'observed_origin_lower_bound': 433,
    'counter_reset': False, 'failure_ledger_writes': 0, 'source_or_canonical_writes': 0,
    'current_formal_accepted': 0, 'formal_required': 42, 'parent_required': 22,
    'goal_complete': False, 'fresh43_compiler_or_cases_executed_in_this_continuation': False,
    'current_task_packet': {'actual_tool_chunk': '37a12b', 'outer_exit': 0, 'selected_card': 'W05-99', 'product_acceptance': 'NOT_ASSERTED'},
    'next_actions': [
        'Finish and independently review the changed CLI43 preparation addressing the three static findings; current two held leaves remain NOT_RUN.',
        'Root explicitly binds the full actual public toolchain/runtime inputs and a new finite scope, registers only after independent review, then compiles and replays once.',
        'Append every selected postcut origin once to the preserved 430-origin prefix in a future explicit CAS; do not infer native exits.',
        'Finish Desktop source-only suitability and future explicit scope binding; do not change Main HEAD during current-source validation.',
        'Keep all remaining W05, Desktop, SDK, installed UI, recovery, live resources and 22/42 formal gates open until their actual evidence is accepted.'
    ],
    'model_preference': 'deepseek-v4.1-flash', 'model_endpoint_from_go_docs': 'https://opencode.ai/zen/go/v1/chat/completions',
    'model_account_qualification_from_public_docs': False, 'credentials_read_or_unsealed': 0,
    'new_authenticated_model_calls': 0,
})
assert [p.read_bytes() for p in CANON] == before
manifest = save('manifest.json', {'entries': [ref(Path(__file__).relative_to(ROOT).as_posix()), audit], 'self_excluded': True})
print(json.dumps({'audit_ref': audit, 'manifest_ref': manifest, 'canonical_changed': False}, ensure_ascii=True))
