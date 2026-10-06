# W13 C26 recovery — PARTIAL execution handoff

结论：SSE 静默失联修复已形成可审查产品代码，并有两次实际浏览器超时 / 水位补齐证据；正常空闲心跳、既有重放和投影相关观察可按相同产品哈希复用。完整 C26、真实浏览器冻结恢复和 physical OS sleep 均未接受。五次 runner 原始退出码全部为 `1 / FAIL`，不得将其中已执行通过的子检查扩写成整轮 PASS。

独立审查：`PENDING`，交 evolution_verifier。施工者不签发自身接受。`execution/commands.json` 未修改，`test.ui.recovery` 仍未正式绑定。真实 SOURCE、activation、旧 native / private helper、电脑睡眠与手机均未执行。

## 源码与范围

- 分支 `work/ui-recovery-c26`；初始 base `2406cc1`，先合并登记，再合并主线 `27ced22` 的相邻非 UI 产品更新。
- 产品提交 `4d3654b`：`apps/web/src/api.js` 固定 45 秒无流数据超时（服务端原有 15 秒 heartbeat）；中止、取消并释放读取器。`apps/web/src/hooks.js` 恢复页面或检测到超过 20 秒墙钟停顿后，先使旧连接失效，再读取当前项目快照。回调与旧快照均受连接 signal 保护。
- 心跳只更新传输内部时间，不增加业务 refresh / sequence / 进度计数；打开连接也不把 lastSync 改写为收到业务数据的时间。原有 API / 后端协议与依赖保持不变。
- 后续 `5478445`、`dce7b06`、`e234960`、`1150137` 均为测试调整；产品两文件从 `4d3654b` 到最终源码 `11501378b116663a9652c82058809a7fba76553d` 字节一致，且与全部五份 runner `before.json` 匹配。
- 新入口 `python ops/ci/ui.py --phase recovery` 有固定 11 项 expected；`--scenario freshness` 有固定 5 项，只验证剩余静默 / 恢复分支。它是测试子集选择器，不是放宽正式 C26 条件的选项。
- 只在 helper 增加 recovery 分支及可选跨项目目标；原 contracts / core 预期含义保留，未运行完整页面 / 状态矩阵。原 core 的 I1 第三条 expected 文案漂移未在此修复。

## 原始执行记录（全部保留）

| 源码 HEAD | 场景 | registered 目录 | browser 目录 | 原始结果与边界 |
| --- | --- | --- | --- | --- |
| `4d3654b` | all | `2cb59b38-ea80-4964-b29a-147d5f29ea3e` | `c266dfa447a049b895341c1e7a8577df` | exit 1；6 条检查已完成；旧 helper 读取事件第一页，未读到较高水位新事件。 |
| `5478445` | all | `809d1cb5-0dd6-4865-9ed5-be67c58a5718` | `78b668c25d2c41d599c1cca1d8541eb2` | exit 1；前 8 条已完成；新测试错误地等待 UI 中不存在的内部“45 秒”文案，实际 UI 使用通用断线提示。 |
| `dce7b06` | all | `2796e4df-dd2d-43a3-ba60-2989d2e605d4` | `f1565ba8fecb40348f980d598e702ccc` | exit 1；6 条已完成；旧 helper 固定等待 5 秒后仅观察到两次连接，第三次连接未到达。 |
| `e234960` | freshness | `27792778-5369-41da-91a4-268decbe3530` | `6ddd6c6a975d450e8cbe81f30312e0ce` | exit 1；登录、项目建立、静默恢复 3 条已完成；等待冻结后的 abort 计数超时，缺现场生命周期记录。 |
| `1150137` | freshness | `6f7aa1e2-eb3b-4555-b727-6e60045c5a7d` | `a1cf4f7592fe4cf387c46c929de845a1` | exit 1；同 3 条已完成；诊断证实 CDP 请求期间页面没有实际冻结，停止此 fixture 分支。 |

以上 registered / browser 路径均相对此目录。每个 registered 目录保留 `before.json`（实际运行 HEAD、源码清单、dirty 库存）、`commands.json`、原始 build / browser stdout / stderr 和 `report.json`；browser 目录保留未改写的报告、服务日志及当时产生的截图。`manifest.json` 另区分产品 / 测试源码及所有原始文件哈希。

## 可复用和新增的具体观察

第二轮前 8 条 raw 检查不是整个 runner PASS：其中登录、实际项目建立、4/6→4/9 计划计数及旧投影拒绝、通知五次及逆序重放零额外业务写入、精确成果链、重复 / foreign / gap / 410 / offline / 跨项目隔离、正常 idle heartbeat 可在相同产品字节范围复用。其旧“actual Chromium freeze”措辞必须降级为“发送 CDP frozen / active 请求后水位追上”，该旧 helper 没有证明计时器真的暂停。

