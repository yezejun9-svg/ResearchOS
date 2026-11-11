# ResearchOS

## 开发目录迁移入口

本分支是可克隆的开发目录。先读 `README.md` 与 `docs/DEVELOPMENT_HANDOFF.md`，使用 `node scripts/dev.mjs` 安装依赖、检查和构建。当前续跑事实以 `execution/product-v1/state.json` revision 92 和 `execution/v2.4/checkpoint.json` revision 694 为迁移时快照；后续修改仍应核对当前文件。

完整 v2.4 冻结规格位于 `spec/v2.4/`。旧 `execution/checkpoint.json` 及下方 v2.0 入口描述属于历史基线。历史回执中的旧电脑路径、HEAD 和工具 hash 按原文保留，不可在新机器直接重放登记命令或据此继承 PASS。普通开发可直接修改源码并运行开发检查；正式验收需要另做环境绑定与独立复核，失败计数不得重置。详细历史证据见 `docs/migration/ARCHIVE.md` 指向的固定备份。

本仓库是独立 ResearchOS 产品，中文沟通。用户授权实现 `spec/v2.0/08_AGENT_EXECUTION_GOAL.md`，按难度选择子 Agent 模型。不得读取或继承其他业务项目的私有配置、身份、代码或部署。

## 唯一执行基线

- `spec/v2.0/`：原实施包逐字节只读快照；不得修改初始状态或验收阈值。
- `execution/project_identity.json`：永久项目身份。`execution/bootstrap_ledger.json`：施工状态，独立于产品业务状态。
- `execution/receipts/`：实际命令与产物回执；`execution/verifier/`：仅独立 Verifier 写入的施工审查。
- `execution/checkpoint.json`：续跑入口。按 `spec/v2.0/contracts/tasks.json` DAG，先核对 Git、身份、输入版本及有效回执。
- `bootstrap/`：开工导入与验证工具。W02 再由平台 owner 登记实际产品目录和命令。
- `.local/`：本仓库生成的工具、进程数据与可重建缓存，不入 Git；不得放正式唯一证据。

## 执行约束

默认最多 2 个活跃施工任务；使用独立 worktree 和唯一 owner/lease。共享合同、锁文件、路由和命令登记串行整合。主 Agent 负责整合与真实验证；执行者不签发自身接受回执。只读审查可使用当前仓库，不能把同用户的不同 Agent 当作受保护留出隔离。

模型策略：架构、安全、独立验收优先 `gpt-6-astra` 高推理；边界清晰的非平凡实现和施工复核用 `gpt-6-sol` 高推理；简单、低风险、可机械核验的独立工作用 `gpt-6-luna`。记录实际选择与理由，不创建用户侧新聊天，除非用户明确要求。

保留既有修改；不用 reset/clean 或 git add .。允许本地原子提交，不自动 push、部署、购买、充值或对外发消息。规格校验、开发夹具、真实服务和产品正式验收分开记录；未实现和零断言不得 PASS。只对新变化和未解决疑点补验。临时文件完成后删除，证据/检查点保留。
