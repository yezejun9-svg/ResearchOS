# ResearchOS 开发交接

本目录用于继续修改和构建当前源码。历史施工状态、失败计数和验收结果保留原值；迁移本身不产生产品验收，也不恢复已消费的任务。完整历史材料保存在固定备份提交，日常 checkout 不携带旧工作树、重复快照、全部日志或依赖缓存。

## 从哪里继续

先读 [产品 V1 方案](product-v1/PLAN.md)、[当前 V1 状态](../execution/product-v1/state.json)、[CP694 续跑记录](../execution/product-v1/receipts/single-harness-20261104/progress-cp694/RESUME.json)，再看 [V1 接口与施工合同](../execution/product-v1/contracts/)。原 `execution/checkpoint.json` 是 v2.0 历史入口；当前 V1 进展以 `execution/product-v1/state.json` 和 `execution/v2.4/checkpoint.json` 为准。

迁移读取到的状态如下，不代表新机器已重新完成这些检查：

| 项目 | 保留的状态 |
| --- | --- |
| 当前施工检查点 | CP694，`IN_PROGRESS` |
| V1 状态版本 | revision 92，`RECONNECTED_READONLY_AUDIT_PASS_NEW_BUILD14_REGISTERED_NOT_EXECUTED` |
| 原 Main 源码提交 | `360c3eefd06ba82255352357c05ece00dae00d3a` |
| 原 Main tree | `19cfb02ef2044eb7b5475302d4ded6ff1569d66e` |
| 当前源文件集合 | 70 个文件；union SHA256 `954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2` |
| V1 用户旅程 | 0/13 接受 |
| 旧正式验收 | 0/42；`needs_rederive_after_source_change=true` |
| 最新构建登记 | build14 已登记；CP694 尚未记录执行结果 |
| 源码 owner | CP694 记录无活跃源码 owner；23 个已整合范围仍标记未完成真实资格验证 |

复制时重新核对了 build14 登记中的 70 个源码 SHA256，均与原 Main 文件一致。新仓库的 Git commit/tree 会变化；上面的提交标识保留为来源，不是新仓库的 HEAD。

旧失败链、重试次数、UNKNOWN 和已消费 scope 不清零。CP694 的 `real_model_requests=2` 单位是已确认的 Host 任务提交数，不是已确认推理次数。原真实任务失败和停止记录见 [CP685](../execution/product-v1/receipts/single-harness-20261104/progress-cp685/RESUME.json) 与 [原任务清理复核](../execution/product-v1/receipts/single-harness-20261104/native-synthetic-flow01-final-cleanup-review/REVIEW.json)。

## 规格的新位置

[spec/v2.0](../spec/v2.0/) 保留完整冻结包。冻结 v2.4 从原候选分支 `work/v24-continuation:spec/v2.4` 提取到 [spec/v2.4](../spec/v2.4/)，包括合同、执行计划、任务卡、工具、示例和清单；原包内容不因迁移修改。

`execution/v2.4/current_spec.json` 仍保留历史定位 `.local/worktrees/v24-continuation/spec/v2.4`，其他历史记录也可能指向原机器的绝对规格目录。继续阅读规格和普通源码开发应使用本仓库 `spec/v2.4/`。这份定位说明不改写原凭据，也不让旧正式命令自动适用于新环境。

## 普通开发入口

使用 [scripts/dev.mjs](../scripts/dev.mjs)，其路径从当前仓库推导。要求 Node.js 24 或更新版本，Go 版本以 `go.mod` 为准；当前为 Go 1.27.1。Windows 原生检查与构建要求 Windows x64。需要时通过 `GO_BINARY` 指定本机 Go 可执行文件。

```powershell
node scripts/dev.mjs help
node scripts/dev.mjs doctor
node scripts/dev.mjs setup
node scripts/dev.mjs check
node scripts/dev.mjs build
```

`setup` 下载 Go modules 并按 lock 安装 web 依赖；`check` 编译入口并运行所列本地测试；`build` 把 Core、CLI、verifier 和 React 资源写到 `.local/dev/`。这些结果不登记正式验收。`web` 只启动本机 Vite UI 服务，后端 API 需要另外配置 Core；`setup-desktop` 只安装锁定的 Electron 依赖，不组装或启动完整 Desktop。

保留的运行与构建输入包括 `spec/v2.0/contracts/`、全部 `migrations/sqlite/`、源码中的嵌入合同、包清单和锁文件、Mu vendored source 与来源清单。Go cache、`node_modules` 和 Electron runtime 需要在目标机器准备。

## 旧构建与正式验收的边界

历史 dispatcher、command registry、toolchain lock 和正式证据读取器会检查真实 cwd、工具绝对路径及 SHA256、规格和计划 hash、源文件 hash、Git 来源及回执。普通 coding 使用新的开发入口；不要为了让旧命令运行而改掉历史回执中的路径、SHA 或失败结果。需要恢复正式流程时，应为新环境登记新的路径和工具绑定，检查新输入与旧证据的适用性，执行所需验证并由独立审查者确认。源代码可编译、fixture 成功或迁移完成都不能自行写成正式 PASS。

[build14 原登记](../execution/product-v1/receipts/single-harness-20261104/build14-scope/registration.json) 仍指向原 `.local/worktrees/product-v1-build-14-20261105` 和 `C:\Users\yqyyds\Documents\Codex\2026-11-04\task\...`。CP694 要求先核对原 `runs/product-v1-build-14` 的 CONSUMED/RESULT；这些外部状态不会因 clone 自动存在。缺少原记录不能推断该 scope 未执行，也不能在新机器重放原 Task 或已消费 scope。

原 `apps/desktop/build-development.py` 是有来源校验的完整 Desktop 构建流程：依赖锁定工具、Mu 构建输入、离线依赖以及 Git common directory。启用 qualification-helper 选项还会核对原 helper 的绝对路径、固定 hash、源文件与原构建回执。保留 [native-helper-build01](../execution/product-v1/receipts/single-harness-20261104/native-helper-build01/) 的来源记录，不表示新机器已经拥有该 helper 或真实资格。后续完整 Desktop、真实 Harness、界面、停止/恢复和安装验证分别记录结果。

## 历史证据在哪里

已公开的历史归档固定到 GitHub commit [`55931878579daebe47af21fbc2c18a31b9f6a032`](https://github.com/yezejun9-svg/ResearchOS/commit/55931878579daebe47af21fbc2c18a31b9f6a032)，对应 `backup/researchos-20261109` 的备份快照。引用历史证据使用下面的固定提交链接，避免分支后续移动影响定位：

- [原 ResearchOS 源码与执行资料](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os)
- [原 v2.4 详细回执](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os/execution/v2.4/receipts)
- [原 V1 详细回执](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os/execution/product-v1/receipts)
- [原 v2.0 独立验收记录](https://github.com/yezejun9-svg/ResearchOS/tree/55931878579daebe47af21fbc2c18a31b9f6a032/ResearchOS/research-os/execution/verifier)

当前 checkout 选留最新续跑记录、build14 源文件登记与准备审查、`state.json` 引用的 23 份源码审查结论、原失败任务的停止复核和 helper 构建来源。大量 `*.before.json`、重复源码快照、原始日志和截图留在归档；它们未被重新签发或删除。需要核实某项历史结论时，按原路径取回相应材料并核对 hash。只有结论文件而缺少其完整依赖时，不能宣称已在当前 checkout 重现该验收。

本次选留的 40 份补充证据均按原相对路径复制并核对源/目标 SHA256。宿主迁移记录位于 `.researchos-migration-20261109/development-20261111/resume-copied.json`；它是迁移过程记录，不是产品验收回执。
