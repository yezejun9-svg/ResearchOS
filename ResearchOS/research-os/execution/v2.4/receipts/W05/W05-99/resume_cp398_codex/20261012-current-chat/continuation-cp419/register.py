import copy, datetime, hashlib, json, os, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[8]
OUT = pathlib.Path(__file__).resolve().parent
assert ROOT.name == 'research-os', ROOT
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp_path = ROOT / 'execution/v2.4/checkpoint.json'
ow_path = ROOT / 'execution/v2.4/path_ownership.json'
handoff_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
cp_raw, ow_raw, handoff_raw = cp_path.read_bytes(), ow_path.read_bytes(), handoff_path.read_bytes()
cp, ow = json.loads(cp_raw), json.loads(ow_raw)
assert (cp['revision'], ow['revision']) == (418, 206)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == 'd3a0fcaf506f1a3dd88f3f5d0a46f7bc1f0b56c1'
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
before_failures = copy.deepcopy(cp['failure_counters'])
before_no_progress = copy.deepcopy(cp['no_progress_rounds'])
assert len(before_failures) == 1273

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def ref(path):
    path = pathlib.Path(path)
    if not path.is_absolute(): path = ROOT / path
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

review_dir = ROOT / 'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_client_review_codex/20261012-current-chat'
review_ref = ref(review_dir / 'independent-review.json')
manifest_ref = ref(review_dir / 'receipt_manifest.json')
assert review_ref['sha256'] == '70255845d8759d930435184d4e1b6e1e8cc0e5c62e10ec190082278d01bf047f'
assert manifest_ref['sha256'] == 'ead81542d3840c6e6476d7776bfa84445739877c42081cd8075272896d62a4a9'
review = json.loads((review_dir / 'independent-review.json').read_bytes())
assert review['decision'] == 'REQUEST_CHANGES'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json').read_bytes())['protected_source']
assert all(ref(row['path'])['sha256'] == row['sha256'] for row in protected)
worktree = '.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012'
candidate = 'fc350c97cddbf7d54e37b88ece25b0e8be8f1d87'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT / worktree).decode().strip() == candidate
scope = {'schema': 'researchos.desktop-managed-client-causal-repair-scope.v1', 'at': now,
         'subtask': 'W05-99/normal_desktop_managed_qualification_client_repair_v2',
         'owner': 'codex:/root/w05_main24', 'model': 'gpt-6-sol', 'reasoning': 'high',
         'base': candidate, 'worktree': worktree,
         'paths': ['apps/desktop/main/lib/desktop-management.js', 'apps/desktop/main/lib/ipc.js',
                   'apps/web/src/workbench.jsx', 'tests/ui/desktop/desktop-management-boundary.test.mjs',
                   'tests/ui/continuity/managed_qualification_driver.mjs'],
         'review_ref': review_ref, 'original_manifest_ref': manifest_ref,
         'findings': [row['id'] for row in review['findings']],
         'scope': 'RECOVER_ONLY_PROVABLY_UNCONFIRMED_VALIDATED_EXPIRED_INTENT_WITH_AUDIT_PRESERVATION_AND_FRESH_HOST_BOUND_CURRENT_SUMMARY',
         'constraints': ['Never retire consumed, sent/uncertain CONFIRM, or uncertain private operation',
                        'No automatic PREPARE/CONFIRM or model call; preserve original identity/history',
                        'Fresh trusted host/process checks must also guard async summary responses',
                        'No new coding UI, frozen V2/Native3, shared Canon, Core, CLI or threshold edits',
                        'New source candidate and new bound build; preserve rejected original',
                        'Report required additional paths before editing'],
         'actual_model_calls': 0, 'independent_review_required': True}
put(OUT / 'client-repair-scope.json', scope)
scope_ref = ref(OUT / 'client-repair-scope.json')
for name, raw in [('checkpoint.before.raw.json', cp_raw), ('ownership.before.raw.json', ow_raw), ('HANDOFF.before.raw.md', handoff_raw)]:
    (OUT / name).write_bytes(raw)
cp['revision'], cp['expected_previous_revision'] = 419, 418
ow['revision'], ow['expected_previous_revision'] = 207, 206
cp['updated_at'], cp['updated_by'], cp['head'] = now, 'codex:/root', head
ow['updated_at'], ow['updated_by'] = now, 'codex:/root'
cp['workers'].append({**scope, 'step_id': 'W05-99', 'state': 'NEW_CAUSAL_SOURCE_REPAIR_AUTHORIZED', 'scope_ref': scope_ref})
ow['path_lease_transfers'].append({'at': now, 'actor': 'codex:/root', 'new_subtask': scope['subtask'],
    'new_owner': scope['owner'], 'new_worktree': worktree, 'paths': scope['paths'], 'scope_ref': scope_ref,
    'kind': 'NEW_CLIENT_LIFETIME_CONTEXT_CAUSAL_REPAIR_PRESERVE_REJECTED_INPUT'})
