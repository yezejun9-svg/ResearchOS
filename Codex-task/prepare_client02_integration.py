"""Read-only plan preparation; does not mutate D or integrate any source."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
REL = 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients'
OUT = ROOT / REL
REVIEW = OUT / 'reviews/freeze-02/source-review.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
assert sha(REVIEW) == 'e85f39c0ba2fae6cf7d068f893635b6fa836cd7db1f4312720dd16ba48665103'
r = read(REVIEW)
assert r['decision'] == 'APPROVE_CLIENT_WIRING_ONLY_NOT_NATIVE_OR_W14_ACCEPTANCE'
assert r['root_source_integration_supported'] is True
assert not r['pending_blockers'] and r['formal_increment'] == 0
assert r['construction_frozen'] is True and r['source_modification_permitted'] is False
assert all(r['tests'][key]['exit_code'] == 0 for key in ('independent_go', 'independent_vet', 'independent_node', 'independently_rerun_author_node'))
assert r['tests']['independent_go']['total_test_records'] == 47
assert r['tests']['independent_node']['pass_count'] == 54
assert len(r['source_sha256']) == 8
manifest = OUT / 'author/freeze-02/MANIFEST.final.json'
assert sha(manifest) == '12252ed255167a9a60398680145dd50c86ffef4dfcba7969b81f7edc32f61784'
frozen = read(manifest)
pins = {}
for item in frozen['raw_and_support_files']:
    p = manifest.parent / item['path']
    assert sha(p) == item['sha256']
    pins[str(p.relative_to(ROOT))] = item['sha256']
archive = read(REVIEW.parent / 'ROOT_ARCHIVE.json')
for item in archive['entries']:
    p = REVIEW.parent / item['path']
    assert sha(p) == item['sha256']
    pins[str(p.relative_to(ROOT))] = item['sha256']
pins[str(manifest.relative_to(ROOT))] = sha(manifest)
for name, expected in {
    'commands.json': 'dc5f7fe16ce55d1fd1d9c50df4df96e266f454a76416d817ed7e62406226f279',
    'step_state.json': '168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e',
    'path_ownership.json': 'af02ff444f344b51e5311f9baa09aff71f7a77816728097e70a2326f09094bcc',
}.items():
    p = ROOT / 'execution/v2.4' / name
    assert sha(p) == expected
    pins[str(p.relative_to(ROOT))] = expected
events = read(HERE / 'cp598-root-diagnostics.json')['events']
for chunk in ('483288', '7bd97b'):
    events.append(dict(origin_key='20261104|cp598-client-author-lookup|' + chunk,
        classification='OPTIONAL_READ_ONLY_LOOKUP_NO_MATCH_NOT_PRODUCT_FAILURE',
        detail=dict(tool_chunk=chunk, ref=REL + '/author/freeze-02/AUTHOR-DIAGNOSTICS.json')))
events.extend([
    dict(origin_key='20261104|cp598-client-review02|post-freeze-session-loss', classification='INFRASTRUCTURE_TRANSPORT_LOSS_WRITER_TERMINAL_UNKNOWN_NOT_SOURCE_FAILURE',
         detail=dict(session=74834, frozen_report_sha256=sha(REVIEW), addendum_ref=REL + '/reviews/freeze-02/post-freeze-disconnect-addendum.json',
                     outcome='Report write and content independently recovered; original writer terminal remains UNKNOWN, no freeze/test rerun or manufactured exit0.')),
    dict(origin_key='20261104|cp599-reconnect|170315', classification='READ_ONLY_LOCATOR_ERROR_NOT_PRODUCT_FAILURE',
         detail=dict(tool_chunk='170315', outcome='Root looked for task_packet.py and execution.plan.json under repository; actual authoritative paths are external specification package. Discovery718957 resolved paths; no mutation.')),
    dict(origin_key='20261104|cp599-reconnect|3685f5', classification='READ_ONLY_CIM_PERMISSION_DIAGNOSTIC_NOT_PRODUCT_FAILURE',
         detail=dict(tool_chunk='3685f5', outcome='C files read successfully; CIM denied. No process absence inferred from CIM; no write or retry.')),
    dict(origin_key='20261104|cp599-reconnect|git-default-sandbox', classification='READ_ONLY_GIT_SANDBOX_PERMISSION_DIAGNOSTIC_NOT_PRODUCT_FAILURE',
         detail=dict(tool_chunks=['98b527', 'ee7826'], outcome='Default sandbox Git could not enter D directory. Config bare=false. Authorized escalated read6be56c confirmed Main001f and original20 statuses; no Git config changes.')),
])
addendum = REVIEW.parent / 'post-freeze-disconnect-addendum.json'
assert sha(addendum) == 'd6fe83bcff48c9312017df4facbae04d94a98b5311d327901e717179b8eba244'
assert not read(addendum)['pending_source_blockers']
assert not read(addendum)['pending_evidence_readback_blockers']
prep = read(OUT / 'reviews/freeze-01/preparation.json')
for item in prep.get('diagnostics', []):
    events.append(dict(origin_key='20261104|cp598-client-review-preparation|' + item['tool_chunk'],
        classification='READ_ONLY_LOCATOR_DIAGNOSTIC_NOT_PRODUCT_FAILURE', detail=item))
scope_review = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/candidate-capture/reviews/design/design-review.json'
for item in read(scope_review).get('diagnostics', []):
    if item.get('chunk_id'):
        events.append(dict(origin_key='20261104|cp598-capture-design-review|' + item['chunk_id'],
            classification=item['classification'], detail=item))
cp = read(ROOT / 'execution/v2.4/checkpoint.json')
assert cp['revision'] == 599 and len(cp['failure_counters']) == 2437
plan = dict(root_only=True, formal_increment=0, scope_ref=REL + '/scope.json',
    scope_sha256=sha(OUT / 'scope.json'), receipt_ref=REL,
    review_ref=str(REVIEW.relative_to(ROOT)), review_sha256=sha(REVIEW), approved_decision=r['decision'],
    source_sha256=r['source_sha256'], evidence_pins=pins,
    expected_main_head='001f7e5a4d95152c8f83874a60d9fbd3bbace538',
    expected_checkpoint=599, expected_failure_records=2437, diagnostic_events=events,
    commit_message='feat(clients): add default-off native create attestation with strict send boundaries',
    result_status='CLIENT_NATIVE_CREATE_WIRING_INTEGRATED_DEFAULT_OFF_NOT_NATIVE_ACCEPTANCE',
    limits='Only default-off client wiring. Core prepared addon is not integrated or enabled; no live Native, old database, inference, business acceptance or full W14 handoff qualification. Pilot replay reacquires proof and can conservatively block when Native is unavailable.',
    next='Continue the exact22 Core and six-path private candidate capture source scopes, test and independently review. Register the prepared three-path sandbox cleanup fix when a construction slot frees. Preserve all failed attempts and do not replay consumed model probes.',
    active_construction_owners=['codex:/root/workbench_builder', 'codex:/root/delivery_binding_impl'],
    handoff_sentence='Independently reviewed exact8 client paths integrated with pilot default off; Core and candidate capture continue separately, old data and safety gates preserved.')
dest = HERE / 'client02-root-integration-plan.json'
assert not dest.exists(), 'Inspect prior plan and any integration journal, do not overwrite'
dest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(plan=str(dest), sha256=sha(dest), source_files=len(r['source_sha256']), evidence_pins=len(pins), diagnostic_events=len(events))))
