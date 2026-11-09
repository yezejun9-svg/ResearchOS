import copy
import datetime
import hashlib
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def ref(path):
    path = pathlib.Path(path)
    if not path.is_absolute():
        path = ROOT / path
    data = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(data), 'bytes': len(data)}

def write_new(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with pathlib.Path(path).open('xb') as stream:
        stream.write(data)

def cas_replace(path, original, data):
    assert path.read_bytes() == original, f'CAS drift: {path}'
    temporary = path.with_name(path.name + '.cp441.pending')
    with temporary.open('xb') as stream:
        stream.write(data)
    assert path.read_bytes() == original, f'CAS drift before replace: {path}'
    os.replace(temporary, path)

cp_path = ROOT / 'execution/v2.4/checkpoint.json'
ow_path = ROOT / 'execution/v2.4/path_ownership.json'
handoff_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
state_path = ROOT / 'execution/v2.4/step_state.json'
before = {p: p.read_bytes() for p in [cp_path, ow_path, handoff_path, state_path]}
cp = json.loads(before[cp_path].decode('utf-8-sig'))
ow = json.loads(before[ow_path].decode('utf-8-sig'))
assert cp['revision'] == 440 and ow['revision'] == 228
assert len(cp['failure_counters']) == 1334
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == cp['head'] == 'c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0'
assert digest((ROOT / 'execution/project_identity.json').read_bytes()) == '03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert digest((ROOT / '.git/config').read_bytes()) == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
source_root = pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
source_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_root, text=True).strip()
source_index_changes = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=source_root, text=True).strip()
assert not source_index_changes
assert (source_root / 'AGENTS.md').is_file()
scaffold_ref = ref('execution/v2.4/receipts/W05/W05-99/qualification_read_lane_repair_codex/20261012-current-chat/scaffold-observation-01.json')
assert scaffold_ref['sha256'] == '307023d3003b77f1642b822cd30fc94db70a48501ab6edf45a3656ec506ccf70'
scaffold = json.loads((ROOT / scaffold_ref['path']).read_text(encoding='utf-8-sig'))
for member in scaffold['backup']:
    raw = pathlib.Path(member['path']).read_bytes()
    assert len(raw) == member['bytes'] and digest(raw) == member['sha256']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
observation = {
    'schema': 'researchos.current-chat-scaffold-correction/1', 'at': now,
    'source_root': str(source_root), 'source_head_at_observation': source_head,
    'source_index_change_count': 0, 'source_agents_file_present': True,
    'initial_fault': 'Root --no-checkout plus sparse patterns did not materialize index or source files',
    'correction': 'Source agent preserved exact WIP backups, then git read-tree -mu HEAD succeeded in original registered worktree; later line-ending normalization explicitly documented',
    'post_command_observation_ref': scaffold_ref,
    'correction_original_tool_chunk': '230ea8',
    'root_readonly_index_check_tool_chunk': 'c974e8',
    'new_root_read_diagnostics': [
        {'tool_chunk': '54d00e', 'exit_code': 1, 'path': 'continuation-cp440/register.py', 'reason': 'Root assumed writer file existed; no mutation'},
        {'tool_chunk': '576efc', 'exit_code': 1, 'path': 'continuation-cp439/register.py', 'reason': 'Root assumed writer file existed; no mutation'},
    ],
    'actual_model_calls': 0, 'actual_tool_dispatches': 0,
    'formal_increment': 0, 'source_authority_unchanged': True,
}
write_new(OUT / 'scaffold-correction.json', observation)
observation_ref = ref(OUT / 'scaffold-correction.json')
old_failures = copy.deepcopy(cp['failure_counters'])
cp['failure_counters'].extend([
    {'origin_key': 'current-chat-20261012|read-lane-scaffold-not-materialized', 'attempts': 1,
     'status': 'ROOT_SCAFFOLD_DIAGNOSTIC_CORRECTED_WIP_PRESERVED_SAME_SOURCE_SCOPE',
     'evidence_ref': observation_ref, 'counter_reset': False, 'actual_models': 0},
    {'origin_key': 'current-chat-20261012|root-assumed-checkpoint-writer-paths', 'attempts': 2,
     'status': 'READONLY_PATH_DISCOVERY_DIAGNOSTICS_NO_CANON_OR_SOURCE_MUTATION',
     'tool_locators': ['54d00e', '576efc'], 'evidence_ref': observation_ref, 'counter_reset': False, 'actual_models': 0},
])
assert cp['failure_counters'][:len(old_failures)] == old_failures
old_resume = ROOT / cp['work_in_progress']['current_chat_continuation_cp440']['path']
resume = json.loads(old_resume.read_text(encoding='utf-8-sig'))
resume.update({'at': now, 'checkpoint_revision': 441, 'ownership_revision': 229,
    'failure_records_preserved': len(cp['failure_counters']), 'scaffold_correction_ref': observation_ref,
    'phone_user_answer': 'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY',
    'phone_ready': False, 'qualification_read_lane_status': 'EXACT3_SOURCE_TESTS_AND_BOUND_BUILD_IN_PROGRESS_SAME_REGISTERED_WORKTREE'})
