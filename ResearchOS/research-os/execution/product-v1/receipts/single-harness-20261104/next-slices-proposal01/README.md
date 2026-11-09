# 下一产品切片提案（未施工）

优先实施 **S05a：隔离候选→一次 Codex 实现→固定检查→成果 diff**。Pi S07 保留为后续支路，遵守计划中的 S05/S06 前置依赖。这两个 JSON 是 C-only 提案，不是 source lease、测试通过或真实资格。

- `s05-candidate-proposal.json`：完整纵切、13 个后端生产路径和 5 个测试路径、独立薄客户端范围、Root rev3 所需字段、dirty 保护和真实验收。
- `pi-s07-proposal.json`：安装版 Pi 0.99.2 静态协议事实、11 个生产路径和 5 个测试路径、取消/重启语义及后续真实验收。
- `PROPOSAL-MANIFEST.json`：提案文件与本轮实际读取的公共源码/文档 pins。它仅绑定本次规划输入，不代表生产 source freeze。

S05 复用现有 Host/Coordinator/Run/lease/idempotency/outbox/ArtifactUse，不增加调度器、DB 或迁移。原树只读；baseline 是授权范围当前实际 bytes，包含原有 dirty。候选 diff 不采用 HEAD/INDEX diff，成果不回写原树。失败检查保留候选与完整原始输出，UNKNOWN 不自动重派。新 check runner 只负责固定命令的 owned Job 生命周期，不负责模型循环。

下一步是 Root 冻结 opt-in candidate wire revision 与精确 lease，然后在新 registered worktree 实现同 Core 的 fake 纵切及 fresh 目录反例。真实 Windows candidate-write allow/deny、原生实现、检查及停止应另行登记执行；Job 不是文件系统隔离，编译检查不是测试 PASS。Pi 的 auth/provider/model 仍未验证，不是 S05 的前置资源。

本轮只读取当前 Main 公共源码、计划与安装版 Pi 公共 docs/dist/package 元数据，并写此 C 包。没有 D 源码写入、构建、CLI/SDK 启动、模型、认证配置读取、安装、旧 DB 或旧探测重放。历史失败与旧 frozen 包未修改。
