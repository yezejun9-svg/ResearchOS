import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
WT = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311'
AUTHOR = WT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'
FINAL = AUTHOR / 'final-audit-c0fea60e04e34fbd803b5d2feae78df8'


def ref(path, expected=None):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    value = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or value['sha256'] == expected
    return value


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


assert sys.flags.isolated and not sys.flags.optimize
handoff_ref = ref(FINAL / 'handoff.json', 'c4bea94e1eec3c9f4a9393e9433d8501a9c51e81b899c51245a8027166a51f60')
handoff = json.loads((FINAL / 'handoff.json').read_bytes())
scope_path = WT / handoff['scope_registration_ref']['path']
conditions_path = WT / handoff['implementation_conditions_ref']['path']
source_audit_path = WT / handoff['source_scope_audit_ref']['path']
assert ref(scope_path) == {**handoff['scope_registration_ref'], 'path': scope_path.relative_to(ROOT).as_posix()}
assert ref(conditions_path) == {**handoff['implementation_conditions_ref'], 'path': conditions_path.relative_to(ROOT).as_posix()}
assert ref(source_audit_path) == {**handoff['source_scope_audit_ref'], 'path': source_audit_path.relative_to(ROOT).as_posix()}
source_audit = json.loads(source_audit_path.read_bytes())
assert source_audit['outside_bounds'] == [] and len(source_audit['rows']) == 15
sources = []
for row in source_audit['rows']:
    item = ref(WT / row['path'], row['sha256'])
    assert item['bytes'] == row['bytes']
    sources.append({'source_path': row['path'], 'original_current_ref': item})
roster_path = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_first_branch_revision_codex/a8e573ecbd20499c8bff9d4222dd9ffc/finite_roster.expanded.json'
roster = json.loads(roster_path.read_bytes())
assert len(roster['leaves']) == 159 and len(roster['regressions']) == 7
assert len({row['name'] for row in roster['leaves']}) == 159
replay_id = uuid.uuid4().hex
proposal = save('desktop_finite_replay.scope.draft.json', {
    'schema': 'researchos.desktop-exact15-root-independent-replay-proposal.v1',
    'state': 'DRAFT_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED',
    'executor': 'codex:/root', 'author': 'codex:/root/sources_parent_impl',
    'candidate': handoff['source_commit'], 'base': handoff['base'],
    'source_only_candidate': '840bc6cc3237ba4dddd3812d2bec157666dc50ee',
    'author_evidence_commit': '0f708eaf0c624fb721f7c9a00d5465ef5f13a68c',
    'author_handoff_ref': handoff_ref, 'original_source_scope_ref': ref(scope_path),
    'implementation_conditions_ref': ref(conditions_path), 'sources': sources,
    'roster_ref': ref(roster_path), 'original_finite_roster_unchanged': True,
    'ordered_finite_leaves': roster['leaves'], 'regression_units': roster['regressions'],
    'uuid': replay_id, 'new_export_root': '.local/independent-desktop-http-' + replay_id,
    'new_receipt_root': 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_root_independent_replay_codex/' + replay_id,
    'planned_phases': ['public_source_export_and_build', 'freeze_actual_inputs', 'finite_replay', 'qualification_seal'],
    'authorization_prerequisites': [
        'Non-author exact15 source and author-current159+7 audit is READY without requested changes.',
        'Root replay runner, fixed public export inventory and process controller receive separate static review.',
        'Root canonical registration binds exact runner/spec/controller/reviewer SHA and new unique roots.',
        'Actual CAS and registration seal finish before any export/build/test launch.'
    ],
    'public_export_policy': 'Candidate regular Git blobs from approved public source families, frozen public schemas/UI/fixtures and the individually approved Go compiler catalog; exclude execution receipts, private configuration and verifier-only datasets.',
    'build_policy': 'New source export and output/cache, fixed offline Go/Node/Electron/Python, actual -deps -test -compiled/-work/-x closure, generated importcfg/archives/exe, default React production assets. No author exe or old development resource reuse.',
    'process_policy': 'Explicit credential-free environment; pinned Windows owned process helper, suspended process assigned before resume, exclusive Job kill-on-close, actual exit/job-idle/all handles, first unexpected stop and no automatic retry.',
    'input_policy': 'Full actual source/schema/tools/imported runtime/assets/dependency/WORK/archive/exe vector frozen before each approved finite batch and checked after it; per-child critical source/resource vector, raw invocation and fixed descriptor/phase identity. Any drift or unbound actual input withholds qualification.',
    'count_policy': '159 exact named finite leaves plus7 original regression units, without inheriting any author PASS; actual PASS/FAIL/SKIP/NOT_RUN reported. Additional two compiled Go units may be proposed separately and cannot substitute for the original roster.',
    'stage_policy': 'Registered caps are maxima; all stage-specific noPOST and REQUEST full cleanup assertions remain. Preserve exact positive/offscreen renderer behavior and failure/quarantine controls.',
    'independent_phase_loopback_HTTP_maximum_proposed': 386,
    'author_original_phase_observed_HTTP_preserved': 302,
    'separate_phase_is_not_failure_counter_reset': True,
    'external_MODEL_SDK_paid_private_calls': 0,
    'first_unexpected_stop': True, 'automatic_same_input_retry': False, 'counter_reset': False,
    'Main_source_writes': 0, 'source_acceptance': False, 'formal_increment': 0,
    'still_hold': handoff['not_run_or_hold']
})
print(json.dumps({'proposal': proposal, 'source_paths': len(sources), 'actual_export_build_tests': 0}, ensure_ascii=True))