write_new(OUT / 'RESUME.current.json', resume)
resume_ref = ref(OUT / 'RESUME.current.json')
cp.update({'revision': 441, 'expected_previous_revision': 440, 'updated_at': now, 'updated_by': 'codex:/root'})
cp['work_in_progress']['current_chat_continuation_cp441'] = resume_ref
cp['work_in_progress']['qualification_read_lane_scaffold_correction_ref'] = observation_ref
cp['work_in_progress']['qualification_read_lane_status'] = resume['qualification_read_lane_status']
cp['work_in_progress']['phone_user_preference'] = {'answer': resume['phone_user_answer'], 'ready': False, 'no_reprompt_required': True}
cp['evidence_index'].append({'kind': 'CURRENT_CHAT_SCAFFOLD_CORRECTION_AND_RESUME', 'ref': resume_ref, 'formal_increment': 0})
ow.update({'revision': 229, 'expected_previous_revision': 228, 'updated_at': now, 'updated_by': 'codex:/root'})
ow['special_paths']['qualification_read_lane_scaffold_correction'] = {'owner': 'codex:/root', 'ref': observation_ref, 'source_scope_unchanged': True}
for path, name in [(cp_path, 'checkpoint.before.raw.json'), (ow_path, 'ownership.before.raw.json'), (handoff_path, 'handoff.before.raw.md')]:
    with (OUT / name).open('xb') as stream:
        stream.write(before[path])
prefix = ('# Current verified continuation CP441\n\nRead `' + resume_ref['path'] + '` first. '
    'Original Session/data retained; formal 0/42, all 22 current obligations open. '
    'Read-lane exact3 Source and bound build underway; original registered worktree materialized with WIP backups retained. '
    'Mu M0 V2 remains isolated exact9 repair. Phone user preference fixed: real user phone only when full pairing/supervision is ready. '
    'All 1334 prior failure records preserved, two diagnostic records appended; no model/tool dispatch this continuation.\n\n')
for p in [cp_path, ow_path, handoff_path, state_path]:
    assert p.read_bytes() == before[p], f'Pre-write CAS drift: {p}'
cas_replace(ow_path, before[ow_path], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
cas_replace(cp_path, before[cp_path], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
cas_replace(handoff_path, before[handoff_path], prefix.encode('utf-8') + before[handoff_path])
assert state_path.read_bytes() == before[state_path]
assert cp['failure_counters'][:1334] == old_failures
print(json.dumps({'checkpoint_revision': 441, 'ownership_revision': 229, 'failure_records_preserved': len(cp['failure_counters']),
    'head': head, 'resume_ref': resume_ref, 'step_state_unchanged': True, 'goal_status': 'ACTIVE', 'formal': '0/42'}))