for row in review['findings']:
    key = 'current-chat-20261012|desktop-managed-client|' + row['id']
    assert all(item.get('origin_key') != key for item in cp['failure_counters'])
    cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'status': 'INDEPENDENT_P2_REPRODUCED_NEW_CAUSAL_REPAIR_PENDING',
        'counter_reset': False, 'evidence_ref': review_ref, 'actual_models': 0})
for path in [review_dir / 'independent-review.json', review_dir / 'receipt_manifest.json',
             ROOT / 'execution/v2.4/receipts/W05/W05-99/installed_runtime_component_preparation_codex/20261012-current-chat/component-package.json',
             ROOT / 'execution/v2.4/receipts/W05/W05-99/installed_runtime_component_preparation_codex/20261012-current-chat/manifest-acl.json']:
    cp['artifacts'].append(ref(path))
cp['temporary_cleanup_pending'].append({'path': (review_dir / 'vite-cache').as_posix(),
    'status': 'BLOCKED_AUTOMATIC_APPROVAL_REVIEW', 'reason': 'blocked by policy; retained and excluded, no alternate deletion method',
    'evidence_ref': review_ref, 'shared_progress_unblocked': True})
next_command = ('Repair the two proven Desktop client lifetime/current-host P2 defects in new candidate, independently review and integrate exact cumulative source. '
                'Continue coding Core explicit workspace/files/checks authorization, with zero actual model calls until reviewed product flow. '
                'Prepare complete hash-bound real Core/Mu/public contracts/migrations package, then normal native first-use and explicit one-model qualification; no substitute RPC acceptance. '
                'Preserve original CLI bug, all failures, old paid UNKNOWN and formal 0/42. Phone: user real phone only when product pairing ready.')
cp['next_command'] = next_command
cp['work_in_progress']['next_action'] = next_command
cp['work_in_progress']['desktop_managed_client_review_ref'] = review_ref
cp['work_in_progress']['desktop_managed_client_status'] = 'REJECTED_TWO_P2_NEW_REPAIR_UNINTEGRATED'
cp['work_in_progress']['coding_core_status'] = 'IMPLEMENTING_17_PATHS_NO_ACTUAL_MODEL_CALL'
cp['work_in_progress']['current_main_source_head'] = head
cp['current_effective_formal_status']['current_head'] = head
cp['current_effective_formal_status']['needs_rederive_after_source_change'] = True
assert cp['failure_counters'][:len(before_failures)] == before_failures
assert cp['no_progress_rounds'] == before_no_progress
resume = {'schema': 'researchos.current-chat-resume.v15', 'at': now, 'checkpoint_revision': 419,
    'ownership_revision': 207, 'head': head, 'project_id': cp['project_id'], 'current_step_id': 'W05-99',
    'accepted_formal_cases': 0, 'required_formal_cases': 42, 'required_parent_tasks': 22,
    'failure_records_preserved': len(cp['failure_counters']), 'goal_status': 'ACTIVE',
    'client_rejected_review_ref': review_ref, 'client_repair_scope_ref': scope_ref,
    'actual_component_preparation_ref': ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/installed_runtime_component_preparation_codex/20261012-current-chat/component-package.json'),
    'coding_core_status': 'IMPLEMENTING_EXPLICIT_POLICY_17_PATHS', 'actual_model_calls_this_preparation': 0,
    'phone_user_answer': 'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY', 'phone_ready': False,
    'old_paid_unknown_replayed': False, 'next_command': next_command}
put(OUT / 'RESUME.current.json', resume)
cp['artifacts'].append(ref(OUT / 'RESUME.current.json'))
prefix = ('<!-- Current Codex resume CP419 / OW207 / Maind3a0fcaf / 2026-10-12; prior bytes retained. -->\n\n'
          'Desktop客户端独审封存REQUEST_CHANGES：过期未CONFIRM请求在session变更后永久卡住，切Host后current摘要仍显示原授权；两个P2限定反例与DOM原证据保留，新v2客户端scope已登记。'
          '真实reviewed Core/Mu组件已准备并保护manifest，未激活；完整随包公开合同/迁移与当前源码绑定待补。codingCore17路径继续实现，0新实际模型；保留1275失败/诊断、正式0/42、22父门OPEN，CLI583原问题未预修、旧付费UNKNOWN不重放。'
          '手机使用用户真实手机，产品配对入口ready后再操作。\n\n机器续跑：' + (OUT / 'RESUME.current.json').as_posix() + '。\n\n').encode('utf-8')
def replace(path, expected, raw):
    assert path.read_bytes() == expected, 'Concurrent mutation: ' + str(path)
    temporary = path.with_name(path.name + '.cp419.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
assert cp_path.read_bytes() == cp_raw and ow_path.read_bytes() == ow_raw and handoff_path.read_bytes() == handoff_raw
replace(ow_path, ow_raw, (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
replace(cp_path, cp_raw, (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
replace(handoff_path, handoff_raw, prefix + handoff_raw)
print(json.dumps({'checkpoint_revision': 419, 'ownership_revision': 207, 'failure_records_preserved': len(cp['failure_counters']),
                  'scope_ref': scope_ref, 'resume_ref': ref(OUT / 'RESUME.current.json'), 'protected_source_drift': 0}))
