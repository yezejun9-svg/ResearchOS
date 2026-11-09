import hashlib
import json
import sys
from pathlib import Path

Q = Path(__file__).resolve().parent

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def main():
    basis = json.loads((Q / 'basis.json').read_text(encoding='utf-8'))
    links = json.loads((Q / 'old-generation-owner-links.json').read_text(encoding='utf-8'))
    archived = json.loads((Q / 'archived-canonical-closed-generation.json').read_text(encoding='utf-8'))
    excerpts = json.loads((Q / 'Source03-generation-excerpts.json').read_text(encoding='utf-8'))
    assert archived['old_source_projection_precondition_holds'] is False
    assert archived['old_subtask']['state'] == 'CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE'
    assert archived['old_subtask']['lease_status'] == 'CONSUMED'
    assert archived['old_worker_count'] == 1
    assert archived['old_workers'][0]['state'] == 'CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE'
    guards = [pin(Q / filename) for filename in ('SourceGuard.closed.json',
        'closed-generation-SourceGuard.closed.json', 'archived-canonical-SourceGuard.closed.json')]
    for ref in guards:
        closed = json.loads(Path(ref['path']).read_text(encoding='utf-8'))
        assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
    mapping = [
        {'line': 26, 'function': 'module constants', 'check': 'fixed KEY and SLICE shared by every registration/live gate'},
        {'line': 286, 'function': 'projection', 'check': 'KEY absent and no worker with SLICE, regardless of closed state'},
        {'line': 289, 'function': 'projection', 'check': 'new ownership subtask uses KEY'},
        {'line': 299, 'function': 'projection inverse', 'check': 'remove only the new KEY to restore original OW bytes'},
        {'line': 338, 'function': 'build', 'check': 'owner and worker common slice_id equals fixed SLICE'},
        {'line': 367, 'function': 'registration', 'check': 'owner/worker fixed SLICE and exact state/scope'},
        {'line': 400, 'function': 'live', 'check': 'select all workers of SLICE, including closed history'},
        {'line': 401, 'function': 'live', 'check': 'exactly one selected worker and fixed KEY task lookup'},
    ]
    proposal = {
        'old_KEY': 'public22_to_main23_continuation', 'old_SLICE': 'PUBLIC22_TO_MAIN23_CONTINUATION',
        'new_KEY_candidate': 'public22_to_main23_continuation_gen02',
        'new_SLICE_candidate': 'PUBLIC22_TO_MAIN23_CONTINUATION_GEN02',
        'candidate_author': None, 'candidate_source_ref': None, 'execution_grant': False,
        'minimal_Source_delta': [
            'new immutable Source namespace, self refs and own non-author review',
            'replace the two fixed constants together; retain existing MODE/schema/STATE/purpose',
            'pure projection predecessor gate: old frozen KEY+SLICE must still exist exactly once, state CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE and lease CONSUMED, exact frozen predecessor scope/owner/worker links',
            'new HDF/input metadata explicitly pins predecessor Scope/facts/owner/worker/failed case/CP386 closure and archives; it grants no execution',
        ],
        'unchanged': ['no state-filter bypass of duplicate-generation gate',
            'no arbitrary request-provided KEY/SLICE', 'all original request/evidence/1025 assertions',
            'Source03 working-copy compatibility fix and observation-before-close fix',
            'exact runtime/module/SQLite qualification and all provider/private-file boundaries',
            'all other CP workers, OW subtasks, historical files, current SS/CM and failure counters'],
    }
    lineage = {'facts_ref': links['facts_ref'], 'scope_ref': links['scope_ref'], 'owner_ref': links['owner_ref'],
               'worker_ref': links['worker_ref'], 'actual_failed_case_ref': basis['Root_resume']['W05']['old_actual_case_ref'],
               'closure_committed_ref': basis['Root_resume']['W05']['closure_ref'],
               'Root_closure_actual_audit_ref': next(ref for ref in basis['source_refs'] if Path(ref['path']).name == 'w09.w05-failed-scope-consumed-cp386.actual-audit.root.json'),
               'after_archive_refs': archived['archive_refs'], 'failure_counter_archive_digest': archived['failure_counters_digest']}
    negatives = [
        'same old KEY+SLICE with new id/lease: reject projection286',
        'new KEY only: reject old SLICE at286 and fail uniqueness400',
        'new SLICE only: reject old KEY at286',
        'same old generation plus closed-state filtering: disallowed history bypass',
        'old generation still ACTIVE/unclosed/missing/foreign scope: reject predecessor gate',
        'new generation already exists or has multiple workers: reject current generation',
        'owner/worker disagreement, nonRoot or cross-scope owner link: reject287/367/402/407',
        'expired/reused/non32hex lease or lease duration over3600s: reject90-93',
        'stale current4/revisions, wrong Source review or pre-review capture: reject271-281',
        'mutated failure counters/next ordinal/old workers or subtasks: reject inverse296-304',
        'old existing output directory or consumed old facts/activation for gen02: reject271-281/361-407',
    ]
    decision = {
        'schema': 'researchos.public22-main23-scope-generation-readonly-diagnosis.v1',
        'decision': 'SOURCE03_FIXED_GENERATION_BLOCKS_NEW_REGISTRATION_REQUIRES_NEW_SOURCE_GENERATION',
        'reviewer_id': 'codex:/root/backup_regression_resources', 'backend_actor': '/root/backup_regression_resources',
        'Source03_caller_ref': basis['Source03_hdf']['caller_ref'],
        'Source03_HDF_ref': basis['source_refs'][0], 'Source03_MF_ref': basis['Source03_hdf']['manifest_ref'],
        'Source03_contract_ref': basis['Source03_hdf']['calling_contract_ref'],
        'all_KEY_SLICE_uses': excerpts['KEY_SLICE_uses'], 'gate_mapping': mapping,
        'actual_old_generation': {'CP_archive_revision': 386, 'OW_archive_revision': 190,
            'state': archived['old_subtask']['state'], 'lease_status': archived['old_subtask']['lease_status'],
            'old_worker_count': 1, 'original1201': 'FAILED_RETAINED_PREPARE_COPIED22_LOGICAL_STATE',
            'original1025': 'FAILED_RETAINED', 'new_native_children_attempted': 0, 'Native_exit': None},
        'predecessor_lineage': lineage, 'minimal_candidate_boundary': proposal,
        'unique_owner_rule': 'exactly one owner/worker in the new fixed generation, both Root, same fresh Scope/lease and acyclic document refs; historical Root workers remain in Canon. Global worker_id uniqueness is not an existing contract.',
        'lease_rule': 'new independent 32lowerhex lease; issued<=now<expires; 0<duration<=3600s; exact same lease in q/scope/owner/worker; consumed old lease never becomes authority',
        'counter_rule': 'new projection preserves the complete actual fresh before cp.failure_counters and root_next_failure_ordinal_live exactly (source304), while retaining all old failure identities. CP386 is lineage, not a frozen future counter or current4 grant; legitimate later Root diagnostic appends remain.',
        'Root_registration_prerequisites': [
            'new Source/HDF/MF/input/contract exact pins and new true Full non-author Source review plus runtime qualification',
            'actual fresh current4 hashes/bytes/revisions and actual Root postreview capture before q.created_utc',
            'predecessor exact closed/consumed lineage against current before CP/OW; candidate KEY/SLICE both absent',
            'fresh 32lowerhex continuation id, unused registration/output roots and fresh finite lease',
            'Root build/check then true activation capture, TP append-only registration CP/OW+1 preserving SS/CM and all counters',
            'new immutable execute request plus separate true preentry Root hostpair; only later Root can execute the three pending children',
        ],
        'unexecuted_negative_boundaries': negatives, 'boundary_control_status': 'NOT_RUN_DIAGNOSIS_ONLY',
        'source_guard_refs': guards, 'Source_guards_closed': True, 'retained_handles_count': 0,
        'live_Canon_read': False, 'projection_build_activate_execute_calls': 0,
        'old_success_control_replays': 0, 'Native_Go_SQL_model_TP_calls': 0,
        'candidate_Source_written': False, 'Main_Canon_Scope_writes': 0,
        'formal_acceptance': False, 'execution_grant': False, 'STOP': True,
    }
    decision_ref = save('decision.json', decision)
    report = '\n'.join([
        'Source03固定代次阻止合法新注册。此报告仅诊断；没有运行projection/build/check/activate/execute。',
        '实际CP386/OW190 after archives与Root closure.committed的SHA/bytes相同；没有读取live Canon。',
        '旧owner及唯一worker：CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE / CONSUMED；原1201 prepare失败、child0、Native exit NULL。',
        'Source03:26固定KEY/SLICE；286不允许任何同名历史；289/299新增与逆恢复KEY；338/367绑定SLICE；400/401限定唯一worker及KEY。',
        '因此只换continuation_id、输出根、lease不能续跑；旧closed历史必须完整保留。',
        '候选新固定KEY=public22_to_main23_continuation_gen02，SLICE=PUBLIC22_TO_MAIN23_CONTINUATION_GEN02。',
        '只在新Source namespace修改两常量/自refs/合同，并增加纯前代closed+CONSUMED+精确Scope链门；不要改成忽略closed重复项。',
        'HDF显式继承旧Scope/facts/owner/worker/失败case/Root CP386闭合原件；无新授予。',
        '每新代次只有一个Root owner/worker，共同新Scope/新lease；历史同Root actor工作者并不删除，也不能误加全局worker_id唯一门。',
        'lease保持32lowerhex、有效期(0,3600s]、issued<=now<expires；所有q/scope/owner/worker精确一致。',
        'Source304保持当前before完整failure_counters/next ordinal；CP386是历史继承，不把后来合法Root新增诊断回退至CP386。',
        'Root前置：新Source非作者复核+runtime资格，真实新current4/postreview capture、unused roots/id/lease、前代closed精确链、Root新TP注册与preentry。',
        '保持MODE/schema/STATE、原22证据/1025/1201、工作副本修复、Owner私有文件边界、全部旧workers/subtasks、SS/CM与计数。',
        '反例边界仅列明NOT_RUN：单改KEY或SLICE、旧前代ACTIVE/缺链、重复代次、错owner、过期lease、staleCAS、改计数、旧facts/旧输出复用均拒绝。',
        '完整精确行号、SHA/bytes、前代七件链和SourceGuard闭合见decision.json。',
        '没有写candidate Source/Main/Canon/Scope；没有产品、Go、SQL、模型、TP调用；不能据此执行或接受。',
    ]) + '\n'
    with (Q / 'report.txt').open('xb') as stream:
        stream.write(report.encode('utf-8'))
    members = [pin(path) for path in sorted(Q.iterdir(), key=lambda path: path.name)
               if path.is_file() and path.name not in ('HDF.json', 'MF.json')]
    mf_ref = save('MF.json', {'schema': 'researchos.immutable-readonly-diagnosis-manifest.v1',
        'members': members, 'member_count': len(members), 'exclusions': ['HDF.json', 'MF.json', 'external seal tool pair after Final'],
        'formal_acceptance': False, 'execution_grant': False})
    hdf_ref = save('HDF.json', {'schema': 'researchos.public22-main23-scope-generation-diagnosis-handoff.v1',
        'reviewer_id': decision['reviewer_id'], 'backend_actor': decision['backend_actor'],
        'decision': decision['decision'], 'manifest_ref': mf_ref, 'decision_ref': decision_ref,
        'report_ref': pin(Q / 'report.txt'), 'source_refs': basis['source_refs'],
        'predecessor_lineage': lineage, 'source_guard_refs': guards,
        'original_IO_ref': pin(Q / 'diagnosis.original-tool-io.REENCODED.json'),
        'raw_own_audit_capture_ref': None, 'formal_acceptance': False, 'execution_grant': False, 'STOP': True})
    print(json.dumps({'HDF_ref': hdf_ref, 'MF_ref': mf_ref, 'decision_ref': decision_ref,
                      'report_ref': pin(Q / 'report.txt'), 'Source_guards_closed': True,
                      'new_original_failures': 0, 'product_calls': 0, 'formal_acceptance': False}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    code = main(); print('ROOT_PYTHON_EXIT=' + str(code)); sys.exit(code)
