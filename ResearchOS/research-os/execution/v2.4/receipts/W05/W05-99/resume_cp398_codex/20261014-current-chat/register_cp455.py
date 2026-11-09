"""Root-only continuation registration; no product-state or acceptance writes."""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).parent
OUT = HERE / 'continuation-cp455'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(), 'sha256': sha(raw), 'bytes': len(raw)}

def new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def replace(path, before, after):
    assert path.read_bytes() == before
    temp = path.with_name(path.name + '.cp455.pending')
    with temp.open('xb') as f:
        f.write(after)
    assert path.read_bytes() == before
    os.replace(temp, path)

def mirror(source, target, manifest_name, expected):
    manifest = source / manifest_name
    assert sha(manifest.read_bytes()) == expected
    value = read(manifest)
    members = []
    for entry in value['files']:
        p = Path(entry['path'])
        p = p if p.is_absolute() else source / p
        raw = p.read_bytes()
        assert len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], str(p)
        members.append(p)
    members += [manifest]
    for name in ['report.json', 'report.md', 'FINAL-report.json']:
        if (source / name).is_file():
            members.append(source / name)
    target.mkdir(parents=True, exist_ok=False)
    index = []
    for p in sorted(set(members)):
        item = ref(p)
        if p.stat().st_size <= 2 * 1024 * 1024:
            dest = target / p.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            assert dest.read_bytes() == p.read_bytes()
            item['mirror'] = ref(dest)
        else:
            item['disposition'] = 'ORIGINAL_C_EVIDENCE_RETAINED'
        index.append(item)
    new(target / 'root-mirror-index.json', {'members': index, 'formal_increment': 0})

cp_path = ROOT / 'execution/v2.4/checkpoint.json'
ow_path = ROOT / 'execution/v2.4/path_ownership.json'
hand_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
state_path = ROOT / 'execution/v2.4/step_state.json'
original = {p: p.read_bytes() for p in [cp_path, ow_path, hand_path, state_path]}
cp, ow = read(cp_path), read(ow_path)
assert cp['revision'] == 454 and ow['revision'] == 242
assert len(cp['failure_counters']) == 1382
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == cp['head'] == 'c465d1356480d6e6a90da84656724f9fc02b31c7'
assert sha((ROOT / '.git/config').read_bytes()) == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert sha((ROOT / 'execution/project_identity.json').read_bytes()) == '03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
for item in read(ROOT / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(ROOT / item['path'])['sha256'] == item['sha256']
assert sha(original[state_path]) == '168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e'
mu_source = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v6-independent-review-20261014')
mu_mirror = ROOT / 'execution/v2.4/receipts/W12/W12-02/mu_m0_v6_independent_review_codex/20261014-current-chat'
live_source = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/original-model-qualification-review-20261014')
live_mirror = ROOT / 'execution/v2.4/receipts/W05/W05-99/original_model_qualification_review_codex/20261014-current-chat'
assert read(mu_source / 'report.json')['verdict'] == 'SOURCE_FIXTURE_ACCEPTED'
assert sha((live_source / 'FINAL-report.json').read_bytes()) == 'dfe4ade015ad1f0ad81885d960e1a0f28e904cac445dcb83e2d1da52d00e7ae8'
OUT.mkdir(exist_ok=False)
mirror(mu_source, mu_mirror, 'manifest.json', '718c5049e251dfcaa4dd10ba286bd7494d9ba5758ef28085bbbdae6589349085')
mirror(live_source, live_mirror, 'FINAL-manifest.json', '8f2467d657dd27cfb6acac5327f3355428f81f734498cb94501d16e841a8fb25')
receipt = ROOT / 'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry07_codex/20261014-current-chat'
diagnostics = [
    ('root-native-edit-aee85a', 'Cross-process GetWindowText Edit validation failed before native button click; WM_GETTEXT then verified same selected path', '07-toolchain-dialog-selection.json'),
    ('root-node-cell64', 'getByLabel timed out and Node kernel reset; fields subsequently filled using observed textbox/spinbutton roles', '09-coding-intent.ui.txt'),
    ('root-node-page-aria', 'Page.ariaSnapshot unavailable; corrected to locator body ariaSnapshot without product mutation', None),
    ('root-missing-register-cp454', 'Attempted read of nonexistent register_cp454.py; existing registration pattern then read', None),
    ('coding-prepare-session-changed', 'Prepare clicked before asynchronous writer acquisition finished; SESSION_CHANGED; no configuration installed', '12-coding-prepared-result.ui.txt'),
    ('coding-prepare-selection-required', 'Writer context change invalidated old native Go selection; GO_TOOLCHAIN_SELECTION_REQUIRED; reselected through ordinary native controls', '13-coding-prepared-final.ui.txt'),
    ('coding-prepare-original-pending', 'After native selection, QUALIFICATION_ORIGINAL_REQUEST_PENDING; completed original request STATUS reports CONTEXT_CHANGED; read-only diagnosis underway', '14-coding-prepared.ui.txt'),
]
prior = copy.deepcopy(cp['failure_counters'])
for key, detail, evidence in diagnostics:
    origin = '20261014|' + key
    assert not any(x.get('origin_key') == origin for x in prior)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'DIAGNOSTIC_PRESERVED', 'detail': detail, 'counter_reset': False, 'actual_models': 0, 'evidence_ref': ref(receipt / evidence) if evidence else None})
