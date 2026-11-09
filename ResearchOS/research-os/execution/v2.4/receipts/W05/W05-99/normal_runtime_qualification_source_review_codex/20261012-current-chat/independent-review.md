# 阶段二 Source 独立审查：REQUEST_CHANGES

候选 `c9e47c6cd16946ac02a874422a894249f87c6c50` 有 1 项 P1，需要新候选修复后复审。

## P1：服务根撤销后仍可签发资格

`internal/host/runtime_qualification_windows.go:160-182` 在原服务根检查之后直接给 verifier child 发短凭证，并在其接受结果后授权 `mu_turn`。服务器认证只检查 child；接受、资格与用途检查仅比较 root ID，没有检查该服务根仍未撤销。

独立反例在实际 verifier `POST /acceptances` 前撤销服务根，确认只改动 1 个根身份；实际 Host、Mu/AppContainer、独立 exe 仍返回 `QUALIFIED_PURPOSE_AUTHORIZED`，包含服务器 AcceptanceReceipt 和 AVAILABLE runtime。两次复现各 synthetic SSE 1 次，真实模型 0 次。原始失败见 `root-counterexample.stdout`、`root-confirmed.stdout`。同位置撤销 child 则正确拒绝。

建议把受管 verifier child 与安装服务根绑定，并在服务器接受快照、qualify、purpose/current admission 的事务中检查根仍有效；仅补 Host 前置检查不能封住并发撤销。复审需覆盖接受前、qualify/purpose 前及后续使用时的根撤销。

## 有效的局部证据

34 项源码/Git/冻结回执/实际 exe metadata 绑定检查通过；domain 18 父+43 子、verifier 2 父+9 子、Host 正向链 1 项、独立拒绝反例 2 项均通过，0 SKIP。原生 UNKNOWN 禁止重试与凭证头回归通过；旧 RESERVE 路径保留。阶段一合法窄 grant 重用问题已在资格与普通 Mu run 后的实际续检中关闭。

额外拒绝反例证明：child 撤销、预算策略更新时间漂移后，PASS/AVAILABLE 均为 0，Verifier 短凭证撤销，原 UNKNOWN/null 保留，重复请求不新增模型派发。

本审查不授予 LIVE runtime 资格，不推进 W05/Main24、Main、Canon 或正式接受。Desktop privileged producer 和实际 Ollama 资格仍未验证。原冻结包及失败历史未改；测试缓存保留。
