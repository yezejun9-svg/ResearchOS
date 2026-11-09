# 18 · 从当前 ResearchOS 接续到 v2.4

版本：2.4.0；日期：2026-10-01。既有仓库是输入资产。本文件只规定下一次实施如何接续，本包编制没有修改该仓库、服务、数据库或旧回执。现场证据见 references/Repository_Baseline_2026-10-01.json。

## 1. 实际起点

授权候选根：D:/作品集/ResearchOS/research-os。永久身份从 execution/project_identity.json 实读，当前已观察为 aede0678-7308-43dc-b9f2-cfe3d90cfdfb。仓库规则仍指向 spec/v2.0，路线为 THIN_CORE：Go 控制面、SQLite、React 网页。它有领域、来源、评测、验收、恢复和 UI 资产，不是空项目；开发包启动及局部测试不能证明 v2.4 自有 CLI/Desktop 已完成。

W00 必须重新核对 HEAD、分支、全部 tracked/untracked 改动、worktree、永久身份、进程与写入归属。目录名改变不创建新身份。旧 agent owner/lease 只是历史登记，不能不经核对就继承写入权或清除正在运行的工作。

## 2. 接续动作顺序

1. 冻结现场：记录 git status --porcelain、git rev-parse HEAD、git worktree list --porcelain 及目标文件 hash；记录修改路径，不复制密钥内容。
2. 比对新包 manifest。将完整 v2.4 只读快照复制到候选仓库 spec/v2.4；spec/v2.0 和旧 execution 回执不改。已有同名快照且 hash 不同立即报告冲突，不原地覆盖。
3. 为本轮创建隔离分支/worktree；实际路径由当前授权根派生并实读验证。已有 dirty 内容先登记和保护，不用 reset、clean、stash-all 或 git add .。不把隔离分支误称为新业务项目。
4. 按 docs/adr 现有编号续写一个迁移 ADR。说明现状、保留/适配/淘汰映射、新控制权、数据迁移与失败返回路径；先通过独立工程审查，再改本候选分支的 AGENTS 入口到 spec/v2.4。用户本次要求完善规格不代表本包编制已批准任何产品阶段。
5. 新施工记录写 execution/v2.4；execution/project_identity.json 保持永久身份。创建输入 hash 绑定的 step_state/checkpoint 和 execution/v2.4/current_spec.json 指针。新版 route/path_ownership/commands 保存在 execution/v2.4；旧根登记保持历史。已有 execution/command_dispatcher/dispatch.py 可以在候选分支内扩展为按 current_spec 选择新登记，默认无有效指针仍按旧行为；不能修改旧登记内容伪称历史更新。旧 bootstrap_ledger 保留，允许关联证据，不批量把旧状态复制为 ACCEPTED。
6. W01 按当前能力缺口资格验证 Mu 优先路线。不能为了迁移先删除 Go/React，不能把老 Paperclip 失败回执当作 Mu 失败证据。新来源、新输入具有新的资格记录，但不是重试已经被拒绝的同一操作。

## 3. 默认保留/适配矩阵

| 现场资产 | v2.4 默认处置 | 需要重新验证的边界 |
|---|---|---|
| execution/project_identity.json、Git 历史、只读 spec/v2.0 | 保留身份与来源；新规格另存 | 路径/身份真实性、版本指针、读权限 |
| internal/domain、internal/store、migrations/sqlite | 优先保留业务状态与接受事务 | 新 Session/客户端映射、迁移事务、旧输入兼容 |
| apps/control、internal/api、调度/预算/接受逻辑 | 默认继续作为唯一业务权威 | Node Agent worker 接入、取消、事件、鉴权与协议 /2 |
| adapters、apps/worker、现有源码/评测能力 | 逐能力复用已通过且输入一致的部分 | 指定运行器版本、工具权限、真实执行，不继承另一模型资格 |
| apps/web 的领域页面和设计 token | 抽取到 Mu Desktop 渲染层或窄客户端适配 | 原 HTTP/事件接入改为统一客户端；不另做第二主界面 |
| Mu CLI/Agent/NativeHost/Desktop | 固定源码后适配为 CLI/worker/Desktop | 前端 NativeClientContext、单会话写入归属、工具批准/取消 |
| 旧 checkpoint、receipts、verifier 索引 | 保留为 HISTORICAL_EVIDENCE；按断言映射 | 当前 hash、输入、模型、环境、UI/安装包是否仍匹配 |
| 旧开发 ZIP、正在使用的数据根、受保护服务 | 原样保留，仅作历史/回退来源 | 不因新 Goal 自动迁移、停止、替换或签发新凭据 |

