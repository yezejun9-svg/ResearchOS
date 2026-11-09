# P1b 后续实施评估（设计建议，不签发实现接受）

建议先并行做 **双 NSIS 介质 + 纯安装计划/owner/journal 模型**。它们可消费已冻结 P1a，避开 chooser 正在改的入口文件；只能称源码/构建准备。首次安装、启动、升级和卸载的完整用户交付仍需要稳定维护门、事务恢复和 chooser 生命周期闭合。`69f91b72` 与既有封卷不改，正式增量 0。

可直接交给独立 owner 的首阶段为下述 **11 个新文件**（media 5 + plan/journal/ownership 及测试 6），交付两个真正由 makensis 编译、携带完整 payload/finalizer 的 `.exe`，以及被工具使用并有测试的计划/状态组件。不能仅交计划 JSON、预存 marker 或手工 copy 后称安装完成。gate 缺失时，已有安装/差异 payload/保留数据支路明确返回 `UPGRADE_REQUIRES_MAINTENANCE`，在修改前拒绝；这不取消后续升级和保数据卸载义务。首阶段只编译和静态/纯测试，不以缺事务支持的分支报告安装成功。

| 用户实际路径 | 最小完整行为与完成条件 |
|---|---|
| 首次安装 | 普通用户运行 Desktop 或 CLI 介质；同一完整 payload，默认 `%LOCALAPPDATA%\Programs\ResearchOS`，业务根 `%LOCALAPPDATA%\ResearchOS`。先确认授权父链并 create-new，验证 staging，进入最终根后才 finalizer；之后核对 identity、记录 ownership、登记入口。根不存在是合法新装状态；保留数据已存在则进入恢复/升级判断。helper 失败不能显示安装成功。 |
| 位置绑定与启动 | marker/verifier 只绑定最终根，定稿后不得再移动。Desktop 入口使用精确引用的 Electron、`apps/desktop` 和工作目录；CLI 使用同根 `bin/researchos.exe`，当前架构不能只发单 exe。两媒体共一个安装 ID、数据根、Core 与 HKCU 卸载登记。CLI 可直接通过 bin PATH 使用，无需为包装再加 `.cmd`；PATH 生效需新终端时给提示及可复制路径。实际通过 chooser 取消/选择、同 project/session、Safe Exit→重开保留数据后才接受启动路径。 |
| 第二媒体/重装 | 完全同 payload、来源、固定根只补缺失且仍属本安装器的入口，不改 ID/数据。`2.4.0` 相同但 payload 不同仍是升级，不能按 DisplayVersion 跳过。 |
| 升级 | 首个支持分支限定为明确兼容的 schema24 old/new payload、协议和 migration inventory，且没有历史 verifier 注册或未完成 replacement journal。安全退出后快照 data/profile/CLI 配置，副本迁移与 binding 更新，受维护门保护交换，事务专用启动验证，再 COMMITTED；失败保留旧可启动配对，无法确认新进程退出则 NEEDS_RECOVERY。历史 verifier/C57 或跨 schema 在写前阻断；该分支不是“所有非空升级完成”。 |
| 卸载保数据 | 同样排除活动使用，只删 path/hash/owner 仍匹配的产品和入口；未知/修改文件留下，空目录才删除。PATH 只移除自己新增且仍可识别的项，不恢复整串旧值。完整保留业务根、外部项目与恢复记录。保留数据重装须核对旧 binding，不能删 binding 伪装新装。 |

可现在并行提出施工范围的是：新增 `ops/release/product_installer/media.py`、`nsis/researchos.nsi`、`nsis/ResearchOS.ico`、`tests/release/product_installer_media_test.py`、发行说明；以及 `internal/installation/{plan,journal,ownership}.go` 和纯单元测试。两介质必须固定同一 payload/helper hash、输出各自 sha256/来源/许可/锁文件，NSIS 检查每阶段退出码。helper、卸载器和 journal 放在产品 inventory 外，分别受 ownership/hash 约束。稳定管理目录建议 `%LOCALAPPDATA%\ResearchOS-Install`，这是待 Root 在新 scope 固定的提议，不是现有事实。工具链锁登记由 Root 串行负责；当前不运行介质。

