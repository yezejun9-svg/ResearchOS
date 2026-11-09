# W16 独立审查（源码 881e42e）

结论：整体范围 PARTIAL；W16-G02=PASS_IN_FIXTURE_SCOPE，其冻结门防篡改、自证拒绝、退化与版本断言均有证据，不要求在此 gate 完成 LIVE 控制面。11 条编号 fixture 断言均有源码与原始证据支持；C09/C10/C12 可按 fixture 范围接受。C20 的三条编号断言通过，但合同还要求“冻结 holdout 结果”，现有只有公开冻结算术套件，且原始回执明记 formal_holdout=NOT_RUN，因此完整 C20 保留 PARTIAL_EVIDENCE。不得接受整个 W16。

独立执行 3 个顶层 Go 测试、5 个子测试，全部通过；其中包含真实 native 正常收益/有界试用，C10 权限攻击和 C12 退化回滚。5 条真实 loopback HTTP 负向请求、6 项原始记录篡改、4 项 runner 非法选择均正确拒绝。19 份 raw 与 136 份源码哈希一致；另从原始输出重算 6 份回归、3 份 canary，校验执行/验收 receipt hash、同输入、独立进程、启动错误/超时及恢复 inventory。

未复现 P1/P2 安全漏洞。C20 为合同证据缺口，不是漏洞。正式 A16 仍只到 PARTIAL_FIXTURE_ONLY；隔离 SQLite 恢复和旧 binary 健康检查不能证明生产服务切换、独立 OS supervisor 或宿主崩溃恢复。W14 LIVE、W15、W18 的上游状态不由本审查解除；W16-G01/G03 与生产接线均不接受。

完整断言映射、范围及可复现命令见 review.json、command-receipt.json 和 probes_test.go。冻结 worktree 保持干净，只新增本 verifier 目录。所有运行时临时目录由 Go fixture 清理；overlay 和 probe 保留用于复现。
