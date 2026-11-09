import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp586-continuation')
SUP = BASE / 'owned-model-resource-supervisor-20261104/attempt-01'
RUN = BASE / 'owned-model-resource-stage-b/revision-04/run-01'
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/resource-metadata-supervised-once'


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
assert cp['revision'] == 594 and len(cp['failure_counters']) == 2425
assert sha(cpfile) == '744f7be96d8c65bd20d5f7f86390d28d3557c82bf9935149d761aed60256cea0'
assert not (OUT / 'settlement-journal.json').exists(), 'Inspect uncertain outcome; no replay'
s = json.loads((SUP / 'SUPERVISOR-RESULT.json').read_bytes())
r = json.loads((RUN / 'RESULT.json').read_bytes())
assert s['status'] == 'REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED'
assert s['controller_exit_code'] == 0 and s['termination_confirmed'] is True
assert s['reported_proof_complete'] is True and s['automatic_retry'] is False and s['resource_ready'] is False
assert s['root_scope_sha256'] == sha(OUT / 'root-authorization.json')
assert s['checkpoint_sha256'] == sha(cpfile)
assert r['status'] == 'METADATA_VERIFIED_OWNED_JOB_CLOSED_ASSETS_UNCHANGED'
assert r['cleanup_proved'] is True and r['streams_drained'] is True and r['stage_a_assets_unchanged_after_stop'] is True
assert r['metadata_get_attempts'] == {'/api/version': 1, '/api/tags': 1}
for name in ('controller_inference_requests', 'paid_provider_requests', 'old_root_writes', 'formal_increment'):
    assert type(r[name]) is int and r[name] == 0
assert r['counter_reset'] is False and r['resource_ready'] is False and not r.get('error')
k = r['kernel']
state = k['State']
assert k['CleanupProved'] is True and not k['Error']
assert k['Close']['JobClosed'] is True and k['Close']['PrimarySignaled'] is True and not k['Close']['Errors']
assert state['Active'] == 0 and state['Complete'] is True and state['PrimarySignaled'] is True and not state['Errors']
assert state['Total'] == len(state['Processes']) == 20
assert len({p['pid'] for p in state['Processes']}) == 20
for process in state['Processes']:
    assert all(process[name] is True for name in ('handle_held', 'in_owned_job', 'new_process_event', 'signaled_after_cleanup'))
    assert process['creation_filetime_decimal'].isascii() and int(process['creation_filetime_decimal']) > 0
primary = next(p for p in state['Processes'] if p['pid'] == k['Primary']['pid'])
assert primary['creation_filetime_decimal'] == k['Primary']['creation_filetime_decimal']
version = json.loads((RUN / 'version.response.json').read_bytes())
tags = json.loads((RUN / 'tags.response.json').read_bytes())
assert len(tags['models']) == 1 and tags['models'][0]['name'] == 'qwen3:4b-instruct'
assert tags['models'][0]['digest'] == '0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'
assert tags['models'][0]['size'] == 2497293803
(OUT / 'checkpoint.cp594.before-settlement.json').write_bytes(raw)
target = OUT / 'actual-evidence'
assert not target.exists()
target.mkdir()
manifest = []
for parent, names, namespace in (
    (SUP, ['CONSUMED.json', 'SUPERVISOR-RESULT.json'], 'supervisor'),
    (RUN, ['RESULT.json', 'ENV-KEYS.json', 'SUSPENDED-OWNED-IDENTITY.json', 'version.response.json', 'tags.response.json', 'stdout.raw', 'stderr.raw'], 'controller'),
):
    for name in names:
        source = parent / name
        dest = target / namespace / name
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(source.read_bytes())
        assert sha(dest) == sha(source)
        manifest.append({'path': str(dest.relative_to(OUT)), 'sha256': sha(dest), 'bytes': dest.stat().st_size})
put(OUT / 'actual-evidence-manifest.json', manifest)
now = datetime.now(timezone.utc).isoformat()
summary = {'status': 'EXECUTION_REPORTED_METADATA_VERIFIED_STOPPED_NOT_QUALIFIED', 'at': now,
    'scope_consumed': True, 'automatic_retry': False, 'controller_exit_code': 0,
    'version': version, 'model_name': tags['models'][0]['name'], 'model_manifest_sha256': tags['models'][0]['digest'],
    'metadata_gets': r['metadata_get_attempts'], 'owned_processes_observed': 20, 'owned_processes_active_at_cleanup': 0,
    'job_closed': True, 'all_held_processes_signaled': True, 'streams_drained': True, 'asset_files_verified_before_and_after': 981,
    'asset_contents_unchanged': True, 'inference_calls': 0, 'paid_calls': 0, 'old_root_writes': 0,
    'resource_ready': False, 'business_or_inference_qualified': False, 'formal_increment': 0,
    'independent_data_review': 'PENDING_READBACK_REPORT', 'evidence_ref': str((OUT / 'actual-evidence-manifest.json').relative_to(ROOT)),
    'tools': {'execution': 'd1e4ff/5ab52c actual exit0', 'Root_readback': 'c70b5d'},
    'limits': 'Real private copied-server metadata only. No inference, task completion, provider qualification, W14 handoff or formal acceptance. New profile private keys were not read or archived.'}
put(OUT / 'execution-summary.json', summary)
put(OUT / 'settlement-journal.json', {'status': 'ACTUAL_EVIDENCE_ARCHIVED_BEFORE_CHECKPOINT', 'controller_exit_code': 0, 'formal_increment': 0})
cp['revision'] = 595
cp['expected_previous_revision'] = 594
cp['updated_at'] = now
for effect in cp['side_effects_pending']:
    if isinstance(effect, dict) and effect.get('origin_key') == 'OWNED_COPY_MODEL_METADATA_ONCE_20261104':
        effect.update(state='EXECUTED_SETTLED_METADATA_ONLY_NO_QUALIFICATION', result_ref=str((OUT / 'execution-summary.json').relative_to(ROOT)), automatic_retry=False)
cp['resource_metadata_diagnostic_20261104'] = summary
resume = dict(summary, checkpoint_revision=595, main_head=cp['current_Main_HEAD'], failure_records=len(cp['failure_counters']), counter_reset=False, formal_accepted=0, formal_required=42,
    next='Read independent actual-data review, then integrate approved exact9 W14 prerequisite source. Do not restart this consumed supervisor/server scope. Trusted Host factory/journal/source checker/Goal aggregation and full W14 durable handoff remain future work.')
put(OUT / 'RESUME.json', resume)
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': summary['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': [], 'formal_increment': 0}
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / 'handoff.cp594.before.md').write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp595.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP595\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. One private copied-server metadata run actually exited0: two GETs, zero inference/paid,20 owned processes stopped/Job closed,981 assets unchanged. Scope consumed; never replay. Metadata only, not resource/inference/business qualification. W14 exact9 source awaits Root integration after independent approval. Formal0/42, historical counters unchanged.\n\n').encode() + before)
os.replace(temp, handoff)
(OUT / 'tools/settle_metadata.py').write_bytes(Path(__file__).read_bytes())
put(OUT / 'settlement-journal.json', {'status': 'CP595_AND_HANDOFF_SAVED_METADATA_ONLY', 'main_head': cp['current_Main_HEAD'], 'controller_exit_code': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 595, 'head': cp['current_Main_HEAD'], 'failure_records': len(cp['failure_counters']), 'owned_processes_stopped': 20, 'inference': 0, 'resource_ready': False, 'formal_increment': 0}))
