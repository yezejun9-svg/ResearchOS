# W11-02：逐用途资格资源报告

结论：`BLOCKED`。本次完成逐键公开汇总审计和本地拒绝反例，没有完成新的真实资格评测，也没有签收 W11-02/A08。自动权限始终为 `NONE`；既有 SHADOW/ADVISORY 与 domain 接受门未修改。

`adapters/decision/qualification_audit.go` 是供报告使用的数值/来源条件检查器。它读取一个完整用途键的汇总，不持有调用或验收能力。即使输入条件全部满足，其结果也仅为 `REVIEWABLE / ADVISORY / NONE`。输入中的来源声明不能证明独立身份；真实服务能力仍来自既有 SCM/PID/二进制绑定查询及独立 domain 接受链。

## 实际观察

- 2026-10-05T19:52:50Z，已安装 broker 的 `--aggregate` 返回 1 / `CANARY_BROKER_UNAVAILABLE`；`sc.exe query ResearchOSVerifierCanary` 返回 STOPPED。
- 2026-10-05T19:56:06Z，主执行者尝试启动同一个已安装服务，`sc.exe start` 返回 5 / Access is denied，随后仍为 STOPPED。原因是 `OS_SERVICE_CONTROL_PERMISSION`，不是凭据缺失或平台自动审批拒绝。
- 启动失败后没有再次启动/停止/探测服务。本卡默认命令读取并校验固定的公开观察回执，标记 `RECORDED_LIVE_WINDOWS_READINESS_NOT_NEW_MEASUREMENT`。只有显式运行 probe 的 `--refresh-aggregate` 才会再次执行只读 IPC；本轮未执行该选项。
- 未读取 formal holdout 输入、标签、逐例结果、私有日志或凭据；没有重置单次运行标记，没有新 provider 推断。费用未知保留 `null`。

## 每用途输入与指标

旧公开归档的 SHA-256 为 `22b5f70744cec75c825ed865dba56bd79ff27b3022a07f78811ed28e5ee04d8a`。以下指标来自 2026-09-30 完成的既有真实运行，**不是本轮新测量**。完整旧键为 `evidence-validity × language × typesafe × jev-1.13.0 × objective-source-records-v1`。

| 用途/语言 | 开发/留出 | 误放/关键误放/误拒 | 接受/拒绝/弃权 | 留出平均耗时 | 实际费用 | 当前意义 |
|---|---:|---:|---:|---:|---|---|
| evidence-validity / zh | 30 / 15 | 0 / 0 / 0 | 1 / 5 / 9 | 1008.8 ms | null | 旧初轮评测；键样本不足，不能晋升 |
| evidence-validity / zh-en | 30 / 15 | 0 / 0 / 0 | 2 / 5 / 8 | 1041.4 ms | null | 旧初轮评测；键样本不足，不能晋升 |
| reuse_selection / zh | 未登记 | 未运行 | 未运行 | null | null | 单独 provider 授权、model/rubric、开发/留出均未冻结 |
| reuse_selection / zh-en | 未登记 | 未运行 | 未运行 | null | null | 同上；不能借用 evidence-validity |

旧两键各有 8 个负标签，误放/留出与误放/负标签均为 0；弃权率分别为 60% 与 53.33%，接受覆盖率为 6.67% 与 13.33%。旧开发集结果另保留在机器报告中，不混入留出分母。旧初轮总体 60+30 可用于失败评测与安全降级，不能拼成任意完整键的 60+30 自动资格。

`reuse_selection` 必须分别具有许可、平台、接入可行性、收益、README/证据不足、README 注入、超时、弃权及跨用途借资格的覆盖。本轮 37 项断言验证的是缺这些证据时报告拒绝，以及数字/来源伪装的拒绝；并未执行这些反例的真实 provider 评测。

## 生产链差距与所需资源

现有 `ImportFrozenQualifications → prepareQualification → acceptQualification → recordQualificationResult` 链继续存在。`FrozenProvider.Read` 不允许施工者读取标签正文是预期边界；并非资格链不可用。

