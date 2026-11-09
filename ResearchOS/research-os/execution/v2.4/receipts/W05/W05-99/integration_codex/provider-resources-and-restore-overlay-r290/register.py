import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
AUTHOR = ROOT / '.local/worktrees/codex-w0599-provider-binding'
STOP = BASE / 'receipts/W05/W05-99/provider_typed_route_independent_replay_codex/34770766-8c66-46d8-b979-f6f81513b9c1'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(name, value):
    with (OUT / name).open('xb') as f:
        f.write(encoded(value))


def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if expected is not None:
        assert digest == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest, 'bytes': len(body)}


def check(row):
    got = ref(row['path'])
    assert got['sha256'] == row['sha256'] and got['bytes'] == row['bytes'], row['path']


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (289, 117, 254)
assert hashlib.sha256(before[CANON[0]]).hexdigest() == '7fbb91a4e68aebc339b464bbe238c1137bc9752021e445b2ccd94d6c431bba99'
assert hashlib.sha256(before[CANON[1]]).hexdigest() == 'f5c265a00f3be8327dda9720e4ac28b690ae776cfb5a021b98f934a95b0421d6'
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
head = subprocess.check_output(['C:/Program Files/Git/cmd/git.exe', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
request_ref = ref(STOP / 'missing-public-resource-request.json', '828d3d1284160713958719e86d1ce2adefe3d181e7e2a13a67615675e1ed73fc')
supplement_ref = ref(STOP / 'restore-delta-scope-supplement.json', '611b121271d68e5a36e1131c0723c222715b5b5621f159e9949502442a0ba5cb')
failure_ref = ref(STOP / 'failure_origins.json', '95746789b01f751e90f0746564a8b39e666fb6ffed0e81f9d61886c61a2e8ba7')
review_ref = ref(STOP / 'review.json', '4a8a3b6a20a951cc48fb542361476a4a8fb5a68546736c092b1b6e8e8f78ebb6')
manifest_ref = ref(STOP / 'manifest.json', '542235a0f621b7a48d171384a2f38625bb737dbae304fcb63a43bfaad7ca22d8')
for row in json.loads((ROOT / manifest_ref['path']).read_bytes())['files']:
    check(row)
request = json.loads((ROOT / request_ref['path']).read_bytes())
supplement = json.loads((ROOT / supplement_ref['path']).read_bytes())
review = json.loads((ROOT / review_ref['path']).read_bytes())
assert review['controls_executed'] == 0 and review['controls_NOT_RUN'] == 76
assert review['gofmt_actual_exit'] == 0 and review['go_list_actual_exit'] == 1 and review['compiler_invocations'] == 0
assert review['input_count'] == 42502 and not review['input_drift'] and review['models_HTTP_Node_worker_paid_private'] == 0
assert request['candidate'] == '6fb5263681c17f0e50920c354dc07ed440a23714'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=AUTHOR).decode().strip() == request['candidate']
assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=AUTHOR).strip()
assert len(request['resources']) == 3 and len(supplement['exact_changes']) == 8
check(request['source_import'])
resources = []
for item in request['resources']:
    actual = ref(AUTHOR / item['path'], item['sha256'])
    assert actual['bytes'] == item['bytes']
    blob = subprocess.check_output(['git', 'rev-parse', request['candidate'] + ':' + item['path']], cwd=AUTHOR).decode().strip()
    raw = subprocess.check_output(['git', 'show', request['candidate'] + ':' + item['path']], cwd=AUTHOR)
    assert blob == item['git_blob'] and raw == (AUTHOR / item['path']).read_bytes()
    assert not re.search(rb'^\s*func\s+init\s*\(', raw, re.M) and b'//go:embed' not in raw
    destination = Path(request['root']).resolve() / item['path']
    assert destination.is_relative_to(ROOT / '.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c')
    assert not destination.exists(), str(destination)
    resources.append({**copy.deepcopy(item), 'source_ref': actual, 'destination': destination.relative_to(ROOT).as_posix(), 'root_verified_exact_git_bytes': True, 'root_verified_no_init_or_embed': True})
for row in supplement['actual_source_reads'].values():
    check(row)
