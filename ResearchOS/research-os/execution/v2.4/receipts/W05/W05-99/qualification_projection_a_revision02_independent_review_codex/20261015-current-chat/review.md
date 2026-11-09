# A-r2 独立 Source 审查：LIMITED_SOURCE_ACCEPTED

候选 `f48fca0e4013bda19913a34d91da0cd23157a08b`，tree `16e72ccf939c13142091495458ad04348a3ba660`；r2 基于 `525a9c923a8761a9491070123de3c94aa5618d71`，整个 A 基于 Main `4f4023c956f84d65743f39ce77d6c8899a21ada1`。

此前 F01–F03 已在本次 Source 范围内关闭，未发现新的可操作阻断问题。结论仅允许后续按冻结候选整合/继续相关 Source 工作，不是 Main、安装包、实际运行或正式验收。

## 修复与实测

- F01：native-offline/model=none 在 model_config 读取前分流，仍拒绝已存在 marker；原先 candidate525 失败的 `TestRuntimeCoordinatorNativeQualification` 在 f48 独立执行通过。纯 policy 也验证普通 native-offline 不变、Mu 缺失配置不回退。
- F02：adapter 使用 UseNumber，每个 mutation 先验证未修改 clone 有效，再单独改变字段。30 个 marker/authority case 通过 validation 与 StartBridge，重算外层 manifest hash，拒绝时不创建 native launch 目录。
- F03：共享 21 marker + 9 authority 变化覆盖 stage、adapter、Host preprepare/pretransport、verifier 与 cost；brokerEffect/cost 的真实函数入口均有未改首行 seed 正对照。反例不能触达 provider、新 effect 或改变原账本。Host provider identity 始终使用 original8/4，投影只用于 effective1/0。

作者176节点选择已独立重跑，另单独运行未被该选择覆盖的 `TestRuntimeMuVerificationRejectsFabrication`（含30矩阵与normal/legacy8/4快照）和旧 drain/UNKNOWN 回归。具体节点数见 test-summary.json，不能把 subtest 数写成动态断言数。独立 build 原生退出0。

## 夹具真实性与边界

TEMP BEFORE INSERT RAISE(IGNORE) 只在新建的隔离数据库中捕获 Begin 将产生的 dispatch，随后删除 TEMP trigger/table，首次 INSERT 一次带正确 manifest_hash 的 dispatch；没有改写历史 immutable dispatch。cost 测试在首次 dispatch INSERT 前构造合成 append-only PREPARED/STARTED/CONFIRMED effect 与 UNKNOWN ledger，正反例使用相同 seed 流程；这证明成本谓词，不证明历史或实际 native 闭合。

旧 marker 缺失配置经真实 legacy brokerEffect 发往 loopback，普通模式的8/4 wire 经直接 brokerModel 发往 loopback；verifier 的普通/legacy8/4是合成快照。完整普通 Mu session 旧基线失败仍未证明通过，未重复无关失败，也未将上述有界证明冒充完整会话。实际冻结 worker 的投影与 hostile tool_calls 回归仍在独立176选择中执行；只证明一次 MODEL、无 coding tool 暴露/TOOL effects，不签发 B 终态闭合。

## 冻结与诊断

已逐项核对58条作者 command/raw 记录、10个r2文件、scope与manifest输入hash；整个 A 的15路径另用完整 Git diff 审查。作者名为 `r2-full-diff-from-4f.binary.patch` 的文件仅含10个r2路径，不能当全部15路径；本审查使用 full-A-diff.raw，不改冻结作者件。

作者9次原生失败、9项只读命令capture gap与1项recipe parser gap保持；原A22条formatter恢复、早期raw缺失和原patch被覆盖的限制保留，不补称历史日志已捕获。审查自身首次scope读取发生在runner创建前，原始输出只在tool记录；另有一次runner显示阶段UTF-8解码失败，子命令已成功捕获raw，后续以独立UTF-8记录纠正；两者在 diagnostic-audit.json 明示。

候选源码/tree/index保持；Main20项既有dirty和空index保持，允许Root3共享文件CAS变化并逐hash记录；冻结SDK bundle不变。没有写实际产品数据、配置、安装包或执行模型/Ollama/Core stop。formal增量0，全部22父任务保持开放。此前policy拒绝清理的旧目录没有重试。

独立计数：176 = 20顶层 + 156子测试，3 package PASS；补充67 = 3顶层 + 64子测试，1 package PASS；均零fail/skip。

本轮新建A-r2临时目录的一次清理命令在启动前被自动策略拒绝，构建/缓存保留；没有尝试绕过，也未触碰此前A-r1被拒绝目录。recipe与policy结果已单独记录。
