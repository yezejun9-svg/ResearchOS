"""Resume the stopped CP558 source owner without changing product acceptance."""
import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import R, N, git, read, ref


def new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def swap(path, previous, value):
    assert path.read_bytes() == previous
    pending = path.with_name(path.name + '.cp559.pending')
    with pending.open('xb') as stream:
        stream.write(value)
    assert path.read_bytes() == previous
    os.replace(pending, path)


def main():
    cp_path, ownership_path, handoff, state = [R / ('execution/v2.4/' + name) for name in
        ['checkpoint.json', 'path_ownership.json', 'HANDOFF_RESUME_PACK.md', 'step_state.json']]
    before = {p: p.read_bytes() for p in [cp_path, ownership_path, handoff, state]}
    cp, ownership = read(cp_path), read(ownership_path)
    assert cp['revision'] == 558 and ownership['revision'] == 344
    assert len(cp['failure_counters']) == 2254
    preserved = verify()
    old_resume = read(N / 'continuation-cp558/RESUME.current.json')
    scope_ref = old_resume['product_host_source_scope_ref']
    scope_path = Path(scope_ref['path'])
    assert ref(scope_path)['sha256'] == scope_ref['sha256']
    scope = read(scope_path)
    worktree = Path(scope['worktree'])
    assert git(worktree, 'rev-parse', 'HEAD').decode().strip() == scope['base']
    spec = R.parent / 'ResearchOS_Implementation_Package_v2.4'
    pointer = read(R / 'execution/v2.4/current_spec.json')
    assert ref(spec / 'contracts/execution.plan.json')['sha256'] == pointer['plan_sha256']
    out = N / 'continuation-cp559'
    out.mkdir()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    command = ['python', str(spec / 'tools/task_packet.py'), 'next', '--state', str(state)]
    result = subprocess.run(command, cwd=R, capture_output=True)
    (out / 'selector.stdout.raw').write_bytes(result.stdout)
    (out / 'selector.stderr.raw').write_bytes(result.stderr)
    packet = json.loads(result.stdout.decode('utf-8-sig'))
    assert result.returncode == 0 and packet['state_source'] == 'VALIDATED_FILE'
    assert packet['step']['id'] == 'W05-99'
    new(out / 'selector.receipt.json', {'argv': command, 'cwd': str(R), 'exit': result.returncode,
        'stdout': ref(out / 'selector.stdout.raw'), 'stderr': ref(out / 'selector.stderr.raw'),
        'product_acceptance': 'NOT_ASSERTED'})
    diagnostics = [
        {'origin_key': '20261028|root-resume|private-state-backend-unavailable',
         'detail': 'Two recovery tool calls failed with backend request failed; used authoritative disk state. No mutation attempted.'},
        {'origin_key': '20261028|root-resume|truncated-read-output',
         'detail': 'Initial combined reads of old checkpoint/status/resume were truncated by output budget; reread selected current fields. Truncated reads are not complete evidence.'},
        {'origin_key': '20261028|root-resume|missing-receipt-helper-probe',
         'detail': 'Read of installed_delivery run_captured.py returned path absent. Existing capture.py located separately; no execution or retry.'},
        {'origin_key': '20261028|root-resume|missing-ops-package-probe',
         'detail': 'rg path ops/package absent, exit 1 preserved. Switched to inventory of existing ops paths.'},
    ]
    for row in diagnostics:
        row.update(status='READONLY_DIAGNOSTIC_PRESERVED', attempts=1, native_exit=None,
            product_failure=False, counter_reset=False)
    assert not ({r['origin_key'] for r in diagnostics} & {r.get('origin_key') for r in cp['failure_counters']})
    old_counters = list(cp['failure_counters'])
    cp['failure_counters'].extend(diagnostics)
    assert cp['failure_counters'][:len(old_counters)] == old_counters
    new(out / 'new-records-ledger.json', {'records': diagnostics, 'counter_reset': False,
        'historical_count': len(old_counters), 'current_count': len(cp['failure_counters'])})
    owner = 'codex:/root/product_host_resume_20261028'
    reviewer = 'codex:/root/product_host_independent_20261028'
    transfer = {'at': now, 'prior_scope_ref': scope_ref, 'prior_owner': scope['owner'],
        'new_owner': owner, 'reviewer': reviewer, 'worktree': str(worktree),
        'owner_liveness': 'Root collaboration.list_agents returned only root before spawning these replacements',
        'source_scope': scope['allowed_source_paths'], 'scope_change': 'OWNER_ONLY_NO_EXPANSION',
        'preserve_uncommitted_source': True, 'preserve_prior_failure_history': True,
        'actual_native_authority': False, 'Main_merge_authority': False,
        'formal_increment': 0}
    new(out / 'source-owner-transfer.json', transfer)
    new(out / 'live-resume-verification.json', {'at': now, 'preservation': preserved,
        'spec_plan_ref': ref(spec / 'contracts/execution.plan.json'), 'selector_ref': ref(out / 'selector.receipt.json'),
        'source_scope_ref': scope_ref, 'candidate_head': scope['base'],
        'previous_goal_turn_classification': 'PROGRESS',
        'classification_evidence': 'CP558 added exact14 source scope; uncommitted implementation and Go/Node/Python result files exist. No live build is claimed from old receipts.',
        'formal_increment': 0})
    resume = dict(old_resume)
    resume.update(schema='researchos.current-chat-resume.v137', at=now, checkpoint_revision=559,
        ownership_revision=345, failure_records_preserved=len(cp['failure_counters']),
        source_owner_transfer_ref=ref(out / 'source-owner-transfer.json'),
        live_resume_verification_ref=ref(out / 'live-resume-verification.json'),
        active_source_cards=[{'owner': owner, 'reviewer': reviewer, 'worktree': str(worktree),
            'task': 'Continue existing exact14 product-host source/build', 'scope_ref': scope_ref}],
        next_command='Finish existing exact14 shared product host and complete fresh layout build, freeze source/build, independent review, then Root-owned native lifecycle qualification. Preserve all old evidence/failures and original data. Actual installer/upgrade/uninstall and all22/42 remain required.')
    new(out / 'RESUME.current.json', resume)
    resume_ref = ref(out / 'RESUME.current.json')
    cp.update(revision=559, expected_previous_revision=558, updated_at=now,
        updated_by='codex:/root', next_command=resume['next_command'])
    cp['work_in_progress'].update(current_chat_continuation_cp559=resume_ref,
        product_host_owner_transfer_ref=ref(out / 'source-owner-transfer.json'))
    cp['evidence_index'].append({'kind': 'CP558_RESUME_OWNER_TRANSFER_LIVE_VERIFIED', 'ref': resume_ref,
        'formal_increment': 0})
    ownership.update(revision=345, expected_previous_revision=344, updated_at=now, updated_by='codex:/root')
    ownership['special_paths']['Installed_delivery_development'].update(owner=owner,
        state='ACTIVE_EXACT14_SOURCE_BUILD_NO_ACTUAL_NATIVE_AUTHORITY',
        owner_transfer_ref=ref(out / 'source-owner-transfer.json'))
    for p, name in [(cp_path, 'checkpoint.before.raw.json'), (ownership_path, 'ownership.before.raw.json'),
                    (handoff, 'handoff.before.raw.md')]:
        with (out / name).open('xb') as stream:
            stream.write(before[p])
    for p, value in before.items():
        assert p.read_bytes() == value
    swap(ownership_path, before[ownership_path], (json.dumps(ownership, ensure_ascii=False, indent=2) + '\n').encode())
    swap(cp_path, before[cp_path], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
    prefix = '# Current verified continuation CP559\n\nRead ' + resume_ref['path'] + ' first. Existing exact14 implementation resumed under current builder and independent reviewer. Source/build only; native awaits review. Main ecc28 and old data protected. Mixed2258; formal0/42/all22open.\n\n'
    swap(handoff, before[handoff], prefix.encode() + before[handoff])
    assert state.read_bytes() == before[state]
    print(json.dumps({'checkpoint': 559, 'ownership': 345, 'mixed_records': len(cp['failure_counters']),
        'resume_ref': resume_ref, 'formal_increment': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