本机只读确认 `C:\Program Files (x86)\NSIS\Bin\makensis.exe` 存在，468,992 bytes，SHA256 `25d1aa7081db1a9de9690b59983f9652b7409a189c3444328cc1841eff693e8d`；MUI2（含 Contrib 实体）、FileFunc/LogicLib/x64 include、Unicode zlib stub 与 `COPYING` 均可定位。未执行编译器；固定源码的 toolchain lock 尚无 NSIS 项。owner 必须记录实际完整 include/plugin/stub 输入，Root 串行登记工具 pin，不仅信任 exe hash。明细见 `NSIS-RESOURCES.json`。

必须等待或单独串行整合的是：`internal/installation/gate_windows.go`、`apps/installation-guard/main_windows.go` 与 Desktop `main.js`/`product-layout.js`、CLI `product_host_windows.go`/`main.go`、Core `apps/control/main.go` 的接入及对应测试；再接 `ops/release/product_installer/transaction/main.go` 和事务测试。新 gate 包可独立设计/开发，但不得同时改 chooser owner 的入口文件。Core 在普通 data lease 之前即分派 verifier replacement；必须逐个证明可达入口受门约束，不能只在文档里排除直接运行。C57 协议源码保持冻结，任何入口 wrapper 影响都需另外明确范围和独立审查。

**维护门顺序必须修正**：消费者若全程持共享租约，不能“先拿独占门再让它退出”。应先串行持久记录 MAINTENANCE_REQUESTED，阻止新的使用准入；已持租约消费者仍可正常 settle/Safe Exit；捕获并核对其退出前身份后，再等待所有使用租约释放并取得独占门。消费者先取得使用租约再检查维护意图，且必须在 marker/config/userData 副作用之前检查。这样检查后才出现意图的消费者也仍在租约计数里。安装器崩溃留下非终态 journal，普通启动继续拒绝。`data/coordinator.lock` 只负责数据一致性，目录交换期间仍靠外部稳定门；normal Safe Exit 会删 witness，缺 witness 不能当停机证明。

事务最小状态是 PREPARED→OLD_PROGRAM_SAVED→NEW_PROGRAM_PLACED→DATA_PLACED→INTEGRATION_APPLIED→VERIFYING→COMMITTED，另有回滚/需恢复；profile/config 子步骤要可重放。独占期间只给该事务一次性验证准入，不向普通客户端开放。每个 intent、外部副作用及完成边界注入失败；COMMITTED 后新用户写入绝不能被静默回滚。

最终发行还需新的产品闭包：chooser/gate 改 main/lib 会使旧 validator descriptor 失效，必须重建 validator→product layout→payload→media。现 P1a builder/finalizer 还固定 `5c4c` 源码与旧 marker，不能直接接受新产品；要在另获授权的后继源码绑定中更新并复核，保留 `69f91b72` 历史接受。增加 guard/品牌文件后按实际 inventory 计数，不能继续硬称133；不得安装时改 Electron PE 或补写 descriptor。

检查依据：蓝图19 §5、§10–11（尤其202–212）、产品合同14:95–119、delivery U08，以及 A15-02/03/06/07。现在可证明介质同 payload、静态路径/owner/状态机；等待门后才能证明 CLI/GUI/直接 Core 与每次交换的启动竞争、双安装器互斥、崩溃恢复、非空升级与保数据卸载。最后必须在无开发 Node/Go/Bun 的干净 Windows 普通用户上，从实际双介质完成首用→同会话→更新→卸载→保留数据重装，并将运行 binary hash 对回安装件。静态通过不代替 LIVE_WINDOWS。

本次只有固定源码/合同只读审查，未编译、跑测试、启动安装器/native/product、改注册表或数据。更细的文件/依赖/完成条件和未覆盖项见 `RECOMMENDATION.json`；输入摘要和源码定位见 `INPUTS.json`。P1a已接受的source/static边界不升级为P1b实现接受。
