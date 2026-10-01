# ADR-003（编号续 ADR-001/ADR-002）：v2.4 现场接续与施工迁移

状态：EXECUTION_REPORTED（W00-02），待独立复核；不是产品验收。
日期：2026-10-01（Asia/Shanghai）。范围：W00 接续动作（18 §2）。宿主：Qoder 桌面端 Agent。

## 背景与现状

既有仓库 `D:/作品集/ResearchOS/research-os` 携带 spec/v2.0 时代完整施工成果：HEAD 2b0f99f，永久身份 aede0678-7308-43dc-b9f2-cfe3d90cfdfb，Go 控制面/SQLite/React 资产、execution/ 台账、81 个 worktree、acceptance_status 中 FIXTURE 模式的历史接受记录。v2.4 包（manifest 4666920727e1…、execution.plan a6669dd94b16…）验证 errors=[]。v2.4 的产品门（22 父任务、42 正式用例）在 v2.4 口径下均 NOT_STARTED/NOT_RUN；历史 PASS 不追认。

## 决定

1. 接续不重建：保留项目身份、Git 历史、spec/v2.0 只读快照与全部旧 execution 回执；旧回执登记为 HISTORICAL_EVIDENCE，按 18 §5 逐断言映射（REUSE_UNCHANGED 需输入/代码/产物/环境一致证据加独立复核，默认只引用不复制状态）。
2. v2.4 规格冻结为本候选分支的 `spec/v2.4/` 只读快照（147 文件逐一 sha256 与 manifest 一致；快照内运行 validate_package.py PASS；嵌套自复制目录与 PACKAGE_VALIDATION.json 生成物不属于清单范围，已从快照剔除；规格包源目录保持不动）。
3. 施工迁移记录写入 `execution/v2.4/`（step_state/checkpoint/inventory/receipts，绑定 plan_sha256 与 spec manifest hash）；`execution/v2.4/current_spec.json` 指针指向 v2.4 快照。旧根登记（route/path_ownership/commands/checkpoint/bootstrap_ledger）保持原字节，command_dispatcher 后续按 current_spec 选择登记，默认无有效指针仍按旧行为。
4. 本卡改动全部落在候选分支 `work/v24-continuation`（worktree `.local/worktrees/v24-continuation`），主根 working tree 不写入产品代码；AGENTS.md 在候选分支的入口更新在独立复核通过后执行，指向 spec/v2.4 并声明 v2.4 施工命名空间。
5. 保留/适配/退休映射（18 §3 为默认，逐条以 v2.4 卡片实测为准）：
   - 保留：project_identity、Git 历史、spec/v2.0、internal/domain、internal/store、migrations/sqlite、apps/control 唯一业务权威（调度/预算/接受事务）、旧证据。
   - 适配：apps/web 页面与 token 抽取到 v2.4 Desktop 渲染层；旧协议 /1 不覆盖 /2；旧 FIXTURE 接受按断言重新映射；command_dispatcher 扩展版本选择。
   - 待资格验证（不预设结论）：Mu 固定组合（8dfebe36508ac0…）优先、Pi+Craft 备选 —— 由 W01 实测；旧 Paperclip 拒绝仅覆盖该候选该用途，不迁移为 Mu 失败证据。
   - 退休：无。不删除 Go/React/SQLite 资产；淘汰决定须另立 ADR。
6. 回退路径：本候选分支可整枝弃用，主根与旧证据字节不变即回退成功；施工检查点失败计数（同输入重试≤2、无进展 3 轮延期）跨窗口/换规格保留。18 §4 记录的受规则拒绝动作（CLI/实例启用）不因换 v2.4、换模型或换编号而清除；旧 PID/同名路径不构成活身份；无授权项目继续 NOT_AUTHORIZED。
7. 数据与凭据：本卡不迁移任何数据根、不动 .local/secrets、不签发凭据；后续迁移演练按 18 §4 只对新数据根/授权备份副本执行。

## 后果

W01 起在候选分支上以 v2.4 卡序推进；v2.4 正式用例全部从 NOT_RUN 起，由各自 -99 卡等待父任务完整前置。历史成果作为输入资产与回退基线受到保护，不构成任何当前接受声明。
