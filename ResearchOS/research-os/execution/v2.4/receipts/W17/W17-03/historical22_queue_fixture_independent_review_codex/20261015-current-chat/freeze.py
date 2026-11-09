from verify import *

before=load(OUT/'guards-before.json');after=load(OUT/'guards-after.json')
cp=MAIN/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp500'
assert sha(cp/'RESUME.current.json')=='a3da48384a5e1013b8426c39bdd5c267838cd773f4d577bdff9426b42fd7260e'
names={'execution/v2.4/HANDOFF_RESUME_PACK.md':'handoff.before.raw.md','execution/v2.4/checkpoint.json':'checkpoint.before.raw.json','execution/v2.4/path_ownership.json':'ownership.before.raw.json'}
changed={k for k in before['main_dirty'] if before['main_dirty'][k]!=after['main_dirty'][k]}
assert changed==set(names)
assert all(sha(cp/v)==before['main_dirty'][k] for k,v in names.items())
assert all(before[k]==after[k] for k in before if k!='main_dirty')
assert set(before['main_dirty'])==set(after['main_dirty']) and len(before['main_dirty'])==20
save('guard-supplement-cp500.json',{'original_guard_result':'FAIL_RETAINED','attribution':'Root confirmed CP499 to CP500 CAS during independent review; no reviewer write to shared files','root_message':'CP500/OW286/failure_records1535; register_cp500.py native0 toolchunk59ce3d','root_resume':pin(cp/'RESUME.current.json'),'root_registrar':pin(cp.parent/'register_cp500.py'),'changed_three':{k:{'before_sha256':before['main_dirty'][k],'after_sha256':after['main_dirty'][k],'matching_root_before_receipt':pin(cp/v)} for k,v in names.items()},'other_17_unchanged':True,'main_head_index_and_dirty_path_set_unchanged':True,'candidate_helper_db_record_unchanged':True})
log({'kind':'shared-guard-attribution','native_exit':0,'original_guard_failure_retained':True,'attributed_to':'Root CP499 to CP500 CAS','three_files':sorted(changed),'other_17_unchanged':True})
log({'kind':'cleanup-denied','native_exit':None,'execution_started':False,'policy_result':'blocked by policy','action':'PowerShell Remove-Item -LiteralPath task-owned exact temporary root -Recurse -Force','path':str(TEMP),'result':'RETAINED_NO_BYPASS','prior_denied_paths_untouched':True})
t3path=MAIN/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat/T3-domain-backup.json'
t3=load(t3path);assert t3['native_exit']==1 and t3['go_test_top_level']['fail']==3
assert sha(t3['stdout']['path'])==t3['stdout']['sha256']
events=[json.loads(line) for line in Path(t3['stdout']['path']).read_bytes().splitlines() if line.startswith(b'{')]
failed=sorted(e['Test'] for e in events if e.get('Test') and e['Action']=='fail')
assert failed==sorted(['TestConfigurationUpgradeActiveQueueRecovery','TestConfigurationUpgradeFrozen22ProgramLock','TestConfigurationUpgradeNativeCLI'])
save('historical-failures-preserved.json',{'author_ledger':pin(AUTHOR/'FAILURE-LEDGER.json'),'author_attempts':18,'author_failed_attempts':7,'prior_T3':pin(t3path),'prior_T3_raw':pin(t3['stdout']['path']),'prior_T3_failed_tests':failed,'rewrite_or_reset':False})
testrefs={label:pin(OUT/(label+'.invocation.json')) for label in ('active','adjacent','missing-record','wrong-record-pin','wrong-db-pin','wrong-row-pin')}
diags=[json.loads(line) for line in (OUT/'diagnostic-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
save('diagnostic-ledger.json',{'append_only_source':pin(OUT/'diagnostic-ledger.jsonl'),'entries':diags,'expected_negative_test_native_failures':4,'unexpected_product_test_failures':0,'review_script_failures':2,'exploratory_tool_diagnostics':2,'expected_missing_historical_tree_native_failure':1,'cleanup_policy_denials':1,'prior_author_failures':7,'prior_T3_failed_tests':3,'counter_reset':False})
review={'schema':'researchos.historical22-fixture-independent-source-review.v1','verdict':'LIMITED_SOURCE_ACCEPTED','reviewer':'codex:/root/historical22_fixture_review','model':'gpt-6-astra','reasoning_effort':'high','candidate_commit':'6802628826dcc4b79a16ced20a8e26f7e5494a1b','candidate_tree':'3069fa1b6321772cf7717e5a2b1a24dda0c54376','base_commit':'2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02','changed_paths':['internal/domain/backup_configuration_upgrade_test.go'],'scope':pin(SCOPE),'author_final':pin(AUTHOR/'FINAL-02.json'),'source_hash':after['candidate_source'],'source_only':True,'fresh_positive_tests':3,'fresh_positive_failures':0,'fresh_skips':0,'expected_negative_test_failures':4,'independent_named_assertions':22,'existing_nonempty_loss_mutation_probes':8,'go_total_assertion_count':'Not instrumented; no fabricated total. 22 independent assertions counted explicitly in snapshot-assertions.json.','input_validation':{'historical_selected_source_files':502,'archive_members':502,'additional_helper_files':1,'prior_compiler_vector':5922,'native_pins':29,'original_closed_db_unchanged':True,'helper_unchanged':True,'prior_missing_git_tree_still_missing':True},'test_invocations':testrefs,'blocking_findings':[],'observations':[{'id':'H22-O1','severity':'integration_condition','description':'Candidate fixture depends on externally provisioned record+closed DB, source22 resources and target23 native program. Environment hash pins are supplied by runner and are not an independent provenance authority. This review anchors exact external artifacts through frozen scope; fresh checkout CI portability is not established.','action':'Before wider suite/CI integration, provision the verified frozen artifact bundle and exact invocation env, including stable workspace path; fail closed on missing/mismatched resources. Do not replace pins with caller-unreviewed records.'},{'id':'H22-O2','severity':'evidence_boundary','description':'Helper invokes historical ClientService.Execute for goal.start + seven session.send + session.control and public orchestration. Six queue states use synthetic SQL receipts/state updates, and Project/WorkspaceBinding current bodies/hashed paths are rebound to stable fixture workspace. No public SDK/provider phase completion demonstrated.','action':'Keep fixture-only and workspace-rebinding declarations attached whenever these results are cited; retain seven-phase setup versus post-CANCEL four-state distinction.'},{'id':'H22-O3','severity':'diagnostic','description':'Initial whole-main guard failed because Root changed three shared continuation files to CP500. Original FAIL remains; supplement matches Root before bytes and confirms other17 plus Source/helper/DB unchanged.','action':'Use guard-supplement-cp500.json alongside original guard snapshots; do not cite whole-main hash equality.'}],'boundaries':{'main_integration':'NOT_DONE','package_acceptance':'NOT_EVALUATED','schema25_candidate':'NOT_MAIN','actual_original_migration':'NOT_PERFORMED','actual_run_replay':'NONE','model_provider_dispatch':'NONE','formal_increment':0,'formal_accepted':0,'formal_required':42,'all_22_parent_tasks':'OPEN'},'cleanup':{'path':str(TEMP),'status':'POLICY_DENIED_RETAINED_NO_BYPASS'},'evidence':{name:pin(OUT/name) for name in ('input-provenance.json','snapshot-assertions.json','guards-before.json','guards-after.json','guard-supplement-cp500.json','historical-failures-preserved.json','diagnostic-ledger.json','diagnostic-ledger.jsonl')}}
save('review.json',review)
md='''# Historical22 fixture 独立 Source 审查

结论：**LIMITED_SOURCE_ACCEPTED**。候选 `6802628826dcc4b79a16ced20a8e26f7e5494a1b` 相对 `2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02` 只修改 `internal/domain/backup_configuration_upgrade_test.go`。限定接受历史夹具来源替换；没有发现阻断该 exact1 Source 接受的缺陷。

新鲜执行 `ActiveQueueRecovery`、`Frozen22ProgramLock`、`NativeCLI` 三项均 PASS，零 skip。四个负向运行分别缺记录、错记录 pin、错 DB pin、错行快照 pin，均 native1 且出现对应拒绝原因；这些 FAIL 原样保留，不能写成“全部命令成功”。独立只读检查实际 SQLite 快照及输入执行 22 个命名断言；现有八个丢表/历史连续性负向分支均对应非空表，不会因空夹具跳过。Go 本身未输出总断言数，不虚构总数。

已逐项核对冻结范围及作者最终引用链、502 个归档/源码文件、5922 个先前编译输入（495 个路径映射到重建根）、29 个本机程序/发布输入以及 helper/编译程序 hash。重建根唯一额外文件是 `active_queue_fixture_child_test.go`。历史 Git tree `458e375ec2be0b989bb9b9e3d487f969e3c62966` 仍缺失；该证据证明选定 502 文件归档的字节来源，不证明完整 Git tree checkout。

helper 经 `goalCommand` 解码、事务及实际旧版 `ClientService.Execute` 完成 1 次 goal.start、7 次 session.send、1 次 session.control；Run 经旧版公开任务 claim 路径生成，effect 经 Prepare/Begin/Observe API 进入 UNKNOWN。六个中间队列状态由 `appendClientReceipt + UPDATE` 合成；跨进程工作区由 Project/WorkspaceBinding 当前对象路径及 content_hash 重绑定。两者均是明确的夹具处理，不是 SDK/provider 真实阶段执行，也不是一般产品路径变更迁移的证明。没有注入 schema23 identities。

原库用 mode=ro 检查，schema min/max/count 为 1/22/22，identities 表不存在。七相位合成后，公开 CANCEL 将 ENQUEUED 改为 DROPPED，将 SENDING/SDK_ACCEPTED 改为 DROP_REQUESTED；所以最终旧库是 CONSUMED1/DROPPED2/DROP_REQUESTED3/UNKNOWN1。迁移后仍有七条相同 generation/sequence 队列记录，其中 UNKNOWN4；控制请求 RECONCILING1；Run 同 epoch、token 更换、lease 过期且 revision+1；effect 保留原三条历史并追加 UNKNOWN fence；idempotency 与 runtime_dispatches 保持逐行类型和值，零 dispatch；新 identities 表为空。原 DB/helper/record 字节不变。

环境 pin 的信任来自本次冻结范围，不来自任意调用者自填 hash。该 exact1 测试消费外部记录、DB、稳定工作区和旧/新程序；纯净 CI 环境尚无可移植性证明。后续集成必须提供本回执验证过的 artifact 集及相同受控 env，并保留缺资源明确失败。该条件不扩大成本轮 Main、打包或正式接受。

失败历史保持完整：作者 18 次尝试中 7 次失败、旧 T3 三项失败均保留。本审查第一次把最终队列误设为七种状态各一条，纠正前的检查失败已保留；原探索查询的路径/编码诊断也保留。整体 Main 守卫首次失败是 Root 同期 CP499→CP500 更新 HANDOFF/checkpoint/path_ownership 三文件，已用 Root before.raw 字节及回执归因；原 FAIL 不覆盖，其余17个脏文件、HEAD、空 index、Source/helper/DB 均不变。

本次临时目录 `.local/builds/historical22-independent-review-20261015` 的精确 PowerShell 清理被自动批准审查以 `blocked by policy` 拒绝，命令未执行，目录保留；未更换工具绕过。所有实际测试 argv/cwd/allowlist env/native exit/raw logs 与快照均在此回执目录，`evidence-manifest.json` 冻结文件 hash。

没有 Main 集成、原实际数据库迁移、package 接受、模型/provider 调用、stop/signature、旧 UNKNOWN Run 重放或正式增量。正式仍为 0/42，22 个父任务仍 OPEN。
'''
with (OUT/'review.md').open('x',encoding='utf-8') as f:f.write(md)
manifest={'schema':'researchos.historical22-independent-review-manifest.v1','verdict':'LIMITED_SOURCE_ACCEPTED','candidate_commit':review['candidate_commit'],'formal_increment':0,'files':[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='evidence-manifest.json']}
save('evidence-manifest.json',manifest)
print(json.dumps({'verdict':review['verdict'],'review':pin(OUT/'review.json'),'manifest':pin(OUT/'evidence-manifest.json'),'diagnostic_entries':len(diags)},ensure_ascii=False))