正常 idle 证据：第二轮连续 47 秒，实际服务端 heartbeat 收到 3 次，连接数 `1→1`、GET 查询数 `28→28`，进度文本不变。不存在每次 heartbeat 重查全页的观察。

两次新静默证据均为显式注入单条无 EOF / 无 heartbeat 的 ReadableStream，浏览器保持 online，服务端真实产生新 Requirement；未修改产品超时配置：

| browser 目录 | 实测中止耗时 | 显示的 lastSync 已旧 | 服务器 / UI 水位 |
| --- | --- | --- | --- |
| `6ddd6c6a975d450e8cbe81f30312e0ce` | 45,009 ms | 46,220 ms | 1 → 2，重新获取快照后吻合 |
| `a1cf4f7592fe4cf387c46c929de845a1` | 45,009 ms | 46,229 ms | 1 → 2，重新获取快照后吻合 |

两轮均记录 aborted / lateBytes 各为 1，显示通用断线、状态可能过期和最后同步时间，保存 `silent-stream-stale.png`。第一张截图已人工查看，提示与旧水位可见。此观察限定于受控浏览器流故障，不能扩写成真实网络设备断电、操作系统休眠或正式产品验收。

## 冻结 fixture 失败与停止依据

第二次 freshness 的 `resume_observation` 保留了冻结前、CDP active 后及等待后的计数。22 秒区间内 5 秒 timer 继续运行，`lifecycle=[]`、`visibility=visible`、`aborted=1`，因此实际冻结预条件不成立；不能用 CDP 返回成功证明冻结，更不能据此判断产品 resume 已通过或失败。

只读源码排查发现，本机 Playwright `crPage.js` 初始化主 frame 会在自身 CDP session 开启 focus emulation。Chromium 官方实现中，启用 focus emulation 会持有 `stay_hidden=false` 的 capturer，而冻结路径依赖页面隐藏。该机制是本次预条件失败的源码解释，未通过修改 Playwright 私有对象或新 native helper 验证或绕过。参考 [Chromium Page handler](https://github.com/chromium/chromium/blob/main/content/browser/devtools/protocol/page_handler.cc) 与 [Emulation handler](https://github.com/chromium/chromium/blob/main/content/browser/devtools/protocol/emulation_handler.cc)；这些上游源码解释不替代本机原始 timer 证据。

按 root 指令停止该支路，没有第三次 freshness 尝试、第四次全 recovery 或任何 OS sleep 操作。产品恢复代码可供静态独立审查，但同项目旧连接晚到隔离、真实计时器停顿后的新快照恢复仍未由该 fixture 完成。最终源码中将旧 event_recovery 固定 5 秒改为最多 15 秒等待实际第三次连接；此测试调整本轮运行资格明确 `NOT_RUN`，不覆盖第三轮 FAIL。

## 复现入口与资格

使用 `execution/toolchains/locked.json` 中的工具；`RESEARCHOS_TASK_ID=W13`、`RESEARCHOS_CASE_ID=C26`、`GOENV=off`、`GOTOOLCHAIN=local`，Go 可由 `RESEARCHOS_GO` 指向同仓已锁工具。Node 从 locked.json 读取；测试源码已移除默认硬编码开发者 Go 路径。新 WT 的 node_modules junction 复用同仓依赖，没有重新安装或更改锁文件。

两个入口均可执行、expected 非空、原始输出可追踪，但本次没有任一整轮 exit 0。`--scenario freshness` 不包括已有完整计划 / 通知 / 事件矩阵和 47 秒 idle；最终 composite 只列已观测子断言，保留所有 FAIL、未运行与降级边界。`full_phase_after_final_test_change=NOT_RUN`，`formal_C26=NOT_ACCEPTED`，`physical_os_sleep=false`，`physical_phone=false`，`independent_acceptance=PENDING`。

## 收尾

五轮 runner 已结束并执行自身 finally，源码没有未提交修改；原始浏览器证据按回执保留。新建 dependency junction 保留供复现。

本轮两个 Python 缓存目录的收尾删除被自动审批以 `blocked by policy` 拒绝；整条命令未执行，没有重试或替换删除方式。`tests/ui/__pycache__`（5 个文件）与 `ops/ci/__pycache__`（1 个文件）保留为 ignored 缓存，不入提交。此限制单独记录，不伪报完整清理。
