# 阶段二 v2：事务内验证服务根持续有效

候选 `68a34150abab24c4e7edc49d166bf540c47cc42d`，父提交为原冻结候选 `c9e47c6cd16946ac02a874422a894249f87c6c50`。隔离 worktree：`D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-qualification-repair-v2-20261012`。本次仅 7 个文件改变，原包、原独审反例、Main、Canon 及失败记录均未改写。

本候选落实 `W05-QUALIFICATION-ROOT-REVOCATION-001` 修复，并已通过本地 source/fixture 验证，等待新非作者独审。原独审 `final-decision-v2.json` 的 REQUEST_CHANGES 仍是原 c9 候选的有效结论，其 SHA256 为 `f475716b0ee1b74a0e7360ce80dfe419fdbbf330b677a634df4856dea313f1b2`。本包不自行替代该独审结论。

## 权威边界修复

新增只读 `currentAuthorityRoot(tx, id)`，所有读取使用调用者当前事务，检查 principal 活性、完整显式 parent/root 链的存在、活性、无环性与根一致性。原有根字符串独立性比较仍保留；此检查不赋予任何角色或项目/task/run grant。

Task acceptance 的准备及最终提交都通过原有 `acceptanceSnapshot` 重读当前根；资格验收同时校验原计划 author 的当前根。`qualificationEvidence` 对 verifier、executor、author、调用者逐一复查，因而原 `/qualify`、`currentRuntimeAdmission` 和 `AuthorizeRuntimePurpose` 使用同一事务中的新鲜活性事实。目的授权者及已有 purpose grant 的 Owner 也复查其根。没有通过 Host 事后撤销 AVAILABLE 来掩盖已写入的验收。

现有未登记的直接 principal 保持原有语义，但必须真实存在且未撤销。已登记的链一旦进入检查，缺少父或根登记不能退回直接身份。新 managed verifier 在原受信管理 provenance 事务内写入私有 lineage anchor，绑定原 child/root/project/Owner；之后即使登记行损坏丢失或整条根被换掉也拒绝，不能把它当旧 direct identity。

Anchor 复用既有 idempotency 存储，不扩公开 API/schema。固定 operation 是 `host:managed-verifier-lineage`，principal/key 均为管理端验证过的 child，project 是当前 OWNER 已授权的项目；不读取客户端提供的 idempotency key。完整 body hash 绑定 namespace/actor/scope，已有值不一致或多重 scope anchor 均拒绝，不覆盖旧记录。Anchor 不含 token，不授予权限；真实安装、image/PID/start time/nonce、显式服务根、私有凭据传输和撤销证据仍按原阶段二流程检查。

## 最终提交上的验证

`attempt06-frozen-domain-regression.txt` 覆盖旧 direct/registered delegated 身份、所有原资格 root/profile/budget/capability gates、窄 executor grant、原 UNKNOWN/null 验证和旧 bounded Mu verifier、独立 native acceptance，以及新根活性/损坏身份/最终事务检查。`attempt07-frozen-actual-service-root-revocation.txt` 使用最终提交构建的实际 verifier.exe、真实 Host 和 Mu AppContainer，所有模型响应来自隔离 httptest synthetic SSE。

| 撤销点 | 原 receipt | 原 runtime | 新目的授权与后续会话 admission |
| --- | --- | --- | --- |
| child POST acceptance 之前 | 未产生 | REGISTERED | 拒绝 |
| acceptance 之后、qualify 之前 | 原件保留 | REGISTERED | 拒绝 |
| AVAILABLE 之后、purpose 之前 | 原件保留 | AVAILABLE 历史事实保留 | 拒绝 |
| 已有 purpose 之后、普通会话之前 | 原件与 grant 保留 | AVAILABLE 历史事实保留 | 拒绝 |

四个反例各仅产生原资格的 1 次 synthetic 请求，未产生新的运行；原 UNKNOWN/null ledger 保留、临时 verifier token 撤销。正常 positive 流程仍为 2 次 synthetic 请求，完成 qualification、purpose 和普通会话 SETTLED。所有测试真实/付费/外部模型调用为 0。

另一个定向测试先完成 prepare 的确定性 PASS，再撤销根或移除 child grant，最终 acceptance 事务都拒绝且未写 receipt。根上即使有完整项目 grant，也不能替代 child 自己已移除的 grant。

## 原失败与限制

原 c9 的两个独立 root 撤销反例完整保留。本包 `attempt02` 首轮损坏身份夹具撞上现有 immutable/durable identity triggers，原始失败保留。`attempt03` 只在一次性测试数据库中显式停用相关存储 guards 来构造缺行/漂移状态，验证读侧 fail-closed；生产迁移、触发器、外键均未修改。真实根撤销反例使用原 `RevokePrincipal` API，不停用任何 guard。

本结果只证明 Source 与明确的本地 synthetic/native 测试。没有实际 Ollama 资格、Desktop privileged producer 完整交互、protected holdout、正式父任务或 Main24 验收。旧 UNKNOWN/bounded 核验实现文件未改；原 source manifest 仍为 `4614b44b8ff3657cc14cac4efa2642e2b87bdbf46a76ea276a9fb37a9344a023`。

两个最终二进制的实际 SHA 和 `go version -m` 来源记录在 manifest 与 `build-provenance.txt`，都应为本候选提交且 `vcs.modified=false`。冻结包包含本次 7 文件 delta 与阶段二累计 20 文件的完整哈希，便于按旧接受事实和本次修复分别审查。
