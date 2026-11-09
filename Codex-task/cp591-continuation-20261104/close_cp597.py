import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
PARENT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104'
RESOURCE = PARENT / 'resource-metadata-supervised-once'
OUT = PARENT / 'checkpoint-cp597'
REVIEWDIR = HERE.parent / 'cp586-continuation/owned-model-resource-supervisor-20261104/reviews/independent-metadata-readback-01'
REVIEW = REVIEWDIR / 'actual-readback-review.json'
REVIEW_SHA = 'f639dba66c00226fad644472f76349eab4bd669045cc7096f35687e0f00deda4'
HEAD = '001f7e5a4d95152c8f83874a60d9fbd3bbace538'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temp = path.with_name(path.name + '.new')
    assert not temp.exists()
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == 596 and len(cp['failure_counters']) == 2432 and cp['current_Main_HEAD'] == HEAD
actual_head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert actual_head == HEAD
assert not OUT.exists(), 'Inspect uncertain closure; do not replay'
assert sha(REVIEW) == REVIEW_SHA
review = json.loads(REVIEW.read_bytes())
assert review['readback_verified'] is True and review['resource_ready'] is False and review['formal_increment'] == 0
assert review['model_inference_qualification'] is False and review['this_scope_replay_allowed'] is False
assert sha(RESOURCE / 'checkpoint.cp594.before-settlement.json') == '744f7be96d8c65bd20d5f7f86390d28d3557c82bf9935149d761aed60256cea0'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path, digest in protected.items():
    assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest
OUT.mkdir()
(OUT / 'checkpoint.cp596.before.json').write_bytes(raw)
archive = RESOURCE / 'reviews/independent-metadata-readback-01'
assert not archive.exists()
archive.mkdir(parents=True)
files = []
for source in REVIEWDIR.iterdir():
    if source.is_file() and source.suffix in ('.json', '.txt', '.py', '.log', '.md'):
        assert source.resolve().is_relative_to(REVIEWDIR.resolve())
        target = archive / source.name
        target.write_bytes(source.read_bytes())
        assert sha(target) == sha(source)
        files.append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target), 'bytes': target.stat().st_size})
assert sha(archive / 'actual-readback-review.json') == REVIEW_SHA
put(OUT / 'independent-readback-archive.json', files)
adoption = {'status': 'INDEPENDENTLY_READ_BACK_METADATA_ONLY_NOT_QUALIFIED', 'readback_verified': True, 'report_ref': str((archive / REVIEW.name).relative_to(ROOT)), 'report_sha256': REVIEW_SHA,
            'resource_ready': False, 'model_inference_qualification': False, 'formal_increment': 0, 'scope_consumed': True, 'this_scope_replay_allowed': False,
            'actual_controller_exit_code': 0, 'owned_processes_stopped': 20, 'owned_processes_active_at_cleanup': 0, 'metadata_gets': {'/api/version': 1, '/api/tags': 1}, 'inference_calls': 0, 'paid_calls': 0}
put(RESOURCE / 'independent-readback-adoption.json', adoption)
now = datetime.now(timezone.utc).isoformat()
old = list(cp['failure_counters'])
key = '20261104|resource-metadata-readback|mutable-resume-harness'
assert key not in {x.get('origin_key') for x in old}
cp['failure_counters'].append({'at': now, 'origin_key': key, 'classification': 'READONLY_DATA_VERIFIER_SCHEMA_ASSUMPTION_FAILURE_NOT_NATIVE_FAILURE', 'attempts': 1, 'counter_reset': False,
    'detail': {'raw_terminal': '493388', 'exit_code': 1, 'cause': 'Verifier expected prelaunch free_bytes_before_scope in the mutable RESUME after normal settlement. No report or native action occurred. Corrected to frozen CP594/auth/consumed chain;64 actual assertions0f95b9 exit0.', 'trace_sha256': 'bdd0290fbd4ae9657049c98360f3db62bc2017cddac6e84dd9b0aca91078a1bd'}})
assert cp['failure_counters'][:2432] == old
cp['resource_metadata_diagnostic_20261104'].update(independent_data_review=adoption)
resume = {'checkpoint_revision': 597, 'status': 'PHASE_RECORDED_SOURCE_INTEGRATED_METADATA_VERIFIED_NOT_PRODUCT_COMPLETE', 'main_head': HEAD, 'failure_records': len(cp['failure_counters']), 'counter_reset': False,
    'formal_accepted': 0, 'formal_required': 42, 'formal_increment': 0,
    'binding': {'commit': 'ebc340ef35cfdbf4449642ed559a05e5cdbaaee6', 'source_files': 4, 'integration_ref': str((PARENT / 'production-binding/integration.json').relative_to(ROOT)), 'limits': 'No registered Host factory/journal/checker or production schema/backup adoption; ordinary LIVE503 unchanged.'},
    'w14': {'commit': HEAD, 'source_files': 9, 'integration_ref': str((PARENT / 'w14-peer-auth-seam/integration.json').relative_to(ROOT)), 'limits': 'Peer/boot-generation and exact-Tx/service/principal credential observation only. No durable proof or writer takeover, new table/wire/lease bypass/ACK change.'},
    'resource': adoption,
    'preserved': {'original_tracked_statuses': 20, 'protected_hash_or_absence_entries': 18, 'registry_revision': 41, 'old_failure_and_UNKNOWN_scopes': True, 'metadata_scope_replay_prohibited': True},
    'next': 'Do not restart the consumed metadata scope. Next implementation needs trusted native client/writer provenance and exact-request attestation with controlled schema/backup lifecycle, then durable attach ACK/replay/full settlement/CAS. Private coding delivery still needs original trusted Host producer/approval journal, separate frozen Goal/Task factories, same-bytes source checker and sealed Goal aggregation before any LIVE503 change. No inference/business or42-case acceptance may be inferred from metadata/source fixtures.',
    'permission_blockers': [], 'remaining_blockers': ['Full W14 durable handoff not implemented', 'Trusted coding delivery/Goal acceptance chain not registered', 'Local model inference/provider qualification not performed', 'Formal LIVE drivers/22 parent gates and42 cases not accepted'],
}
put(OUT / 'RESUME.json', resume)
cp['revision'] = 597
cp['expected_previous_revision'] = 596
cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': resume['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': [], 'formal_increment': 0}
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / 'handoff.cp596.before.md').write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp597.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP597\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Main001f7e5a:4 private-binding +9 peer/auth source files integrated after independent checks. One metadata scope consumed/closed and independently read back:20 owned processes ended,2 GET,0 inference,981 assets unchanged. resource_ready=false; never replay. Full handoff and trusted coding/Goal acceptance remain unimplemented. Formal0/42;22 parent tasks not declared complete; all old failures/UNKNOWN and20 tracked statuses preserved.\n\n').encode() + before)
os.replace(temp, handoff)
(OUT / 'close_cp597.py').write_bytes(Path(__file__).read_bytes())
put(OUT / 'closure-journal.json', {'status': 'CP597_AND_HANDOFF_SAVED', 'main_head': HEAD, 'failure_records': len(cp['failure_counters']), 'readback_report_sha256': REVIEW_SHA, 'formal_increment': 0})
print(json.dumps({'checkpoint': 597, 'head': HEAD, 'failure_records': len(cp['failure_counters']), 'readback_verified': True, 'resource_ready': False, 'formal_increment': 0}))
