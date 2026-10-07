# 一轮 UAC 前的最小可审查路线

当前 broker 可作为 synthetic service 安装准备；它没有正式评测实现。安装前审查通过不代表实际身份、文件权限、重启持久性或 A08/G04 通过。已有 60 条 development 真调用为 49 correct / 2 critical false accepts / 9 abstentions；每语言 30 条，正式 holdout 为 0。不得在开发用户 SID 下生成正式输入或标签。

1. 在同一服务中增加固定 evaluator，先冻结完整 qualification key、现有 0.8 阈值、模型/rubric/生成器/真值代码哈希、来源族排除表、一次性评测批次与调用预算。安装前只用明确公开的 synthetic fixtures 测接口，不能预生成正式数据。既有 60 个 development case 属于一个生成模板族；它的翻译、改数字、同义改写全部排除。新样本的来源性质如实写 GENERATED，不能宣称独立经验来源。
2. 由独立 Verifier 编写确定性生成器和真值判定代码。冻结代码后，仅安装后的 service SID 产生私有随机种子、正式输入与独立标签。标签不得来自候选输出、Jev 多数票或低置信转正；开发 root/worker、调优进程和普通 API 不能获得正式输入/标签/逐例哈希。
3. 服务内部承担真实官方调用、原始请求/响应封存、标签比较及 qualification 计算。原始响应、逐例详情、失败文本、日志、临时文件、重试记录均留在 service SID 私有存储。禁止把 Provider.Read 接回同用户控制面；禁止调用通用 shell 或接受调用方路径、URL、模型、阈值、命令。
4. 管道只允许冻结的一次性 start、有限状态与最终聚合。公开完整 key 级计数、固定失败原因枚举与 FAILED/ADVISORY；不公开逐例详情、可调查询、任意错误字符串或适应性反馈。每 key 开发不足 60、留出不足 30、严重误接受或其他合同门未过，资格失败；完整真实评测和正确安全降级可支持 A08 验收，不授予自动权限。
5. UAC 前把最终 binary、安装脚本、配置、全部哈希、固定 service SID/路径和凭据交付方式放入一个具体包。凭据只授权固定官方 endpoint 与有限预算，不放到仓库/命令行/公开日志；实现和验证 service 身份能够使用凭据且不会回传。当前 synthetic installer 无该功能，不能把它解释为已经完成。
6. 一次明确授权的管理员会话中安装最终包，先跑 synthetic canary 和控制服务重启；在非提权开发用户上下文核对实际读取/写入/改 ACL/改服务配置均拒绝。通过后才由服务自身生成与执行正式批次；若真实身份或任何泄漏门失败，正式批次不生成、不调用。仍须真实候选 AppContainer 的当例输入正对照、其他输入/标签/日志负对照及公开 API/缓存/事件不泄漏证据。评测结束只交付固定汇总和 FAILED 资格证明。

合同依据：`spec/v2.0/11_EVALUATION_AND_INTEGRATION.md`、`spec/v2.0/06_ACCEPTANCE_TESTS.md` A08/C22、`spec/v2.0/contracts/tasks.json` W11-G04。上述属于下一实现路线，不是本次已实现声明。
