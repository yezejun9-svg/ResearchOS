import hashlib,json,pathlib,sys
E=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
check=json.loads((E/'POST-INTEGRATION-INDEPENDENT-CHECK.json').read_bytes())
assert check['verdict']=='EXACT_MAIN_FAST_FORWARD_POST_REVIEW_PASS'
put('DIAGNOSTICS.json',{'new_unexpected_diagnostics':0,'new_review_failures':0,'capture_script_native_exit':0,'verification_script_native_exit':0,'expected_negative_query':{'argv':'git merge-base --is-ancestor 03aa4d687dfaa541d9b18d4c766805307a537d1d ecc28dd3c91a0f68dcddb41b53325aa7f0e81419','native_exit':1,'meaning':'C57 is not an ancestor of Main; expected negative predicate, not a failed command or product failure'},'checkpoint_revision_observed':555,'ownership_revision_observed':341,'mixed_diagnostic_history_count_observed':2250,'historical_counters_reset':False,'prior_diagnostics_preserved':True,'tests_builds_native_rerun':0,'source_or_shared_state_writes':0,'cleanups_or_rejected_action_retries':0,'formal_increment':0})
report='''# Main Desktop 七文件整合后独立复核

**结论：EXACT_MAIN_FAST_FORWARD_POST_REVIEW_PASS；阻断0，新诊断0。** 可供CP556收敛封存。

实际读取Git确认 Main分支为 `main`，HEAD `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`，tree `1d44a02c9483fc529b08ffe81895ec443920bdd1`，直接父为 `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`。差异仅已批准的6A/1M七路径；七文件磁盘字节、Git blob与r3候选SHA逐项相等，index为空。

原20条tracked dirty与独立preflight记录逐行一致。Root整合前48项保护refs在整合后55项refs中完整保留且hash/bytes相同，新增的7项恰为本次文件。Root新post gate已按ecc28检查Main，未把旧Main7d约束误用为当前HEAD。此处核对原保全回执，没有扩大访问原数据或凭据。

C57工作树实际HEAD仍为 `03aa4d687dfaa541d9b18d4c766805307a537d1d` 且clean；只读Git ancestry查询确认它不是Main祖先，未被此次fast-forward合入。该谓词预期返回1，已单独记录，不计为新诊断或产品失败。

两份commands、dispatcher、Desktop package与既有W13测试入口均与preflight hash一致。desktop.shell_launch和desktop.installer_build仍UNBOUND。读取当前状态为CP555/ownership341/mixed2250；既有历史不重置，未提升平台命令登记或正式接受。整合scope `ecf4ed370ee094af13a290d1c04c6d7925da7823ab4b273b84efcb97297ae8a2` 与实际runner/post-gate、前序review seals全部核对；Git执行及外层090回执均exit0，raw证明执行的仅为精确候选本地fast-forward。

已有source/build与有限owned native smoke可继续按相同提交/blob及原绑定开发产物引用；本次没有重新构建、测试或启动原生程序，也不把带原20条dirty的完整Main工作树视为干净候选。C57原恢复、installer、W13/W20全项或正式v2.4接受均不从本次整合推出，formal_increment=0。

复核仅在本独立main-integration-post目录写回执；source/shared-state写入0、GUI/Core启动或进程控制0、清理与被拒绝操作重试0。实际只读Git命令及期望退出码见ACTUAL-READ-ONLY-GIT-COMMANDS.json，原始整合证据副本见inputs目录。
'''
with (E/'POST-REVIEW.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
put('003-seal.recipe.json',{'argv':[sys.executable,'-B','-Xutf8',str(E/'seal_post.py')],'mode':'SEAL_POST_REVIEW_NO_BUILD_TEST_NATIVE_OR_SOURCE_MUTATION'})
rows=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ['POST-MANIFEST.json','POST-SEAL.json']]
put('POST-MANIFEST.json',{'schema':'researchos.desktop-main-integration-post-review-manifest.v1','root':str(E),'files':rows})
for r in rows:assert sha(E/r['path'])==r['sha256']
seal={'schema':'researchos.desktop-main-integration-post-review-seal.v1','verdict':check['verdict'],'main_commit':check['main_head'],'main_tree':check['main_tree'],'direct_parent':check['direct_parent'],'exact_seven_files':True,'original_20_tracked_dirty_preserved':True,'captured_original_48_refs_preserved':True,'C57_merged':False,'commands_unchanged':True,'index_empty':True,'scope_sha256':'ecf4ed370ee094af13a290d1c04c6d7925da7823ab4b273b84efcb97297ae8a2','report_sha256':sha(E/'POST-REVIEW.md'),'independent_check_sha256':sha(E/'POST-INTEGRATION-INDEPENDENT-CHECK.json'),'diagnostics_sha256':sha(E/'DIAGNOSTICS.json'),'manifest_sha256':sha(E/'POST-MANIFEST.json'),'reference_count':len(rows),'blocking_findings':0,'new_unexpected_diagnostics':0,'tests_builds_native_rerun':0,'formal_increment':0,'C57_recovery_or_acceptance':False,'installer_acceptance':False}
put('POST-SEAL.json',seal)
print(json.dumps({'verdict':seal['verdict'],'report_sha256':seal['report_sha256'],'manifest_sha256':seal['manifest_sha256'],'diagnostics_sha256':seal['diagnostics_sha256'],'seal_sha256':sha(E/'POST-SEAL.json'),'reference_count':len(rows),'new_diagnostics':0}))
