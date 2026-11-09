# Source58 signing boundary

指定的**现有只读事实字段**是 source15 review/public authority/CLI2 qualification 的 `/source_acceptance`（目前全false），以及CLI2 `/whole58_test_suite_qualified`（false）。这些不可变原件不能改成新的签署。

所读合同没有提供 `source.accept` 命令，也没有已冻结的 Source58 全suite accepting consumer。`task_packet.py:186–200` 只有list/show/next，输出read_only与product_acceptance NOT_ASSERTED；它不签收。要设置新source接受语义，Root还须固定新不可变签署合同及真实consumer，然后非作者在同一E2/58输入上提交签署，Root再串行登记。这一缺口不能用字段存在来掩盖。

**已经固定的施工/父回执入口字段**：

- step_state：schema_version1.0/package_version2.4.0/plan_sha256；steps[].id/status/executor_id/verifier_id/evidence[].path+sha256。ACCEPTED须不同真实身份、非空当前hash evidence及所有依赖卡接受；evidence为状态目录下安全相对路径。`task_packet.py:124–166` 仅验证结构/hash，不认证身份，不接受产品。
- W05父receipt：task_id, run_id, project_id, owner_role, executor_identity, verifier_identity, base_revision, input_manifest_hash, rubric_revision, artifact_manifest_hash, route_revision, code_revision, changed_paths, verification_results, open_blockers, resource_request_ids, side_effects, rollback_reference, next_action, started_at, ended_at, receipt_hash。
- verification_results各项：command_key, registered_command_revision, actual_invocation_reference, mode, status, started_at, ended_at, exit_code, assertion_ids, artifact_versions, stdout_reference, stderr_reference, raw_evidence_references。
- GLOBAL_EVIDENCE_V1：case/run/mode/OS时间/独立身份、code/spec/lock/input版本、actual command argv/cwd/rawstdoutstderr、全部 assertion 原证据locator+SHA、独立 acceptance 基线/索引/结论。

新source58 signature的最小绑定提案保存于 [signing-map.json](signing-map.json)，明确未被Root采用；不写未来hash/路径/权限。Source接受、W05父门/A04、W13 GUI与formal、发行A15和Goal全验收是分别签署的对象，不能从某一签署推导其它层。

W05-99前置：W05-01, W05-02, W05-03, W02-99, W03-99, W04-99；只拥有A04。C11/C15最终owner W12。W13拥有C17/C18/C23/C24/C25/C26，模式FIXTURE；W20 A15 LIVE_WINDOWS。P02/C01协议fixture在W06，真正双端P06/A13在W14，发行件在W20；无需以尚未实现的后置live门阻塞无关前置切片。
