import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OUT = BASE / 'session_list_identity_independent_replay_codex/root-r310-534857db-public-plan'
CASE = OUT / 'cases/TestSessionListHTTPOriginalContextIdentity__NullContext'
LAUNCH = BASE / 'integration_codex/root-list14-launch-r310'
DRIVER = BASE / 'integration_codex/complete-public-graph-and-g2-r310/list_replay.v2.py'
SOURCE = ROOT / '.local/independent-session-list-r310-534857db-public-plan/internal/api/v2_sessions_test.go'

def ref(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

paths = [SOURCE, DRIVER, LAUNCH/'invocation.json', LAUNCH/'stderr.raw', LAUNCH/'stdout.raw',
    OUT/'driver.exception.json', OUT/'case-01.invocation.json', OUT/'case-01.stdout.raw',
    OUT/'case-01.stderr.raw', OUT/'case-01.before_native.inputs.json', OUT/'case-01.after_native.inputs.json',
    CASE/'closed-proof.json', CASE/'closed-original.files.json', CASE/'before-close.files.json',
    CASE/'closed.rows.json', CASE/'post-open.rows.json', CASE/'closed.sqlite',
    CASE/'closed.sqlite-wal', CASE/'closed.sqlite-shm', LAUNCH/'failure_origin.json', LAUNCH/'manifest.json']
before = [ref(p) for p in paths]
if before[0]['sha256'] != 'e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0':
    raise RuntimeError('pinned source mismatch')
if before[1]['sha256'] != '85e35100bd7ed509883a0ae4729f68aab283032002f8eb8784d28900e97c54ea':
    raise RuntimeError('pinned driver mismatch')
if before[-2]['sha256'] != '6503124cc34e7ec26e407030a7b34cd365d8d7c69ad27062cf0eb363915dc757' or before[-1]['sha256'] != '91eb5b9d95543a1fa1a5cd621ee463aec4c7c35bba15614169b0e953f3150278':
    raise RuntimeError('Root stopped seal mismatch')
copied = []
(HERE/'inputs').mkdir()
for i, p in enumerate(paths):
    if p.name.startswith('closed.sqlite'):
        continue
    dest = HERE/'inputs'/f'{i:02d}-{p.name}'
    with dest.open('xb') as f:
        f.write(p.read_bytes())
    copied.append({'original': ref(p), 'copy': ref(dest)})
load = lambda p: json.loads(p.read_bytes())
outer = load(LAUNCH/'invocation.json')
native = load(OUT/'case-01.invocation.json')
proof = load(CASE/'closed-proof.json')
original = load(CASE/'closed-original.files.json')
v1 = load(OUT/'case-01.before_native.inputs.json')
v2 = load(OUT/'case-01.after_native.inputs.json')
raw = (CASE/'closed.sqlite').read_bytes()
facts = {
    'outer_exit': outer.get('actual_exit'), 'driver_exit': 1,
    'driver_exit_basis': 'outer invocation directly launches driver; traceback ends AssertionError',
    'native_actual_exit': native['actual_exit'], 'native_process_observation': native['process_observation'],
    'before_after_native_vectors_equal': v1 == v2, 'vector_entries': len(v1),
    'vector_comparison_only': 'Compared recorded complete vectors; did not independently rehash every compile dependency in this readonly cause review',
    'closed_original_file_observation': original, 'closed_proof': proof,
    'closed_copy_and_sidecars_current': [ref(CASE/n) for n in ['closed.sqlite','closed.sqlite-wal','closed.sqlite-shm']],
    'raw_header': {'signature_hex': raw[:16].hex(), 'file_format_write_version_byte18': raw[18], 'file_format_read_version_byte19': raw[19]},
    'raw_header_read_is_not_SQL': True,
    'driver_SQL_open_reached': False, 'native_case_passed': True,
    'independent_closedcopy_case_accepted': False, 'remaining_cases': 13,
    'remaining_status': 'NOT_RUN_AFTER_FIRST_UNEXPECTED',
    'proof_missing': ['copy-path sidecar absence immediately before Go readonly open', 'copy-path sidecar absence after Go readonly close', 'direct process-level sidecar creation trace'],
}
save('facts.json', facts)
save('read_audit.json', {'schema':'researchos.readonly-input-audit.v1','before':before,'copied_inputs':copied,
    'SQL_DB_connection_calls':0,'case_execution':0,'source_mutations':0,'sidecar_mutations':0,
    'actual_tool_calls':[{'tool_id':x,'outer_exit':e} for x,e in [('345483',0),('fc0e77',0),('f17a80',1),('3b9394',0),('814901',0),('f5524d',0),('0e319e',0)]]})
save('failure_origins.json', [{'origin_id':'session-list-closedcopy-review-f17a80',
    'actor':'codex:/root/w05_merge_review','kind':'READONLY_LOCATOR_ERROR','outer_exit':1,'native_exit':None,
    'tool_call_output_id':'f17a80','raw_file':None,'raw_limitation':'Original command/output exists in tool trace, no contemporaneous raw file was captured',
    'command':'rg check_closed followed by Get-Content of nonexistent Root launch stderr.txt',
    'error':'Cannot find path root-list14-launch-r310/stderr.txt because it does not exist.',
    'correction':'3b9394 rg --files found stderr.raw; 814901 read actual stderr.raw with exit0',
    'product_case_count':0,'Root_driver_origin_distinct':True,'canonical_imported_by_this_agent':False}])
save('scope_proposal.json', {
    'decision':'MINIMAL_TEST_FIXTURE_CORRECTION_PROPOSED_NOT_AUTHORIZED',
    'source_commit':'534857db99fa5e694987f877af74c322eaa2a0b3',
    'exact_source_paths':['internal/api/v2_sessions_test.go'],
    'function_bounds':'sessionListFixture.closeEvidence (current lines760-825), plus new appended readonlyCopyOpen helper and necessary URI construction/import support in same test file; protect original14633-byte body',
    'required_changes':[
        'Require original database closed and both original sidecars absent before making an immutable standalone copy; refuse rather than silently copying sidecars.',
        'Keep exclusive creation of fresh closed.sqlite and preserve all original database bytes; record and require both copy-path sidecars absent immediately before its readonly open.',
        'Use new appended readonlyCopyOpen helper to open only that fully closed standalone copy using correctly escaped SQLite file URI with mode=ro&immutable=1; never apply immutable to active fixture database.',
        'After actual row/schema capture and sql.DB.Close, record main DB byte/hash equality and explicit existence facts for both sidecars; require both absent. Preserve close/read errors.',
        'Keep original full sqlite_schema/columns/typed-row multiset equality and all14 business/assertion cases, original command/replay/schema/permission/HTTP limits intact.',
        'Keep Root check_closed sidecar assertion and independent immutable SQL verification unchanged; no deletion of sidecars before or after verification.',
        'After Root grants implementation and execution, new source/test binary/full compiler vector and fresh fixture directories must be frozen. Preserve original case01 native0/driver1 and13NOT_RUN; do not reinterpret native0 as independent product acceptance.'
    ],
    'protected':['internal/domain/client_protocol_sessions.go','Root list_replay.v2.py assertions','SQL/schema/SDK','all original raw/DB/sidecars/proof'],
    'future_controls_status':'NOT_RUN',
    'not_proposed':'No cleanup command, no generic production DB behavior change, no weakening sidecar checks'
})
save('review.json', {
    'schema':'researchos.session-list-closedcopy-cause-review.v1',
    'reviewer':'codex:/root/w05_merge_review',
    'decision':'EVIDENCE_FIXTURE_GAP_CONFIRMED_CAUSE_INFERRED_MINIMAL_TEST_SCOPE_PROPOSED',
    'reviewed_at':datetime.now(timezone.utc).isoformat(),
    'candidate_commit':'534857db99fa5e694987f877af74c322eaa2a0b3',
    'source_ref':ref(SOURCE),'driver_ref':ref(DRIVER),'facts_ref':ref(HERE/'facts.json'),
    'confirmed':[
        'Actual Root traceback is check_closed line150 sidecar assertion before sqlite3.connect at153; this Root verification did not open this DB.',
        'Native case01 exit0 with all owned Job cleanup confirmed; driver/outer exit1 is an evidence-check failure, not a native product-test failure.',
        'Original closed source records no WAL/SHM. Fixture copies main bytes, optionally source sidecars, then opens copy via mode=ro without immutable at805 and captures rows at810.',
        'Go proof checks only copied main DB bytes and schema/row equality after Close. It has no copy-path sidecar before/after assertion. Current copied WAL and SHM exist.',
        'Source evidence gap cannot be repaired by relabeling native0 or deleting sidecars. Thirteen remaining cases did not run.'
    ],
    'causal_inference': 'The mode=ro non-immutable read of a WAL-format closed copy is the source-supported candidate cause of new sidecars. Original-sidecar absence plus source sequence and final presence support this inference, but there is no direct creation trace or explicit copy-path before/after-sidecar record; exact creator/timing remains unproven.',
    'source_cause_locations':[{'file':str(SOURCE),'lines':'784-805','meaning':'Close original, record source sidecar absence, exclusively save copy, reopen mode=ro'}, {'file':str(SOURCE),'lines':'810-822','meaning':'Read/close, main-bytes/rows proof only'}, {'file':str(DRIVER),'lines':'147-153','meaning':'Root fail before independent SQL open'}],
    'Root_unique_origin':{'launch_tool':'0f9faf','completion_tool':'d7304c','outer_exit':1,'driver_exit':1,'case_native_exit':0,'invocation_ref':ref(LAUNCH/'invocation.json'),'sealed_failure_ref':ref(LAUNCH/'failure_origin.json'),'sealed_manifest_ref':ref(LAUNCH/'manifest.json'),'count':1,'pending_Root_registration':True},
    'new_review_tool_origins_ref':ref(HERE/'failure_origins.json'),
    'scope_proposal_ref':ref(HERE/'scope_proposal.json'),
    'SQL_or_case_execution_by_reviewer':False,'source_acceptance':False,'formal_increment':0,
    'SDK_model_HTTP_paid_calls_by_reviewer':0
})
after = [ref(p) for p in paths]
save('after_inputs.json', {'after':after,'unchanged':before==after})
if before != after:
    raise RuntimeError('readonly inputs changed')
entries = [ref(p) for p in sorted(HERE.rglob('*')) if p.is_file()]
save('manifest.json', {'schema':'researchos.receipt-manifest.v1','entries':entries,'count':len(entries)})
save('handoff.json', {'review_ref':ref(HERE/'review.json'),'facts_ref':ref(HERE/'facts.json'),
    'manifest_ref':ref(HERE/'manifest.json'),'scope_proposal_ref':ref(HERE/'scope_proposal.json'),
    'failure_origins_ref':ref(HERE/'failure_origins.json'),'protected_inputs_unchanged':True,
    'actual_SQL_cases_models':0,'source_acceptance':False,'formal_increment':0})
print(json.dumps({'handoff':ref(HERE/'handoff.json'),'review':ref(HERE/'review.json'),'manifest':ref(HERE/'manifest.json'),'scope':ref(HERE/'scope_proposal.json'),'failure':ref(HERE/'failure_origins.json'),'facts':facts},ensure_ascii=False,indent=2))
