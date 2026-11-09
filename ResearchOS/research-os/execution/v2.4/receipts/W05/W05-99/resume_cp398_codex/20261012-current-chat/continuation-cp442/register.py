import copy
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).parent
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def ref(relative):
    path = ROOT / relative
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(raw), 'bytes': len(raw)}
def new_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
def replace(path, old, value):
    assert path.read_bytes() == old
    temporary = path.with_name(path.name + '.cp442.pending')
    with temporary.open('xb') as stream:
        stream.write(value)
    assert path.read_bytes() == old
    os.replace(temporary, path)

cp_path = ROOT / 'execution/v2.4/checkpoint.json'
ow_path = ROOT / 'execution/v2.4/path_ownership.json'
hand_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
state_path = ROOT / 'execution/v2.4/step_state.json'
original = {p: p.read_bytes() for p in [cp_path, ow_path, hand_path, state_path]}
cp = json.loads(original[cp_path].decode('utf-8-sig'))
ow = json.loads(original[ow_path].decode('utf-8-sig'))
assert cp['revision'] == 441 and ow['revision'] == 229 and len(cp['failure_counters']) == 1336
assert shutil.disk_usage('D:/').free > 2 * 1024**3
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == cp['head'] == 'c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0'
assert sha((ROOT / 'execution/project_identity.json').read_bytes()) == '03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert sha((ROOT / '.git/config').read_bytes()) == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
protection = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json').read_text(encoding='utf-8-sig'))
for member in protection['protected_source']:
    raw = (ROOT / member['path']).read_bytes()
    assert sha(raw) == member['sha256'] and len(raw) == member['bytes']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
reports = {
    'mu_v2': ref('execution/v2.4/receipts/W12/W12-02/mu_m0_v2_independent_review_codex/20261012-current-chat/report.json'),
    'mu_v3': ref('execution/v2.4/receipts/W12/W12-02/mu_m0_v3_independent_review_codex/20261012-current-chat/report.json'),
    'observer_v2': ref('execution/v2.4/receipts/W05/W05-99/normal_qualification_observer_v2_review_codex/20261012-current-chat/report.json'),
    'readlane_v1': ref('execution/v2.4/receipts/W05/W05-99/qualification_read_lane_review_codex/20261012-current-chat/report.json'),
    'readlane_v1_correction': ref('execution/v2.4/receipts/W05/W05-99/qualification_read_lane_review_codex/20261012-current-chat/addendum-01.json'),
    'storage_recovery': ref(OUT.relative_to(ROOT).as_posix() + '/storage-recovery-and-mirror.json'),
    'observer_v3': ref('execution/v2.4/receipts/W05/W05-99/normal_qualification_actual_observer_v3_codex/20261012-current-chat/manifest.json'),
}
prior_failures = copy.deepcopy(cp['failure_counters'])
for label in ['mu_v2', 'mu_v3', 'observer_v2', 'readlane_v1']:
    report = json.loads((ROOT / reports[label]['path']).read_text(encoding='utf-8-sig'))
    for finding in report['findings']:
        cp['failure_counters'].append({'origin_key': 'current-chat-20261012|' + label + '|' + finding['id'],
            'attempts': 1, 'status': 'INDEPENDENT_REQUEST_CHANGES_PRESERVED',
            'priority': finding.get('priority'), 'evidence_ref': reports[label],
            'correction_ref': reports['readlane_v1_correction'] if label == 'readlane_v1' else None,
            'counter_reset': False, 'actual_models': 0})
