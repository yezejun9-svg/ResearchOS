# ADR-004（编号续 ADR-001/002/003）：v2.4 唯一复用路线 = MU_FORK（Go 控制面保留）

状态：EXECUTION_REPORTED（W01-03），待独立 bootstrap 审查；不是产品验收。
日期：2026-10-01（Asia/Shanghai）。范围：W01 / 路线冻结。取代对 W01 的适用性：ADR-001 的 THIN_CORE 记录保留为历史，不删除。

## 决定

选定 **MU_FORK**：固定 Mu `8dfebe36508ac0c2508735bb866756dab9283e74`（内嵌 Pi 0.87.1 作为 RPC worker）+ 保留现有 Go/SQLite 控制面为唯一业务权威（项目、Goal/Task/Run、预算、租约、权限、验收、/2 协议）。Desktop 复用 Mu Electron 壳与 Native* 渲染组件，经 `NativeClientContext`（实际文件 `desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts`）注入 ResearchOS 适配。备选 PI_COMPOSE（合格 Pi + Craft 桌面壳 `73bd9c2a…`）**未触发**：Mu 路线资格未被观察到失败，按 19 §1/08 §3 不预先接线。

## 依据（G01–G07，当前版本证据）

- G01 需求覆盖：W01-02 实测双端共享一会话、真实模型读/改/测试、取消链与崩溃无孤儿（`execution/v2.4/receipts/W01/W01-02/results_attempt2.json`，critical_fail=0）。限定：writer epoch/去重/水位由 Node 资格 supervisor 仿真取证（ACCEPT_WITH_LIMITATIONS P1–P8 见 W01-02 independent_review），Go 权威接入是 W02+ 实施义务而非已完成。
- G02 许可：根 MIT、desktop Apache-2.0、AionUi 来源声明实存（W01-01 ACCEPTED）。
- G03 平台兼容：Windows 11 实机 clone→构建（npm ci+build exit0）→ rpc-entry 0.87.1 实跑→ DeepSeek provider 真实推理。
- G04 边界：研究 clone 非正式依赖；安装脚本零 approve；worker 只执行委派范围（19 §2 表）。
- G05 同输入对照：attempt1（失败输入=模型模式解析到 Cloudflare 目录）与 attempt2（唯一一次针对性修复=显式 set_model）差异定位到 provider 解析，机制断言两轮全绿，证明修复非偶然。
- G06 维护成本：上游锁文件自带 pin；Mu 桌面/CLI 入口清单实际路径已登记（source_candidates.json）；升级策略=按 commit 重放 W01-01/02 资格矩阵；回退=弃用 work/v24-continuation 候选分支回到其派生点 2b0f99f（不对 main 执行 reset/clean；main 上的 v2.4 台账提交保留）。
- G07 硬验收：42 例与 22 父任务不因此路线选择而豁免；W01-99 仍需实际资格通过。

## 已证实的规范缺口（CUSTOM_GAP，均有上游源码取证）

上游所采用的 RPC 路径无 writer lease/epoch（`packages/coding-agent/src` 中按大小写敏感全词 epoch/lease 零命中；`src/modes/rpc/` 无 owner/stale 字段；`core/session-manager.ts` appendFile 无锁，两 worker 并发追加同一会话文件不受保护。相邻机制不在采用路径上：CoordinatorStartupLease 与 experimental session-worker 的 lockfile 存在但属另一执行器路径，结论限定于 --mode rpc 采纳面）。writer_epoch、command 去重、事件水位与快照补齐属 **Go 控制面自有的最小缺口**，可复用上游惯用法：KyrnSettings.revision 的拒旧 CAS、Conversation.ts only-grows seq、`Session is already open` 单开语义。缺口范围以此处为界，不扩大为全栈自研。

## Jev 与 bootstrap

本路线判定由独立 bootstrap 审查推进（W01 不依赖未实现的 W11）。Jev 本卡**未调用**：NOT_RUN（缺 live Jev 服务不能伪造 reuse_selection 建议；ADVISORY 缺失不阻塞硬门）。W01-02 复核的后续义务登记见 `execution/v2.4/receipts/W01/W01-02/carry_forward_obligations.json`（W03-02/W05-02/W06-02/W13-01，含 P8 并发追加反例）。

## 后果

W02 按 MU_FORK 建立共享核心/CLI/Desktop 壳与登记（component_lock、patch_inventory、client_mapping）；正式门失败或真实 Mu 能力缺口出现时按 19 的路线切换纪律处理（一次定向修复→失败才验 PI_COMPOSE，保留证据）。
