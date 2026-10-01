# ResearchOS

本仓库是独立 ResearchOS 产品，中文沟通。用户授权实现 `spec/v2.0/08_AGENT_EXECUTION_GOAL.md`，按难度选择子 Agent 模型。不得读取或继承其他业务项目的私有配置、身份、代码或部署。

## 唯一执行基线

- `spec/v2.0/`：原实施包逐字节只读快照；保留只读，不得修改初始状态或验收阈值。
- `spec/v2.4/`：v2.4 实施包逐字节只读快照（manifest 4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964）；当前任务卡、验收门与施工命名空间 `execution/v2.4/` 以 v2.4 为准；A01/A12 等历史映射见 docs/adr/ADR-next-v24-continuation.md。
- `execution/project_identity.json`：永久项目身份。`execution/bootstrap_ledger.json`：施工状态，独立于产品业务状态。
- `execution/receipts/`：实际命令与产物回执；`execution/verifier/`：仅独立 Verifier 写入的施工审查。
- v2.4 逐卡循环：每回合在 `spec/v2.4` 内运行 `python tools/task_packet.py next --state <仓库根>/execution/v2.4/step_state.json` 选择当前卡；施工状态、检查点与回执只写 `execution/v2.4/**`；执行者不签自己的接受。
- `execution/checkpoint.json`：旧版续跑入口。按 `spec/v2.0/contracts/tasks.json` DAG，先核对 Git、身份、输入版本及有效回执。
- `bootstrap/`：开工导入与验证工具。W02 再由平台 owner 登记实际产品目录和命令。
- `.local/`：本仓库生成的工具、进程数据与可重建缓存，不入 Git；不得放正式唯一证据。

## 执行约束

默认最多 2 个活跃施工任务；使用独立 worktree 和唯一 owner/lease。共享合同、锁文件、路由和命令登记串行整合。主 Agent 负责整合与真实验证；执行者不签发自身接受回执。只读审查可使用当前仓库，不能把同用户的不同 Agent 当作受保护留出隔离。

模型策略：架构、安全、独立验收优先 `gpt-6-astra` 高推理；边界清晰的非平凡实现和施工复核用 `gpt-6-sol` 高推理；简单、低风险、可机械核验的独立工作用 `gpt-6-luna`。记录实际选择与理由，不创建用户侧新聊天，除非用户明确要求。

保留既有修改；不用 reset/clean 或 git add .。允许本地原子提交，不自动 push、部署、购买、充值或对外发消息。规格校验、开发夹具、真实服务和产品正式验收分开记录；未实现和零断言不得 PASS。只对新变化和未解决疑点补验。临时文件完成后删除，证据/检查点保留。