diagnostics = [
    ('root-read-path-2ccce1', 'READONLY_ASSUMED_QUALIFICATION_JS_ABSENT', '2ccce1'),
    ('root-read-path-599479', 'READONLY_RG_ASSUMED_SOURCE_PATH_ABSENT', '599479'),
    ('root-read-glob-af8f42', 'READONLY_POWERSHELL_LITERAL_GLOB_INVALID', 'af8f42'),
    ('root-read-path-f1515c', 'READONLY_RG_ASSUMED_TASK_GO_ABSENT', 'f1515c'),
    ('readlane-D-full', 'AUTHOR_TEE_SINK_DISK_EXHAUSTION_PARTIAL_INVALID_OUTER_EXIT_NOT_PROOF', None),
    ('readlane-v2-renderer-first', 'AUTHOR_REACT_NATIVE_FATAL_EXIT_PRESERVED_UNEXPLAINED_RAW_OVERWRITE_LIMITATION', None),
    ('mu-v3-premature-freeze', 'ROOT_INTERMEDIATE_WIP_SENT_TO_REVIEW_FREEZE_AUDIT_DRIFT_BLOCKED_BEFORE_COMPILE', None),
    ('mu-v3-queue-harness', 'INDEPENDENT_CONTROLLED_FIXTURE_STAGE_ASSUMPTION_FAILED_CORRECTED_SEPARATELY_NOT_SOURCE_FINDING', None),
    ('readlane-v2-cache-cleanup', 'AUTOREVIEW_REMOVE_ITEM_REJECTED_BLOCKED_BY_POLICY_NO_BYPASS', None),
]
for key, status, tool in diagnostics:
    cp['failure_counters'].append({'origin_key': 'current-chat-20261012|' + key,
        'attempts': 1, 'status': status, 'tool_locator': tool,
        'evidence_ref': reports['storage_recovery'], 'counter_reset': False, 'actual_models': 0})
assert cp['failure_counters'][:1336] == prior_failures
pending = [
    {'origin': 'readlane-v1-test-synchronization-and-go-invocation', 'status': 'RAW_PRESERVED_C_AUTHOR_CENSUS_PENDING_EXACT_FAILURE_RECORD_RECONCILIATION'},
    {'origin': 'build-boundary-PS-module-startup', 'status': 'RAW_PRESERVED_FORMAL_BOUNDARY_REPORT_PENDING_REGISTRATION'},
    {'origin': 'mu-v2-full-tsgo-uninstalled-deps', 'status': 'RESOURCE_DIAGNOSTIC_PRESERVED_AUTHOR_C_MANIFEST_TARGETED_TYPES_PASSED'},
    {'origin': 'observer-global-empty-project', 'status': 'READINESS01_PRESERVED_QUERY_CORRECTED02_AND_OBSERVER_V3_REVIEW_PENDING'},
    {'origin': 'mu-v2-generated-output-relocation', 'status': 'AUTHOR_DISCLOSED_MOVE8_GENERATED_OUTPUTS_22743432B_BEFORE_STOP_NO_OLD_CACHE_OR_EVIDENCE_DELETION'},
]
cp.setdefault('pending_original_tool_diagnostic_reconciliation', []).extend(pending)
resume = {'schema': 'researchos.current-chat-resume.v37', 'at': now, 'checkpoint_revision': 442,
    'ownership_revision': 230, 'head': cp['head'], 'project_id': cp['project_id'],
    'current_step_id': 'W05-99', 'goal_status': 'ACTIVE', 'accepted_formal_cases': 0,
    'required_formal_cases': 42, 'required_parent_tasks': 22,
    'failure_records_preserved': len(cp['failure_counters']), 'reports': reports,
    'D_storage': 'USER_CLEANED_SPACE_VERIFIED_RECOVERED', 'D_free_observed': shutil.disk_usage('D:/').free,
    'actual_session_preserved': 'a09d4435036b2b32a0d7076bfc53fd93', 'actual_private_qualification_requests': 0,
    'real_models_this_preparation': 0, 'phone_ready': False,
    'phone_user_answer': 'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY',
    'readlane_v2': 'CONDITIONALLY_SOURCE_APPROVED_C_WIP54OF54_PENDING_FORMAL_MIRROR_COMMIT_ROOT_INTEGRATION_NEW_COMBINED_PACKAGE_NORMAL_UI',
    'mu_v3': 'REJECTED_TWO_P1_PREPARED_MODEL_CONTEXT_AND_TOOL_LOADOUT_LOST_PENDING_SAME9_V4_REPAIR',
    'observer_v3': 'ROOT_CONTROLLED9_DB_CASES_AND3_REAL_GO_JCS_ORACLES_PENDING_INDEPENDENT_REVIEW',
    'source_write_policy': 'D minimal Gitmetadata/small formal manifests now allowed after Root exact scope; generated caches/packages/fullfixtures stayC; no cache-delete bypass',
    'next_command': 'Mirror/freeze approved readlaneV2 source+review, scopedRootintegrate then fresh combinedpackage and same originalSession normalUI qualification1MODEL0TOOL. MuV4 same9 from independently reviewed state contract, uninstalled; observerV3 independent proof before originalCONFIRM. All22/42 remainopen.'}