现有 `frozen_summary.go` 固定为 evidence-validity 两语言、各 30+15、FAILED/ADVISORY，`evaluation/holdout/jev/rubric.go` 也固定此用途。本次未扩展受保护服务、私有数据生成、评测 rubric 或 domain 准入格式；这些共享生产路径需先由 owner 登记范围并审查，再对新用途接入，不能让本报告成为新的授予入口。

资源请求：

1. 恢复读取旧汇总：需要具备本机服务控制权限的操作员仅启动既有 `ResearchOSVerifierCanary`，随后通过已绑定客户端读取 `aggregate`；不得执行 `start-frozen-run`、替换二进制、重设凭据或删除 marker。仅恢复服务不补齐 reuse_selection 资格。
2. 新用途 provider：在调用前冻结 endpoint、用途/语言、model_revision、rubric_revision、样本 ID/输入 hash、请求数量与最大预算，并得到本次授权。目前具体新预算与授权未建立，凭据状态为 `NOT_PROBED`；不能借 W14 的未对账调用继续收费。
3. 独立标签：每个申请键至少 60 条开发、30 条未见且来源族隔离的 holdout，标签来自可追溯人工或客观重算；两种语言均申请时至少各自 90 条。正式标签继续由独立受保护服务持有，不放候选目录，不能用 12 smoke、模型投票、开发集或旧调优留出替代。

## 验证与入口

精确入口 `tests/jev/w1102_check.py` 只接受 `RESEARCHOS_TASK_ID=W11`、`RESEARCHOS_CHECK_ID=W11-02`、空 CASE_ID，无参数；旧 selectors 被拒绝，旧 registry 保持原 handler。主执行者负责登记 v2.4 的 `test.jev.live`。该入口的整体正常结果是 exit 2 / BLOCKED，局部 fixture PASS 不改整卡结论。

最终本地检查回执：`execution/v2.4/receipts/W11/W11-02/dispatched/f06daedf-1fbf-4489-b868-64322058ab72/report.json`，37/37 严格断言通过。初次 35 项版本及实际只读 IPC 回执保留在 `cc07a710-de8c-49fe-b9d8-84be80e14748`，已被最终源码覆盖的测试版本不作为当前结果。

`regression-20261006/report.json` 中的 7 个定向回归全部通过：typed adapter、transport、单次执行/不泄露进度、summary authority 拒绝、冻结资格导入、trusted admission 和 drift 拒绝。它们全部是 FIXTURE，不是新 LIVE 资格。`selector-rejection-20261006/report.json` 证明旧 W11-G02 selector 在 Go/provider 操作前被拒绝。

执行者仅提交可复查产物；独立验收仍待其他身份完成。

## 最终增量：非有限费用与旧入口兼容

当前报告与资源结论见同目录 `resources_round2.json`。上文 35/37 项回执及旧 selector 拒绝属于变更前的历史版本；原始文件保留。当前资格审计为 40 项，新增 NaN、正无穷、负无穷费用的拒绝，并将不可编码费用输出为 `null`。另外 12 项仅使用替身子进程验证转发，不计入资格样本或上述 40 项。

AUTO dispatcher 按 command key 选择 v2.4 registry；因此当前 wrapper 将 W11-G02/G03/G04、A08 和旧空 selector 默认路径转交未修改、固定 hash 的旧 handler，保留原参数、环境、输出、退出码及历史评测语义。W11-02 仍只接受空 case、无参数；混合或未知 selector 拒绝。旧 selector 拒绝回执不再代表当前行为。本轮没有实际运行旧 admission，没有服务刷新或 provider 调用。

初轮真实评测的基线是每用途整体至少 60 开发与 30 独立留出，两种语言的留出各至少 15；只有**申请自动化资格**的完整键才分别要求 60/30。旧 evidence-validity 的 30/15 语言键不足以授予自动化资格，但不否定其完整失败评测与 ADVISORY 降级的有效性。当前整卡 BLOCKED 的依据是 reuse_selection 的真实调用、独立标签和本次 provider 授权未建立，以及服务控制权限受限；不是要求旧语言键为了安全降级交付而晋升。