assert cp['failure_counters'][:len(prior)] == prior
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
resume = {'schema': 'researchos.current-chat-resume.v38', 'at': now, 'checkpoint_revision': 455, 'ownership_revision': 242, 'head': cp['head'], 'project_id': cp['project_id'], 'current_step_id': 'W05-99', 'goal_status': 'ACTIVE', 'accepted_formal_cases': 0, 'required_formal_cases': 42, 'required_parent_tasks': 22, 'failure_records_preserved': len(cp['failure_counters']), 'no_progress_rounds': cp['no_progress_rounds'], 'mu_v6_review_ref': ref(mu_mirror / 'report.json'), 'mu_v6_status': 'SOURCE_FIXTURE_ACCEPTED_NOT_INSTALLED_PRODUCTION_UNACCEPTED', 'original_qualification_review_ref': ref(live_mirror / 'FINAL-report.json'), 'original_qualification': '1 MODEL / 0 TOOL; SETTLED; product PASS; UNKNOWN/null; consumed request STATUS only', 'coding_config': 'PREPARE blocked after writer context change; inputs and native choices retained, no config install', 'phone_ready': False, 'next_command': 'Diagnose and repair only actual coding qualification context lifecycle if normal UI cannot recover; preserve current Desktop/session and original consumed request. Prepare bounded M1 scope from accepted M0 source without installing yet.'}
new(OUT / 'RESUME.current.json', resume)
resume_ref = ref(OUT / 'RESUME.current.json')
cp.update({'revision': 455, 'expected_previous_revision': 454, 'updated_at': now, 'updated_by': 'codex:/root', 'next_command': resume['next_command']})
cp['work_in_progress'].update({'current_chat_continuation_cp455': resume_ref, 'mu_m0_current_status': resume['mu_v6_status'], 'mu_m0_v6_review_ref': resume['mu_v6_review_ref'], 'original_model_qualification_review_ref': resume['original_qualification_review_ref'], 'coding_current_gui_status': resume['coding_config']})
cp['evidence_index'].append({'kind': 'LIVE_MODEL_AND_M0_SOURCE_INDEPENDENT_REVIEW_CODING_CONTEXT_DIAGNOSIS', 'ref': resume_ref, 'formal_increment': 0})
for path, name in [(cp_path, 'checkpoint.before.raw.json'), (ow_path, 'ownership.before.raw.json'), (hand_path, 'handoff.before.raw.md')]:
    (OUT / name).write_bytes(original[path])
for p, raw in original.items():
    assert p.read_bytes() == raw
replace(cp_path, original[cp_path], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode('utf8'))
prefix = '# Current verified continuation CP455\n\nRead `' + resume_ref['path'] + '` first. Original actual model qualification independently reviewed (1 MODEL/0 TOOL); Mu V6 M0 source/fixture accepted only, uninstalled. Coding PREPARE context lifecycle diagnosis ongoing. Formal0/42, all22 open, phone not ready.\n\n'
replace(hand_path, original[hand_path], prefix.encode('utf8') + original[hand_path])
assert ow_path.read_bytes() == original[ow_path] and state_path.read_bytes() == original[state_path]
print(json.dumps({'checkpoint': 455, 'ownership': 242, 'failures': len(cp['failure_counters']), 'resume': resume_ref}))