new_json(OUT / 'RESUME.current.json', resume)
resume_ref = ref(OUT.relative_to(ROOT).as_posix() + '/RESUME.current.json')
cp.update({'revision': 442, 'expected_previous_revision': 441, 'updated_at': now, 'updated_by': 'codex:/root', 'next_command': resume['next_command']})
cp['work_in_progress'].update({'current_chat_continuation_cp442': resume_ref,
    'D_storage_branch': 'RECOVERED_BY_USER_VERIFIED', 'storage_recovery_ref': reports['storage_recovery'],
    'mu_m0_v2_review_ref': reports['mu_v2'], 'mu_m0_v3_review_ref': reports['mu_v3'],
    'mu_m0_current_status': resume['mu_v3'], 'qualification_read_lane_status': resume['readlane_v2'],
    'observer_v3_binding_ref': reports['observer_v3']})
cp['evidence_index'].append({'kind': 'STORAGE_RECOVERY_AND_CURRENT_REVIEW_CONTINUATION', 'ref': resume_ref, 'formal_increment': 0})
cp['blocked_resources'].append({'resource_id': 'CURRENT_CHAT_D_STORAGE', 'status': 'RESOLVED_USER_CLEANUP',
    'blocks_resolved': ['Canon/formal mirror', 'Source Git metadata', 'normal Desktop database storage'], 'evidence': reports['storage_recovery']})
cp['latest_user_instructions'].append({'at': now, 'text': 'Phone: use user realphone after product ready; D storage user cleaned, continue authorized work without renewed approval.'})
ow.update({'revision': 230, 'expected_previous_revision': 229, 'updated_at': now, 'updated_by': 'codex:/root'})
ow['special_paths']['current_chat_storage_recovery'] = {'owner': 'codex:/root', 'ref': reports['storage_recovery'], 'prior_scopes_and_owners_unchanged': True}
for path, name in [(cp_path, 'checkpoint.before.raw.json'), (ow_path, 'ownership.before.raw.json'), (hand_path, 'handoff.before.raw.md')]:
    with (OUT / name).open('xb') as stream:
        stream.write(original[path])
for p, raw in original.items():
    assert p.read_bytes() == raw
replace(ow_path, original[ow_path], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
replace(cp_path, original[cp_path], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
prefix = ('# Current verified continuation CP442\n\nRead `' + resume_ref['path'] + '` first. '
    'D storage recovered by user and verified; C pending records formally mirrored, no reset. '
    'Readlane V2 conditional Source WIP approval54/54 still requires committed exact3/Root integration/fresh package/normal originalSession UI. '
    'Mu V3 rejected2P1; same9 V4 state-contract repair remains uninstalled. ObserverV3 controlled proof pending independent review. '
    'Current MainC381, real qualificationrequests/modelcalls0, phone NOT_READY, formal0/42 all22open.\n\n')
replace(hand_path, original[hand_path], prefix.encode('utf-8') + original[hand_path])
assert state_path.read_bytes() == original[state_path]
print(json.dumps({'checkpoint_revision': 442, 'ownership_revision': 230, 'failure_records_preserved': len(cp['failure_counters']),
    'previous_failure_prefix_unchanged': True, 'resume_ref': resume_ref, 'step_state_unchanged': True,
    'formal': '0/42', 'goal': 'ACTIVE'}))
