"""Register the resumed independent review and its bounded repair without changing acceptance."""
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
OUT = HERE / 'continuation-cp450'
REVIEW = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m0-v5-independent-review-20261013')
MIRROR = ROOT / 'execution/v2.4/receipts/W12/W12-02/mu_m0_v5_independent_review_codex/20261014-current-chat'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def reference(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(), 'sha256': digest(raw), 'bytes': len(raw)}

def new_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def replace(path, before, after):
    assert path.read_bytes() == before, str(path)
    pending = path.with_name(path.name + '.cp450.pending')
    with pending.open('xb') as stream:
        stream.write(after)
    assert path.read_bytes() == before
    os.replace(pending, path)

def main():
    cp_path = ROOT / 'execution/v2.4/checkpoint.json'
    ow_path = ROOT / 'execution/v2.4/path_ownership.json'
    hand_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
    state_path = ROOT / 'execution/v2.4/step_state.json'
    originals = {p: p.read_bytes() for p in [cp_path, ow_path, hand_path, state_path]}
    cp, ow = read(cp_path), read(ow_path)
    assert cp['revision'] == 449 and ow['revision'] == 237
    assert len(cp['failure_counters']) == 1371
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == cp['head'] == '91218bdd3901bae94a2c1c90521a4d133c59026d'
    assert digest((ROOT / '.git/config').read_bytes()) == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
    assert digest((ROOT / 'execution/project_identity.json').read_bytes()) == '03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
    protection = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')
    for member in protection['protected_source']:
        raw = (ROOT / member['path']).read_bytes()
        assert digest(raw) == member['sha256'] and len(raw) == member['bytes']
    report = read(REVIEW / 'report.json')
    assert 'REQUEST_CHANGES' in json.dumps(report)
    assert (REVIEW / 'manifest.json').is_file()
    assert report.get('findings'), 'FINAL findings required'
    OUT.mkdir(exist_ok=False)
    MIRROR.mkdir(parents=True, exist_ok=False)
    members = []
    for source in sorted(REVIEW.rglob('*')):
        if not source.is_file():
            continue
        info = reference(source)
        rel = source.relative_to(REVIEW)
        if source.stat().st_size <= 2 * 1024 * 1024 and 'vite-cache' not in rel.parts:
            target = MIRROR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            assert target.read_bytes() == source.read_bytes()
            info['mirror'] = reference(target)
        else:
            info['disposition'] = 'ORIGINAL_C_EVIDENCE_RETAINED'
        members.append(info)
    new_json(MIRROR / 'root-mirror-index.json', {'members': members, 'formal_increment': 0})
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    old_scope_path = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp445/mu-m0-v5-source-scope.json'
    scope = read(old_scope_path)
    scope.update({'at': now, 'owner': 'codex:/root/mu_m0_v6_repair', 'model': 'gpt-6-astra', 'model_choice_reason': 'Security DTO validation and multi-phase restore lifecycle require architecture reasoning', 'phase': 'M0_V6_SAME9_NOT_INSTALLED', 'previous_scope_ref': reference(old_scope_path), 'rejected_candidate_review_ref': reference(MIRROR / 'report.json'), 'state_contract_ref': reference(MIRROR / 'state-contract-v5-addendum.md'), 'source_owner_unchanged': False, 'amendment_reason': 'V5 independent typed discriminant/inherited schema key rejection and phase-scoped restoration binding', 'required_repairs': ['Strict typed enum/discriminant validation without coercion on export, restore and all message paths; reject unknown fields', 'Closed custom schemas and required/optional keys use explicit own-property semantics', 'Preserve original checkpoint phase bindings and effects exactly once, then permit trusted registered model/tool selections for subsequent phases with per-dispatch drift checks', 'Strengthen full completion regressions: expected final response/model call count/no error/queue consumption once; preserve old failed raw and compatible registered custom schema controls']})
    new_json(OUT / 'mu-m0-v6-source-scope.json', scope)
    prior = copy.deepcopy(cp['failure_counters'])
    for i, finding in enumerate(report['findings']):
        cp['failure_counters'].append({'origin_key': 'current-chat-20261012|mu_v5|' + str(finding.get('id', i)), 'attempts': 1, 'status': 'INDEPENDENT_REQUEST_CHANGES_PRESERVED', 'priority': finding.get('priority', finding.get('severity')), 'evidence_ref': reference(MIRROR / 'report.json'), 'counter_reset': False, 'actual_models': 0})
    assert cp['failure_counters'][:1371] == prior
    scope_ref = reference(OUT / 'mu-m0-v6-source-scope.json')
    resume = {'schema': 'researchos.current-chat-resume.v38', 'at': now, 'checkpoint_revision': 450, 'ownership_revision': 238, 'head': cp['head'], 'project_id': cp['project_id'], 'current_step_id': 'W05-99', 'goal_status': 'ACTIVE', 'accepted_formal_cases': 0, 'required_formal_cases': 42, 'required_parent_tasks': 22, 'failure_records_preserved': len(cp['failure_counters']), 'no_progress_rounds': cp['no_progress_rounds'], 'preflight_ref': reference(HERE / 'resume-preflight/preflight.json'), 'task_packet': 'VALIDATED_FILE W05-99 NOT_STARTED', 'mu_v5_review_ref': reference(MIRROR / 'report.json'), 'mu_v6_source_scope_ref': scope_ref, 'attach_source': 'b955c8665281193d5cbf90a146f936c9212c7940 frozen; independent review resumed', 'phone_ready': False, 'installed_mu': '8dfebe36508ac0c2508735bb866756dab9283e74 unchanged', 'actual_model_calls_this_continuation': 0, 'previous_turn_classification': 'PROGRESS', 'next_command': 'Implement Mu V6 exact9 from frozen V5 with independent review; finish Core attach review, integrate approved source then build fresh package and retry original desktop session. Preserve failures and all 22/42 requirements.'}
    new_json(OUT / 'RESUME.current.json', resume)
    resume_ref = reference(OUT / 'RESUME.current.json')
    cp.update({'revision': 450, 'expected_previous_revision': 449, 'updated_at': now, 'updated_by': 'codex:/root', 'next_command': resume['next_command']})
    cp['work_in_progress'].update({'current_chat_continuation_cp450': resume_ref, 'mu_m0_v5_review_ref': resume['mu_v5_review_ref'], 'mu_m0_current_status': 'V5_REQUEST_CHANGES_V6_EXACT9_REGISTERED_UNINSTALLED', 'mu_m0_v6_source_scope_ref': scope_ref})
    cp['evidence_index'].append({'kind': 'RESUMED_V5_REVIEW_AND_V6_REPAIR_SCOPE', 'ref': resume_ref, 'formal_increment': 0})
    ow.update({'revision': 238, 'expected_previous_revision': 237, 'updated_at': now, 'updated_by': 'codex:/root'})
    ow['special_paths']['mu_m0_v6_repair'] = {'owner': scope['owner'], 'ref': scope_ref, 'same9_scope_preserved': True, 'prior_owner_terminal_handle_absent': True}
    ow['path_lease_transfers'].append({'at': now, 'actor': 'codex:/root', 'new_owner': scope['owner'], 'new_subtask': 'W12-02/M0-v6-causal-repair', 'new_worktree': scope['worktree'], 'paths': scope['paths'], 'scope_ref': scope_ref, 'kind': 'SAME9_REPAIR_OWNER_TRANSFER_PRIOR_HANDLE_ABSENT'})
    for path, name in [(cp_path, 'checkpoint.before.raw.json'), (ow_path, 'ownership.before.raw.json'), (hand_path, 'handoff.before.raw.md')]:
        with (OUT / name).open('xb') as stream:
            stream.write(originals[path])
    for path, before in originals.items():
        assert path.read_bytes() == before
    replace(ow_path, originals[ow_path], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
    replace(cp_path, originals[cp_path], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
    prefix = '# Current verified continuation CP450\n\nRead `' + resume_ref['path'] + '` first. V5 independent REQUEST_CHANGES preserved; same9 V6 repair registered. Core attach b955 frozen, independent review resumed. Identity, protected9 and task packet verified. Phone not ready; formal0/42 all22 open.\n\n'
    replace(hand_path, originals[hand_path], prefix.encode() + originals[hand_path])
    assert state_path.read_bytes() == originals[state_path]
    print(json.dumps({'checkpoint': 450, 'ownership': 238, 'failures': len(cp['failure_counters']), 'resume': resume_ref}))

if __name__ == '__main__':
    main()
