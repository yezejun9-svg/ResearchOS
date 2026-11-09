"""Save an honest pre-registration continuation snapshot without modifying canonical state."""
import hashlib
import json
from pathlib import Path
import sys

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'

def pin(p):
    p = Path(p).absolute()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def doc(p):
    return json.loads(Path(p).read_bytes())

def save(name, value):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

canon = [ROOT / ('execution/v2.4/' + name + '.json') for name in ('checkpoint','path_ownership','step_state','commands')]
cp, ow = doc(canon[0]), doc(canon[1])
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [328,156,469]
scope = doc(OUT / 'scope_registration.json')
assert pin(OUT / 'scope_registration.json')['sha256'] == '90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0'
assert scope['expected_registration'] == [329,157,481]
assert not any(Path(scope[k]).exists() for k in ('new_output_root','new_wrapper_root','new_export_root','new_authorization_root'))
payload = {
    'schema': 'researchos.root-resume.pre-registration.v1', 'actor': 'codex:/root',
    'snapshot_stage': 'R329_PREPARED_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED',
    'current_project_head': cp['head'], 'current_card': 'W05-99',
    'actual_canonical_tuple': [328,156,469], 'planned_registration': [329,157,481],
    'canonical_refs': [pin(p) for p in canon], 'current_scope_ref': pin(OUT / 'scope_registration.json'),
    'binding_ref': pin(OUT / 'binding.json'), 'prepared_draft_ref': pin(OUT / 'registration-draft.manifest.json'),
    'fixed_origin_cut_ref': pin(OUT / 'failure-origins.cut.json'), 'fixed_cut_origins': 12,
    'observed_origin_count_reported_at_snapshot': 484,
    'outside_fixed_cut': [
        {'origin': 'I17-author-PowerShell-parser', 'ref': pin(BASE / 'f08_i17_binding_revision_preparation_codex/b918c16361bb4744bc7fffb6434d6849/original-parser-failure.json'), 'actual_outer_exit': 1, 'actual_native_exit': None},
        {'origin': '89547b', 'ref': pin(BASE / 'cli43_current_bound_scope_independent_review_codex/2770189c101441f39fcbe8fd83d98ffd/failure-origin.89547b.json'), 'actual_outer_exit': 1, 'actual_native_exit': None},
        {'origin': 'F08-independent-I17-JS-parser', 'sealed_ref': None, 'actual_outer_exit': None, 'actual_native_exit': None, 'process_launched': False, 'authority': 'Agent report; sealed exact ref pending'}
    ],
    'prior_actual_execution': {
        'root_closed_manifest_ref': pin(BASE / 'integration_codex/cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec/root-launch.closed.manifest.json'),
        'independent_closed_review_ref': pin(BASE / 'cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09/review.json'),
        'native_calls': 13, 'all_native_calls_exit': 0,
        'case00': 'EXECUTED_UNQUALIFIED_HTTP_REQUESTED_BUFFER_ALIAS_SHA_MISMATCH',
        'case01': 'NOT_STARTED', 'scope_grant_spent': True, 'relaunch_old_scope_allowed': False
    },
    'new_ownership_fix_review_ref': pin(BASE / 'cli43_http_bytes_ownership_independent_review_codex/2c1fd6a5825447b99c8f7a9d6ceaa483/review.json'),
    'source_branches': {
        'driver18_controller_v2': 'SOURCE_ONLY; non-author review running; completion deadline issue still under review',
        'driver18_partial17': 'NOT_RUN; actual resource catalog/source lease/Root adapter+two grants missing',
        'I17_b918': 'SOURCE_ONLY; independent review running; original byte normalization and bad-vector coverage findings pending',
        'F08_SQL24_auth_history_ordinary_final_mode3': 'OPEN_NOT_ACCEPTED',
        'Desktop15': 'NOT_IMPORTED; needs qualified fresh43 plus separate Root15-file scope; no ancestor fast-forward'
    },
    'next_action': 'Wait actual registration-draft independent review, Root run CAS then seal/grant, prepare and independently review new caller, launch exactly once with fresh namespaces, close all actual observations and independent qualification.',
    'checkpoint_next_command': 'Protected historical field; follow actual current bound scope/receipt instead of stale r324 wait text.',
    'preserve': ['Old 11 tracked deleted artifacts, empty index and a510 Main head.', 'All old scopes, failed inputs, evidence and counter prefix.', 'No old binary/cache/grant reuse; no Qoder session.'],
    'completion_gate': {'required_effective_parents': 22, 'required_current_formal_cases': 42, 'last_verified_current_formal_acceptances': 0, 'formal_increment_this_snapshot': 0, 'goal_complete': False},
    'cleanup_pending': {'status': 'PENDING_POLICY_REJECTION', 'reason': 'blocked by policy',
        'path': 'D:/作品集/ResearchOS/execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/verify_inputs.py',
        'retained_without_alternative_deletion_tool': True},
    'credential_policy': 'User supplied credential remains opaque; no key unseal/copy/SDK/model calls in these finite scopes.',
    'automatic_retry': False, 'counter_reset': False, 'canonical_writes': 0
}
save('RESUME.prepare.snapshot.json', payload)
md = '# ResearchOS r329 续跑快照\n\n实际 canonical 仍为 CP328 / OW156 / 469首因；r329草案已准备，待独立复核后由 Root 唯一 CAS 写入329 /157 /481。固定12条cut保留，另3条晚到首因在cut外，报告观察总数484。\n\n上一轮13次native均0，首例测试叶运行成功但HTTP requested缓冲区引用导致SHA证据不合格，第二例未启动；原scope/grant已消耗，不得重跑。新的即时bytes.Clone修正已通过独立源码复核，须全新授权与产物执行。\n\n下一步按本目录实际scope、草案及独审继续：Root run → seal → grant → 新caller独审 → 一次launch → 实际闭合与独立资格复核。保护旧11处删除、空index、a510 HEAD及全部旧失败。22父任务和42正式用例未全部有效接受，目标仍未完成。\n\nF08 driver17、I17与SQL24仍未实际验证；Desktop15尚未导入。误写metadata脚本清理曾被自动审批以blocked by policy拒绝，文件保留，不换工具绕过。\n'
with (OUT / 'RESUME.prepare.snapshot.md').open('xb') as f:
    f.write(md.encode('utf-8'))
save('RESUME.prepare.snapshot.manifest.json', {'files': [pin(OUT / name) for name in (
    'RESUME.prepare.snapshot.json','RESUME.prepare.snapshot.md','save-resume.prepare-snapshot.py')], 'self_excluded': True})
print(json.dumps({'resume_ref': pin(OUT / 'RESUME.prepare.snapshot.json'),
    'manifest_ref': pin(OUT / 'RESUME.prepare.snapshot.manifest.json'), 'canonical_writes': 0}, ensure_ascii=False))
