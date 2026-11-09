"""Receipt-only sealing, after actual isolated Python preparation/audit exit0."""
from pathlib import Path
import ast
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_io import OUT, PRIOR, REVIEW, ACTOR, ref, checked, load, dump, write

def main():
    for script in sorted(OUT.glob('*.py')):
        ast.parse(script.read_bytes().decode('utf-8'), filename=script.name)
    audit = load(OUT/'static-byte-audit.json')
    assert audit['status']=='STATIC_PREPARATION_CHECKED_NOT_ACCEPTED'
    assert audit['R01']['old_Test_raw_byte_bodies_equal_without_normalization']==28
    assert len(audit['R02']['five_planned_source_fact_pairs'])==5
    assert audit['vector_count']==114 and audit['whole_forward_inverse_bytes_exact']
    observations = []
    for phase in ['prepare.completed','audit.corrected']:
        observation = load(OUT/(phase+'.native-observation.json'))
        assert observation['actual_native_exit']==0
        assert observation['executable']=='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
        assert observation['argv'][:4]==['-I','-S','-X','utf8']
        assert observation['outer_exit'] is None
        observations.append(ref(OUT/(phase+'.native-observation.json')))
    enclosing = load(OUT/'enclosing-tool-results.json')
    assert enclosing['prepare']['outer_exit']==0 and enclosing['prepare']['actual_native_exit']==0
    assert enclosing['audit']['outer_exit']==0 and enclosing['audit']['actual_native_exit']==0
    before, after = load(OUT/'inputs.before.json'), load(OUT/'inputs.after.json')
    assert before==after
    for r in before:
        checked(r)
    group = load(OUT/'source-group.json')
    scope = load(OUT/'scope-and-open.json')
    scope['prior_preparation_scope_ref'] = ref(OUT/'scope-and-open.json')
    scope['new_failure_origins'].append(ref(OUT/'origin.metadata-BLOB-occurrence-count.json'))
    scope['actual_native_observations'] = observations
    dump('scope-and-open.final.json', scope)
    prior_hand = ref(PRIOR/'handoff.json')
    reviewer_hand = ref(REVIEW/'handoff.json')
    # Reused source refs remain explicit, pinned byte for byte. Current output
    # manifest covers only this owned namespace; prior whole-packet inventories
    # cover the immutable reused bytes rather than copying all 57MB again.
    readable = (
        '# I17 R01/R02 最小修订源码准备\n\n'
        '新候选只恢复 v4 test 的原 LF，并向原向量清单追加非作者计划中的五个 source 事实反例。'
        '28 个旧 Test 和另 17 个 driver Test 的原始字节 body 完全相同；I18 整个 body、'
        'v3 生产 source、私有 domain harness、修好的 I17 driver 断言及 DDL34 原样复用。\n\n'
        'R02 的五个反例保持 INTEGER mode5、合法 commit.insert/journal.update action 与 source34 '
        'mask/key/type 形状。分别删除一条 ADMITTED pin、一条 FINAL member，仅改 control '
        'CONFIRMED→RECONCILING、保留 header 内 expected_revision 7→8、保留 journal timestamp。'
        '每个坏向量逆向恢复一个事实即复原完整 baseline raw 字节，原因定位见 source-fact-cases.json '
        '及 static-byte-audit.json。预期是真实 callback nil+F08_ORIGINAL_BINDING、SQLite primary1、'
        '失败 INSERT 不增行，全部 SOURCE_INFERENCE_NOT_RUN；未执行目标 callback 或 SQL。\n\n'
        '原 109 项向量字节前缀及 100 项 dispatch controls 不变，新总数114。四条 pretransition '
        '序列仍24/24/26/26。八组 whole forward/inverse 逐字节闭合；新输出 MF 自排除。\n\n'
        '本包是作者的源码准备，未自签接受。独立复审、实际 Go producer/编译、v5 native source '
        '排序与 typeof-before-CAST、sameTxn parent/member/pin/control/solejournal、SQL24/22-23 '
        'rollback、初始 auth/current authority、mode3、ordinary native/SDK、完整历史/backup、'
        '合法大响应 solejournal completion/replay 均 FATAL_OPEN。需新 Root source/resource '
        'lease 和非作者复审后才能做后续真实验证。\n\n'
        '实际元数据 prepare/audit Python 与 enclosing 工具均0；seal 退出只由本次外层工具结果证明，'
        'sealed handoff 内为 NULL。本轮新出现一次只读 rg 不存在 specs 目录错误，outer1/nativeNULL；'
        '元数据检查另出现三次脚本自身失败，均 outer/native1，原脚本与日志保留；'
        '修正 root manifest 排除与 LF 分隔后使用新脚本字节、新日志，已写出的准备文件只读逐字节复用。'
        'BLOB 次数按实际 valid/corrupt 参数重算，原失败输入未重跑，旧 origins 不重计。'
        '所有目标测试 NOT_RUN；'
        'Main/canonical/module/cache/旧 sealed receipt/失败计数无写入。封存后 STOPPED。\n'
    )
    write('PREPARATION.md', readable.encode('utf-8'))
    handoff = {'schema':'researchos.f08.i17.minimal-binding-revision-preparation.handoff.v1',
        'actor':ACTOR,'owned_namespace':OUT.as_posix(),'writer_status':'STOPPED_AFTER_FINAL_SEAL',
        'status':'SEALED_SOURCE_PREPARATION_NOT_ADOPTED_NOT_RUN','self_acceptance':False,
        'independent_non_author_review':'REQUIRED_FOR_NEW_REFS_NOT_YET_DONE',
        'previous_author_handoff':prior_hand,'previous_author_manifest':ref(PRIOR/'manifest.json'),
        'non_author_REQUEST_handoff':reviewer_hand,'non_author_REQUEST_source_review':ref(REVIEW/'source-review.json'),
        'non_author_REQUEST_readable':ref(REVIEW/'REVIEW.md'),'non_author_minimum_plan':ref(REVIEW/'minimum-source-fact-plan.json'),
        'source_group_ref':ref(OUT/'source-group.json'),'changes_ref':ref(OUT/'changes.json'),
        'metadata_script_fix_ref':ref(OUT/'metadata-script-fix.json'),
        'metadata_audit_count_fix_ref':ref(OUT/'metadata-audit-count-fix.json'),
        'static_byte_audit_ref':ref(OUT/'static-byte-audit.json'),
        'raw_source_fact_cases_ref':ref(OUT/'source-fact-cases.json'),
        'corrected_producer_test_ref':group['producer_tests']['after'],
        'corrected_vector_manifest_ref':group['raw_vectors'],
        'reused_real_private_domain_harness':group['domain_harness']['after'],
        'reused_corrected_driver_test':group['driver_test_contract']['after'],
        'reused_v3_source':group['production_callback']['after'],
        'reused_real_driver_source':group['driver_source']['after'],
        'reused_v5_DDL34':group['original_DDL34'],
        'reused_raw_sequences_ref':group['raw_sequences'],
        'reused_provenance_ref':group['raw_provenance'],'reused_raw_digest_controls':group['raw_digest_controls'],
        'old_Test_raw_byte_bodies_equal_without_normalization':28,'other_driver_Test_raw_byte_bodies_equal':17,
        'I18_entire_raw_byte_body_equal':True,'original_partial17_controller_unchanged':True,
        'R01_original_LF_preserved':True,'original109_vector_prefix_raw_bytes_equal':True,
        'old100_dispatch_controls_unchanged':True,'new_source_fact_pairs':5,'vector_count':114,
        'same_accepted_mode_action_valid_shapes':True,'five_single_fact_byte_inverses_exact':True,
        'whole_forward_inverse_byte_pairs':8,'pretransition_frames':100,'sequence_frames':[24,24,26,26],
        'inputs_before_ref':ref(OUT/'inputs.before.json'),'inputs_after_ref':ref(OUT/'inputs.after.json'),
        'whole_prior_packet_audit_ref':ref(OUT/'whole-prior-packets.before.json'),
        'original_input_refs_rehashed':46,'total_pinned_inputs_rehashed':len(before),'input_drift':0,
        'source_and_callback_error_expectation_authority':'SOURCE_INFERENCE_NOT_RUN',
        'actual_callback_results':None,'actual_native_SQL_results':None,
        'metadata_actual_native_observations':observations,'enclosing_tool_results_ref':ref(OUT/'enclosing-tool-results.json'),
        'actual_python_prepare_exit':0,'actual_python_static_audit_exit':0,
        'prepare_audit_outer_exits':[0,0],
        'new_failure_origins':[ref(OUT/'origin.rg-absent-specs.json'),ref(OUT/'origin.metadata-membership.json'),ref(OUT/'origin.metadata-vector-newline.json'),ref(OUT/'origin.metadata-BLOB-occurrence-count.json')],
        'new_failure_exit_pairs':[{'outer':1,'actual_native':None},{'outer':1,'actual_native':1},{'outer':1,'actual_native':1},{'outer':1,'actual_native':1}],
        'prior_failures_preserved_not_recounted_not_retried':True,
        'original_tool_observations_ref':ref(OUT/'original-tool-observations.json'),
        'scope_ref':ref(OUT/'scope-and-open.final.json'),'remaining_FATAL_OPEN':scope['remaining_FATAL_OPEN'],
        'non_author_remaining_FATAL_OPEN_verbatim':scope['non_author_remaining_FATAL_OPEN_verbatim'],
        'all_target_tests_NOT_RUN':True,'Go_AST_compile_gofmt_driver_SQL_helper_HTTP_SDK_model_runs':0,
        'source_acceptance':False,'driver_adopted':False,'SQL24_adoption_allowed':False,
        'three_callbacks_complete':False,'formal_acceptance':False,'formal_increment':0,'full_I17':'FATAL_OPEN',
        'Main_canonical_module_cache_old_receipt_failure_counter_writes':0,
        'Root_next':'Non-author read-only R01/R02 exact-ref review, then separately Root-owned fresh source/resource lease and real Go/native verification',
        'manifest':{'path':(OUT/'manifest.json').as_posix(),'self_excluded':True},
        'seal_actual_outer_exit':None,'seal_actual_native_exit':None,
        'seal_exit_authority':'External enclosing exec_command result only; NULL is not a success claim',
        'finish':'STOPPED after final enclosing metadata seal result; no output changes afterward'}
    dump('handoff.json', handoff)
    members = [ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
    assert not any('/__pycache__/' in r['path'] for r in members)
    manifest = {'schema':'researchos.whole-namespace-manifest.v1','root':OUT.as_posix(),
        'self_excluded':'manifest.json','file_count':len(members),'total_bytes':sum(r['bytes'] for r in members),'members':members}
    dump('manifest.json', manifest)
    for r in members:
        checked(r)
    current = [ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
    assert current==members
    print(json.dumps({'status':'SEALED_SOURCE_PREPARATION_NOT_ADOPTED_NOT_RUN','actor':ACTOR,
        'writer_status':'STOPPED_AFTER_SEAL','handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),
        'static_audit':ref(OUT/'static-byte-audit.json'),'source_cases':ref(OUT/'source-fact-cases.json'),
        'producer_test':group['producer_tests']['after'],'vector_manifest':group['raw_vectors'],
        'members':len(members),'member_bytes':manifest['total_bytes'],'vector_count':114,
        'old_raw_Test_equal':28,'other_raw_driver_Test_equal':17,'single_fact_pairs':5,
        'target_runs':0,'full_I17':'FATAL_OPEN','self_acceptance':False,
        'seal_exit_authority':'External actual tool result only'},ensure_ascii=False))

if __name__=='__main__':
    main()