check(supplement['existing_overlay'])
origins = json.loads((ROOT / failure_ref['path']).read_bytes())['origins']
assert len(origins) == 1
origin = origins[0]
check(origin['invocation'])
check(origin['result'])
result = json.loads((ROOT / ref(origin['result']['path'])['path']).read_bytes())
assert result['exit'] == origin['actual_exit'] == origin['driver_outer_exit'] == 1
check(result['stdout'])
check(result['stderr'])
assert origin['product_case_failures'] == 0 and origin['count_once']
assert 'researchos.local/research-os/ops/experiment_sandbox' in (ROOT / ref(result['stderr']['path'])['path']).read_text(encoding='utf-8')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
amendment = {
    'schema': 'researchos.root.independent-provider-compile-resource-and-restore-delta-amendment.v1',
    'actor': 'codex:/root', 'executor': 'codex:/root/w05_merge_review', 'at': now,
    'original_scope_ref': cp['work_in_progress']['provider_typed_route_independent_execution_scope_ref'],
    'previous_prepare_amendment_ref': cp['work_in_progress']['provider_independent_overlay_prepare_amendment_ref'],
    'stopped_review_ref': review_ref, 'stopped_manifest_ref': manifest_ref, 'failure_origin_ref': failure_ref,
    'resource_request_ref': request_ref, 'exact_public_compile_exports': resources,
    'implementation_authorized': True, 'production_source_writes': 0, 'SQL_product_changes': 0,
    'resource_export_authority': 'Export exactly these three immutable candidate Git blobs to the previously registered isolated checkout only. Do not export tests/cmd/evidence/datasets/holdouts or execute sandbox functions. Existing original nine product files remain immutable.',
    'overlay_supplement_ref': supplement_ref, 'original_overlay_ref': supplement['existing_overlay'],
    'exact_producer_bound_changes': copy.deepcopy(supplement['exact_changes']),
    'root_static_source_observations': [
        'Root independently read backupFence216-278, store.event368-408 and bump158-168, effectAppend17-25, backupPrepareWorkspaces334-383, backupActivateWorkspaces395-429 and putOpaque490-512. Reads were native tools b076af, d176b9 and4f565d actualexit0. Exact frozen source hashes checked above; no restore SQL or cases were executed by Root.',
        'All preexisting full typed SQL rows remain unchanged except exact producer replacements. Restore Run/ProjectState/EventEnvelope and causal version/ref/outbox/snapshot appends must be bijective to actual original active Runs, not a kind allowlist. Per-project ordering is by actual resulting event sequence; do not assume query iteration or random new IDs.',
        'Project workspace remapping is putOpaque: real_path and revision only, updated_at remains exact. WorkspaceBinding is putOpaque twice with original metadata and exact callback path/pin. No invented domain_versions or refs for opaque rows.',
        'For timestamps use actual restore invocation interval, not a guessed generation timestamp. Every new immutable object hash and SQL content_hash must use its actual existing producer formula and persisted body. Keep raw typed and parsed-semantic evidence distinct.',
        'Source/route/profile/request/budget ledger and historical producer refs unchanged. Resource-effect append is UNKNOWN at original tuple with exact sequence and reason; do not infer actual dispatch/settlement/requalification.',
        'Original internal64 controls still first with R01/R02/R03 first. Public6 positives then6 refusal cases remain the same registered76 total; workspace witness remains explicitly SYNTHETIC_NOT_PRODUCT, one31-byte supplied file, no old path read.'
    ],
    'write_scope': 'New independent review-owned immutable overlay/driver/spec/receipt namespace and isolated cache. Preserve both prior overlays, raw results and exported source. Test checks may change only as enumerated by the actual producer-bound restore supplement; no unrelated expectation weakening.',
    'next_sequence': 'Verify/export exact3 -> new overlay/spec/driver -> actual gofmt -> actual go-list -> complete current source/compiler/tool/SDK/7 original DB closure -> actual compile -> executable closure -> same76 controls. First unexpected stops every dependent control. No model/HTTP/Node/worker/private/paid/generator call.',
    'preregistered_progress': ['gofmt0 previously achieved and retained', 'new exact3 exports unblock actual go-list closure', 'actual compile0 and new executable before any case'],
    'same_control_budget': 76, 'previous_controls_executed': 0,
    'preparation_failure_origins': 2, 'old_model_history_failures': 5, 'old_P1_failures': 3,
    'automatic_retries': False, 'failure_reset': False,
    'source_acceptance': False, 'formal_increment': 0,
    'models_HTTP_Node_worker_paid_private_calls': 0
}
save('scope_amendment.json', amendment)
amendment_ref = ref(OUT / 'scope_amendment.json')
old = copy.deepcopy(cp['failure_counters'])
key = 'W05-99/independent-provider-precompile/' + origin['origin_id']
assert key not in {r.get('origin_key') for r in old}
cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'retries_used': 0,
    'status': 'ACTUAL_INDEPENDENT_GO_LIST_EXIT1_OUTER1_SINGLE_RESOURCE_OMISSION_NO_CASE',
    'evidence_ref': failure_ref, 'detail': origin, 'count_once': True,
    'product_test_failure': False, 'counter_reset': False, 'formal_increment': 0})
assert cp['failure_counters'][:254] == old and len(cp['failure_counters']) == 255
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
lease = ow['card_path_bindings']['W05-99']['subtasks']['provider_typed_route_independent_replay']
assert lease['owner'] == 'codex:/root/w05_merge_review' and lease['maximum_controls'] == 76
lease.update(state='EXACT3_PUBLIC_COMPILE_EXPORT_AND_PRODUCER_BOUND_RESTORE_OVERLAY_AMENDMENT_AUTHORIZED_CONTROLS0_OF76',
    resources_restore_overlay_amendment_ref=amendment_ref, stopped_review_ref=review_ref, preparation_failures=2)
cp['work_in_progress'].update(provider_independent_resources_restore_overlay_amendment_ref=amendment_ref,
    provider_independent_stopped_review_ref=review_ref,
    next_action='Execute authorized nonself same76 after exact3 public dependencies and producer-bound new restore overlay; handler same27 pending proof continues. F08 proposal readonly; no source or formal acceptance and no held retries.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'EXACT3_PUBLIC_PROVIDER_COMPILER_ASSETS_AND_PRODUCER_BOUND_RESTORE_OVERLAY_CAS',
    'amendment_ref': amendment_ref, 'failure_origins_before': 254, 'failure_origins_after': 255, 'formal_increment': 0})
cp.update(revision=290, expected_previous_revision=289, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=118, amended_at=now, amended_by='codex:/root')
for row in [amendment_ref, request_ref, supplement_ref, failure_ref, review_ref, manifest_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [289, 290], 'ownership': [117, 118], 'failure_origins': [254, 255],
    'public_compiler_exports': 3, 'producer_bound_overlay_changes': 8, 'cases_executed': 0, 'formal_increment': 0})
assert all(p.read_bytes() == body for p, body in before.items())
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root290.tmp')
    with temp.open('xb') as f:
        f.write(encoded(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 290, 'ownership': 118, 'failure_origins': 255, 'scope_amendment_ref': amendment_ref,
    'source_changes': 0, 'controls_run': 0, 'formal_increment': 0}, ensure_ascii=True))
