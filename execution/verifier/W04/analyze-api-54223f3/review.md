# W04 analyzeChangeImpact 独立审查：PASS（仅 FIXTURE 开发门）

生产源码提交：`9e419e7361eb8b4586b7d9da637d8be90bc73d2f`。冻结证据 HEAD：`54223f3355baf267113f04a3cc139f2d2d7d0dec`。审查前后 worktree 均干净；六个改动文件的 Git blob 哈希与作者回执逐一一致，冻结规格树未变。

独立 overlay 的 **7 个顶层测试、40 个子例全部通过**，退出码 0；另定向重跑 W15 正式来源冲突解决回归，1 个测试及 7 条既有断言通过，退出码 0。未发现本切片的阻断缺陷。

## 已验证行为

- 普通 SETTLED、Task 为 EXECUTION_REPORTED 的 impact_review Run 可以提交精确绑定的封存报告。分析、独立接受、应用均经过真实 loopback HTTP，不要求先接受 Task。
- 确定性影响身份全部保留，额外 Artifact 及下游 Task 加入闭包；应用将下游置为 NEEDS_REVALIDATION。缺 key/ETag、旧 ETag、请求与报告向量不一致均拒绝，精确幂等重放一致。
- 八类报告或运行绑定攻击全部拒绝：错误 proposal/hash、向量错配、重复引用、未知字段、首次分析伪造前驱、错误 Task 类型、错误冻结输入。
- 跨项目、旧版本及受限引用全部拒绝；受限对象来自临时 CanaryStore 的真实登记。
- analyze/accept/apply 三个阶段均拒绝失效 executor grant/role、撤销或 LIVE 模式 runtime、变更 epoch/policy、STALE 报告。共 21 个 HTTP 拒绝；另 3 个 observation 篡改在不可变存储触发器处拒绝，未冒充后续 HTTP 检查。
- OPEN 冲突保持 OPEN，提案 BLOCKED，接受返回 409。另一个提案经独立接受和应用正式解决冲突后，新 Run 重新分析，旧语义影响不丢失，并能继续独立接受和应用。
- 续接后撤销旧 review executor，接受及应用均拒绝，证明会重查历史报告链。执行者和提案作者的两层别名不能自我接受；接受者 grant 被撤销后不能应用。
- W15 合法来源冲突解决、解决后证据可用性、技能采用及来源撤回阻断未回归。

## 范围

这是结构、来源绑定和状态控制的 FIXTURE 开发门通过，不接受任何新 formal case，不接受整个 W04，也不证明自然语言语义完整性或 LIVE 语义真值。测试创建过程复用仓库 fixture factory；独立断言及关键 HTTP 请求由外置 overlay 提供。所有故障注入仅发生在临时 SQLite，未访问生产数据、受保护服务或外部 provider。

闭包保留按实体身份验证，当前版本随正常生命周期重新计算；不要求保存已经过时的版本引用。原始响应、精确命令、退出码和来源哈希见同目录 JSON、stdout 及 `evidence-index.json`。