新架构中的共享核心是一个逻辑控制边界，可以包含 Go 宿主和受控 Node worker。Go 负责项目、Goal/Task/Run、预算、租约、权限和最终接受；Mu/Pi worker 负责一次委派的模型/工具循环。CLI/Desktop 只通过相同协议发指令。Mu 内部 Goal 自动续跑/独立调度必须禁用或映射到 Go 的原有 Goal，不能同时拥有第二个 READY 队列。

保留上游会话记录的原始格式和来源，以稳定 ID/hash 与 Go Session 索引绑定；谁可写、何时封存、重放水位必须只有一处定义。禁止两个活客户端各起一个可写 Agent，也禁止把一份上游数据库和一份 Go 数据库同时当作业务真值。

## 4. 数据与凭据迁移

默认只对新候选数据根和经授权取得的备份副本演练。源码迁移不等于稳定数据库切换授权。先验证备份可恢复，再运行连续编号迁移、行数/引用/对象 hash 校验、恢复对账和失败回退。迁移失败不得把 schema_version 写成成功，不原地降级唯一数据库。

测试矩阵至少含：空库、已观察旧 schema 版本副本、目标版、损坏备份、缺对象、旧 token/密钥后端不可用。权限秘密不从个人 profile 或别的业务项目复制。旧 token 不当作长期桌面登录凭据；本机身份绑定与短会话签发由受保护宿主处理。

当前历史记录含受规则拒绝的 CLI/实例启用动作。v2.4 文档、换模型、换候选编号都不能清除该拒绝。若后续仍需要对应动作，记录原拒绝及受支持恢复条件；不改名、换脚本或借另一执行器绕过。旧现场具体 PID/端口不能当活身份，操作前核对实际进程、启动时间、数据根和 lease。

## 5. 旧证据复用规则

为每一条旧断言登记 disposition：REUSE_UNCHANGED、REVALIDATE_CHANGED、HISTORICAL_ONLY 或 NOT_APPLICABLE_WITH_REASON。REUSE_UNCHANGED 必须有输入/代码/产物/环境一致证据及独立复核，不能只比较文件名或旧 PASS 字样。旧网页截图不覆盖新的原生Desktop安装包；旧协议 /1 不覆盖 /2；不同 model/provider/rubric 不共享 Jev 自动资格。

v2.4 仍有 42 个父用例，但追加了 U01–U09 及 typed protocol 断言。新断言一律从 NOT_RUN 开始。没有变化且证据仍有效的检查不全量重跑；受影响的检查不可省略。证据索引记录旧 receipt 引用与新复核结论，不回写历史时间或原接受者。

## 6. 退出与交付

资格路线失败可回到未修改的旧开发代码/数据；这只表示回退到已知局限，不表示旧版符合 v2.4。发布前 W18 必须完成独立恢复资格，W16 才能晋升系统代码。正式切换只通过既有授权与受支持流程；无法完成的 live 门维持 BLOCKED，同时继续无依赖支路。

本文件不新增长期数据库、第二套业务完成总账或额外产品审批页。execution/v2.4 是施工证据命名空间；产品事实仍由现有领域服务维护。
