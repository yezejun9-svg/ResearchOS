import base64
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

N = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
R = ROOT / 'execution/v2.4/receipts/W05/W05-99'
A = R / 'handler38_independent_replay_codex/363d72047db247eea2a76e91be26ed8c'
O = R / 'handler38_independent_replay_codex/c09-a0163b5c32ed44f7aca7730f3834e009'
S = R / 'handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b'
E = R / 'handler38_final_source_review_codex/1bfca99c7bd04ec7842ab2c810c35522'
C = ROOT / '.local/independent-handler38-a639cfcf'

def read(p):
    return json.loads(p.read_bytes())

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()

def ref(p):
    return {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def write(name, value):
    p = N / name
    with p.open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(p)

def require(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def subseteq(before, after, except_tables=()):
    return set(before) == set(after) and all(before[k] == after[k] for k in before if k not in except_tables)

def request(p):
    d = read(p)
    raw = base64.b64decode(d['raw_request_base64'], validate=True)
    require(len(raw) == d['raw_bytes'], 'raw length')
    require('sha256:' + hashlib.sha256(raw).hexdigest() == d['raw_sha256'], 'raw SHA')
    return json.loads(raw), raw

result = read(N / 'result.json')
before, after = read(N / 'source.before_first_case.json'), read(N / 'source.after_cases.json')
require(before == after and len(before) == 42966, 'C09 input drift/count')
require(result['actual_exit'] == 0 and result['not_run'] == [] and not result['source_drift'], 'C09 result')
require(read(N / 'cases.invocation.json')['actual_exit'] == 0, 'actual native exit')
for stage in ('gofmt', 'go-list', 'compile'):
    require(read(N / (stage + '.invocation.json'))['actual_exit'] == 0, stage)
require(sha(N / 'domain-c09-corrected.test.exe') == result['testexe_sha256'], 'testexe')
require(sha(N / 'overlay/handler_configuration_independent_review_test.go') == '65d085318b3c3fa81c30f05a4cbae8c122d67bcb0b4ee5c6ab1e3937e24263c2', 'overlay')

source38 = read(A / 'source38.current.json')
require(len(source38) == 38, 'source38 count')
for f in source38:
    require(sha(C / f['path']) == f['actual_sha256'], 'source drift ' + f['path'])
source_ref = write('source38.final-check.json', {'candidate': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8', 'files': source38, 'all_isolated_current_equal': True, 'original_git_binding': ref(A / 'source38.current.json')})
require(read(A / 'source.before_first_case.json') == read(A / 'source.after_AE.json'), 'AE vector drift')
ae = read(A / 'AE.independent_audit.json')
require([x['test_events']['pass'] for x in ae['counts']] == [189, 10, 1, 1, 294], 'AE counts')
require(sum(x['top_events']['pass'] for x in ae['counts']) == 114, 'AE top counts')

case_audits = []
for name, verdict in result['case_results'].items():
    d = N / 'cases' / name
    cr = read(d / 'result.json')
    require(verdict == 'pass' and cr['passed'], 'case verdict ' + name)
    require(all(cr[k] == 0 for k in ('HTTP', 'Node', 'models', 'worker')), 'forbidden execution')
    require(sha(d / 'input.sqlite') == result['original_DB_sha256'], 'fresh original input')
    states = {x: read(d / x) for x in ('00.before-store-open.fullrows.json', '01.after-store-open.fullrows.json', '03.post-attach.fullrows.json', '03b.post-attach-replay.fullrows.json', '05.pre-command.fullrows.json', '07.post-command.fullrows.json', '09.post-replay.fullrows.json', 'closed.fullrows.json')}
    require(states['00.before-store-open.fullrows.json'] == states['01.after-store-open.fullrows.json'], 'Open semantic drift')
    require(states['03.post-attach.fullrows.json'] == states['03b.post-attach-replay.fullrows.json'], 'attach replay drift')
    require(states['07.post-command.fullrows.json'] == states['09.post-replay.fullrows.json'] == states['closed.fullrows.json'], 'configure replay/close drift')
    ar, araw = request(d / '02.actual-attach.request.json')
    rr, rraw = request(d / '03a.exact-attach-replay.request.json')
    require(araw == rraw and ar['writer_epoch'] is None and ar['payload']['after_sequence'] >= 0, 'attach request')
    att, attrep = read(d / '02.actual-attach.json'), read(d / '03a.exact-attach-replay.json')
    require(not att['replay'] and attrep['replay'] and att['response'] == attrep['response'], 'attach original replay')
    require(att['response']['status'] == 'ACKNOWLEDGED', 'attach must remain ACK')
    req, reqraw = request(d / '06.configure.request.json')
    replayreq, replayraw = request(d / '08.replay.request.json')
    require(reqraw == replayraw and req['method'] == 'host.configure', 'configure exact replay raw')
    reply, replay = read(d / '06.configure.json'), read(d / '08.replay.json')
    require(not reply['replay'] and replay['replay'] and reply['response'] == replay['response'], 'configure response replay')
    positive = name.endswith('-positive')
    require(reply['response']['status'] == ('COMPLETED' if positive else 'REJECTED'), 'configure branch')
    pre, post = states['05.pre-command.fullrows.json'], states['07.post-command.fullrows.json']
    if not positive:
        cause = 'session permission remains unresolved' if name.startswith('permission-') else 'earlier session run is not settled'
        require(reply['response']['error_code'] == 'SESSION_BUSY' and reply['response']['error']['message'] == cause, 'precise guard cause')
        require(subseteq(pre, post, ('idempotency', 'client_command_identities')), 'negative business write')
        require(all(len(post[t]) == len(pre[t])+1 for t in ('idempotency', 'client_command_identities')), 'negative original identity counts')
    closed = read(d / 'closed.bytes.json')
    require(sha(d / 'actual.sqlite') == closed['sha256'], 'closed DB hash')
    case_audits.append({'case': name, 'positive': positive, 'verdict': 'PASS', 'actual_result': ref(d / 'result.json'), 'attach_original': ref(d / '02.actual-attach.json'), 'configure_original': ref(d / '06.configure.json'), 'input': ref(d / 'input.sqlite'), 'closed_database': ref(d / 'actual.sqlite'), 'closed_rows': ref(d / 'closed.fullrows.json'), 'schema_and_all_rows_before_after_open_equal': True, 'attach_ACK_exact_replay_all_rows_equal': True, 'configure_exact_replay_all_rows_equal': True, 'after_replay_closed_rows_equal': True, 'negative_business_rows_unchanged': True if not positive else None, 'input_closed_byte_equality_not_assumed': True})

audit_ref = write('C09.independent-final-audit.json', {'schema': 'researchos.handler38.C09-independent-final-audit.v1', 'case_count': 6, 'leaf_pass': 6, 'parent_pass': 1, 'fail': 0, 'skip': 0, 'native_exit': 0, 'outer_driver_exit': 0, 'outer_completion_locator': 'tool:52f9c8/session:16134', 'before': ref(N / 'source.before_first_case.json'), 'after': ref(N / 'source.after_cases.json'), 'input_count': 42966, 'input_drift': False, 'testexe': ref(N / 'domain-c09-corrected.test.exe'), 'physical_overlay': ref(N / 'overlay/handler_configuration_independent_review_test.go'), 'mapping': ref(N / 'overlay/overlay.json'), 'spec': ref(N / 'execution_spec.json'), 'raw': ref(N / 'cases.stdout.raw'), 'invocation': ref(N / 'cases.invocation.json'), 'cases': case_audits, 'interpretation': 'Explicit residual-state and non-head-Run injection isolates direct domain configuration settlement guards. It is not execution of a permission lifecycle, worker, CLI attach completion barrier, or external provider.'})
failure_ref = write('failure_origins.json', {'new_origins': [{'origin': 'tool:c6509c', 'actual_outer_exit': 1, 'kind': 'readonly_locator_error', 'action': 'Get-Content guessed source_review.json in existing static review namespace; actual filename is review.json', 'original_tool_trace_locator': 'conversation/functions.exec/exec_command/chunk:c6509c', 'original_raw_file': None, 'raw_limitation': 'Only original tool trace exists; no byte-exact standalone raw was captured. This JSON is an explicit observation, not reconstructed raw.', 'production_runs': 0, 'SQL': 0, 'case_runs': 0, 'correction': 'rg --files identified review.json; read-only read succeeded; no product rerun.'}], 'historical_C09_failed_invocation_reference_only_do_not_reimport': ref(O / 'failure_origins.json'), 'old_failed_result_preserved': ref(O / 'source_review.json'), 'current_C09_native_failures': 0, 'canonical_write': False})

review = {'schema': 'researchos.handler38.independent-source-review.v1', 'reviewer': 'codex:/root/w05_merge_review', 'decision': 'SOURCE_READY_HANDLER38_WITH_DECLARED_OPEN_PRODUCT_GATES', 'candidate': '22752a6a41732c8c158d7d7e1b8932ec958f8cb8', 'scope': {'exact_source_paths': 38, 'production': 14, 'tests_and_formal_fixture': 24, 'source_current': source_ref, 'static_review': ref(S / 'review.json'), 'whole38_static_map': ref(S / 'whole38_static_map.json'), 'author_evidence_independent_review': ref(E / 'review.json'), 'author_manifest_files_verified_in_prior_review': 3332}, 'basis': ['Whole38 nonauthor static source/diff review remains bound to exact unchanged candidate hashes.', 'Independent A-E current compiled executions and complete before/after closure passed under the registered local fixture scope.', 'Corrected C09 has two legitimate controls and four isolated causal negative controls, exact ACK/replay and full-state witnesses; no manufacturing of COMPLETED attach.', 'Private exact original request bytes/semantic request hash, global command identity, savepoint rejection, typed config/history, API raw replay framing, Host metadata authority, CLI exact numeric and adoption behavior, and backup original-response proof are reviewed and covered by scoped current evidence.'], 'new_confirmed_product_blockers': [], 'A_E_distinct_cohorts': {'audit': ref(A / 'AE.independent_audit.json'), 'manifest': ref(A / 'manifest.json'), 'counts': ae['counts'], 'input_count': 42940, 'aggregate_pass_events': 495, 'aggregate_top_level_pass_events': 114, 'aggregation_limit': 'Arithmetic description of five separate invocations, not one test binary or one formal acceptance.'}, 'C09': {'new_audit': audit_ref, 'new_leaf_pass': 6, 'new_parent_pass': 1, 'old_prerequisite_failed_leaf': 1, 'old_remaining_not_run': 5, 'old_failure_retained': ref(O / 'manifest.json'), 'cohort_limit': 'New six cases use a new physical overlay, new executable, fresh copies and 42966-input closure. The old failed invocation remains failed; A-E was not rerun.'}, 'SDK_and_network_facts': {'D_actual_local_TLS_provider_fixture_requests': 2, 'D_basis': ae['TLS_D_actual_provider_fixture_requests'], 'E_queue_explicit_logged_fixture_calls': 4, 'E_basis': ae['CLI_queue_explicit_logged_fixture_calls'], 'E_other_SDK_or_HTTP_aggregate_count': None, 'aggregate_count_limitation': 'No global SDK/model/HTTP invocation counter exists across the whole CLI cohort. Retain per-test raw and pinned source assertions; do not infer a total.', 'new_C09': {'Node': 0, 'HTTP': 0, 'models': 0, 'worker': 0, 'paid': 0}, 'external_paid_provider_requests': 0, 'qualification': 'Authorized local FIXTURE only; not LIVE/provider/runtime qualification.'}, 'remaining_open': ['C29/F08 original immutable ACK-to-final trigger1811 and finalization gate remain held.', 'C09 proves direct domain guard and ACK replay; does not close separate CLI attach ACK-completion barrier.', 'C18 external/provider LIVE qualification and unanchored legacy execution remain unproved.', 'C19 does not gain dedicated coverage of every possible metadata representation mutation.', 'C30 original formal CLI contract retains 69 successful check IDs and 26 failure entries; full CLI unit/integration green does not relabel that harness.', 'Historical14 ActiveRecovery/Q10, provider history5/held positives, and all parent/A04/W05 formal gates remain unchanged.', 'SourceParent later CLI8/other branches are outside this fixed38 candidate.', 'Main integration/current Main composition is a separate Root action and verification.'], 'formal_increment': 0, 'parent_acceptance': False, 'Main_integration': False, 'failure_origins': failure_ref, 'reviewed_at_utc': datetime.now(timezone.utc).isoformat()}
review_ref = write('source_review.json', review)
entries = []
for p in sorted(N.rglob('*')):
    if p.is_file() and p.name not in ('manifest.json', 'handoff.json'):
        entries.append({'path': p.relative_to(N).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size})
manifest_ref = write('manifest.json', {'schema': 'researchos.public-evidence-manifest.v1', 'namespace': N.relative_to(ROOT).as_posix(), 'entries': entries, 'count': len(entries), 'bytes': sum(x['bytes'] for x in entries), 'excludes': ['manifest.json', 'handoff.json'], 'source_and_old_evidence_mutations': 0})
handoff_ref = write('handoff.json', {'schema': 'researchos.handler38.independent-handoff.v1', 'decision': review['decision'], 'candidate': review['candidate'], 'review': review_ref, 'manifest': manifest_ref, 'case_audit': audit_ref, 'source38': source_ref, 'failure_origins': failure_ref, 'actual_driver_completion': {'tool_chunk': '52f9c8', 'session': 16134, 'actual_exit': 0}, 'A_E': ref(A / 'AE.independent_audit.json'), 'old_C09': ref(O / 'manifest.json'), 'new_C09_cases': 6, 'new_C09_input_count': 42966, 'formal_increment': 0, 'all_evidence_immutable_after_seal': True})
print(json.dumps({'review': review_ref, 'manifest': manifest_ref, 'handoff': handoff_ref, 'failure_origins': failure_ref, 'files': len(entries)}, ensure_ascii=True))
