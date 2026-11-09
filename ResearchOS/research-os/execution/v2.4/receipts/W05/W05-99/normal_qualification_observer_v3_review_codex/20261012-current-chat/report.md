# Observer V3 独立审查

结论：**APPROVE_ROOT_READONLY_HELPER_SCOPE**。V2 的 OBSV2-R1 / R2 两个 P1 和 OBSV2-R3 P2 在本次冻结 V3 中已修复，本轮未发现该受控只读收集范围内的新阻断。该结论支持 Root 使用此 helper 收集当前原请求/Run 证据，不能据此宣布真实资格验证或产品正式验收通过。

D 正式 manifest `06ee2e6504439bde03b1ebc238db5847221bbd0025df8b74ace94750bc3c5c7c` 中12个成员，与 C 原冻结目录全部按字节核对一致；`observe.py` SHA256 为 `ee8d210fc092847c921623924bb68b8fc7b2534a44c99691d6ab9cfede765959`。Go oracle 的 canonical/jcs.go 与项目原文件一致。本审查未修改 Root helper 或 Canon。

| 检查 | 独立结果 |
| --- | --- |
| 原请求及 consume JSON BLOB | 限定 body/plan/manifest/identity JSON 列严格 UTF-8 解码，保留原字节大小及 SHA；未知 binary 列只输出摘要。合法 BLOB 和 TEXT 都能读取，非法 UTF-8 拒绝。 |
| 请求摘要 | 17字段、16string + 1 bounded integer 的固定 ASCII-key 子集，生成带 sha256: 前缀的 canonical digest；原存储字节 hash 单列。字段逆序、缩进、escaped Unicode 和 raw 非canonical JSON 不会误判。原始字节 hash 冒充产品 canonical hash 正确拒绝。 |
| Go 对照 | 实际运行冻结 Go oracle：作者 ASCII/Unicode/escaping 三组及独立复杂组合一组均一致。这里只证明合法 producer request 的固定标量子集，不宣称通用 JCS/任意 JSON 验证器。 |
| Run 串联 | 原 request、唯一 consume、RunRef type/id/revision、qualification task/runtime/owner/plan/profile、唯一实际 Run body id/project/task/runtime/epoch/context、Task active_run_id 均有检查。相关错绑、缺失、bool/future revision 反例均拒绝。 |
| Goal 和预算祖先 | 精确 Task.goal_id → Goal.budget_policy_id → GOAL/PROJECT/GLOBAL，scope/project/parent/cycle 检查有效；preconfirm PAUSED 拒绝，已 consume 后 PAUSED/CANCELLED 可回顾。 |
| 只读约束 | 独立调用的连接守卫只允许 C 盘当前 fixture 的 mode=ro URI；query_only 检查存在；实测 SQL trace 仅 SELECT、PRAGMA、BEGIN、ROLLBACK；全部 fixture 前后哈希相同。 |
| 敏感字段 | Run 的 lease_token_hash 不在结果中；fixture secret sentinel 与未知 binary sentinel 均未出现在输出。没有 credential-table 查询。该检查不等于为未来任意资源正文提供通用脱敏保证。 |

本轮实际执行作者9个受控数据库用例（3合法、6拒绝）及3个真实 Go oracle 对照；另独立23个数据库用例（4合法、19拒绝）及1个真实 Go oracle 对照，均符合预期。32个数据库用例和4次 oracle 比较分别统计；其中作者用例为重跑，不作为新增正式产品用例。独立 trace、结果与数据库均在本 C 盘目录封存。

保持的使用边界：未来生效的预算版本会明确拒绝，未实现从 domain_versions 查找历史有效祖先；本 observer 要求 Task 仍指向该原 Run，不能当任意旧 Run 查询器。请求剩余秒数仅被记录，Root 必须根据该值判断当前 PREPARE 是否仍有效，不能因 collector exit0 自动认为可 CONFIRM。Run snapshot 可以合法包含不同空白/字段顺序，Run 引用 revision 只要求不超过当前持久化 revision；不把当前 mutable Run JSON 的原始 hash 当不可变请求 hash。

没有执行 launcher、正常 Electron、Core、worker 或 verifier。`Popen.wait` 的既有设计只涉及 Electron，本轮没有产生任何真实进程退出观察。private management stdout frames、native verifier stderr、native verifier numeric wait 仍为 missing，不能从 SQLite 行或空日志补造。没有访问原数据库或真实密钥，没有 API、外部网络、模型或工具执行请求；正式接受增量为0。

正式归档目标由 Root 指定为 `execution/v2.4/receipts/W05/W05-99/normal_qualification_observer_v3_review_codex/20261012-current-chat`。当前提供已封存的 C 盘证据供 Root mirror；本轮 D 写入为0，未清理任何被阻止删除的缓存目录。
