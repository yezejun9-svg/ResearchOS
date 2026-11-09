# Mu M0 V6 独立差异复核 — FINAL

结论：**SOURCE_FIXTURE_ACCEPTED（仅有限 M0 源码与合成夹具接受）**。V5-J/K/L 已在冻结 V6 中修复；旧 M/N 安全控制、旧 checkpoint 阶段、工具效果和队列消费回归仍通过。本轮没有新增阻断项。

冻结 manifest：`9e5dd1e5d93f19c6a4aa5eb5c0e2ebd7f0d1e05a987f6ec03963b4b560139da9`。精确 9 源、作者 2134 个实际编译输入、15 个冻结 bundles、101 个冻结文件均已核验。本轮独立从 V6 candidate 源新编译 13 个 bundles，追踪 2132 个实际输入（与作者差异来自复核 fixture 集合）；未使用 installed agent SDK 或旧 V5 bundle。前后源 hash 无漂移；V5 manifest 的 157 个成员全部保持原样。见 [source-provenance-final.json](source-provenance-final.json)、[freeze-audit-after.json](freeze-audit-after.json)。

## 已解决问题

| 原问题 | V6 变化与独立证据 |
|---|---|
| J / P1 类型标识强转绕过 | agent.ts:278 先要求 string，再检查 literal，switch default 拒绝；三类 message 的原数组反例全部拒绝。validate/export/restore、stopReason/sampling 控制通过。 |
| K / P1 继承字段绕过闭合 schema | agent.ts:377、429、434 使用 own-property 查询；constructor/__proto__/toString 及普通未知字段全部拒绝，合法登记字段仍通过。 |
| L / P2 旧绑定阻断合法后续阶段 | agent.ts:1748 的阶段 guard 保留旧身份；agent-loop.ts:435–501 在可信 prepareNextTurn/prepareRequest 后明确提交新绑定。原 L 两类恢复与无暂停序列一致，加强 N5 最终成功。 |

模型登记签名在构造时固定，工具登记同时固定签名及函数引用；提交新阶段先校验旧身份，再解析已登记的新身份。每次模型/工具 dispatch 仍检查。没有通过清空 guard、信任篡改后重算签名或开放整个工具 registry 换取通过。

## 实际验证

| 独立运行 | 结果 |
|---|---|
| 实际 V6 源 + 原 reviewer 回归 | 67/67 PASS，exit 0 |
| 新阶段边界 P/Q/R | 3/3 PASS，exit 0 |
| 原 Agent 回归 | 40/40 PASS，exit 0 |
| 合成 worker 协议 | 2/2 PASS，exit 0 |
| 定向 tsgo | exit 0 |

旧 V5-J/K/L/M/N 与 strengthened-N5 fixture 按原字节复制、新编译运行。M 的四种异步 mutation 仍拦截；N 只执行 allowed 工具、excluded 返回错误。N5 同实例和新实例恢复均到达最终 done 回复，调用数 2、无 error、两项效果及结果 ID 恰好一次、延迟 custom context 恰好一次、队列为空。

新增 P 验证合法下一阶段再次暂停并第三实例恢复：模型序列 initial/next/next，3 次调用、工具效果及结果各一次、原始 user 一次、prepares=2、finishes=3、最终回复完成。Q 在 prepareRequest 中尝试篡改当前/下一模型、下一工具元数据和同 toString 的替换函数，4/4 在下一 dispatch 前拒绝且无工具效果。R 在新阶段提交后通过 transform/convert/getApiKey 异步篡改新模型，3/3 拒绝且调用数维持 1。见 [v6-phase-boundary.stdout.txt](v6-phase-boundary.stdout.txt)。

## 保留限制

原未登记 custom fixture 的 7/10、三项失败仍保留于作者冻结包；没有改写为通过。全仓 tsgo 的 exit 2 和模型目录/依赖类型错误也保留，不能宣称全仓类型通过。exact9 Biome 为作者冻结 exit 0 证据，本轮只核验，不执行写入格式化。详见 [historical-limits-reference.json](historical-limits-reference.json)。

本轮依据 Root 明确提供的 dispatch 元数据记录 gpt-6-astra/high。结论仅覆盖本次 same9 M0 源码修复与合成夹具；没有安装 SDK、生产 M1/M2、真实 provider/外部工具调用或手机验收。正式增量 0，仍为 0/42，22 父任务全部 open。后续集成与真实资格验证须单独记录，不能把此结论晋升为产品正式接受。
