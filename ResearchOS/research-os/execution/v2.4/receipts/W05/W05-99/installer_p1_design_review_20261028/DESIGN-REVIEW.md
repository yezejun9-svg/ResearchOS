# P1 安装器独立设计审查

日期：2026-10-28。结论：**NEEDS_REVISION；P1a 纯重绑定算法可采用，P1b 发行结构可采用，P1c 当前不能按“只新增安装器源码”实现安全升级。** 本收据仅为静态源码/设计审查，未运行安装件、产品、native、进程检查或注册表操作，不签发 W20/A15/U08/C57 接受。

审查模型：继承父 Agent 的当前模型配置，未另指定或启动模型；角色为独立设计复核。只读候选源码，没有修改 Main、候选产品或旧证据。输入设计 SHA-256 已实读匹配 `e14bd052a4a67538ab6fad7f6b88c63f1266796cfcf1ed304425c52a99a7edbb`；路径 JSON 匹配 `a3bdb2dcb262f758fde754de0c2cd8322d7da4328ecc1f4a9bbbedff56d83794`。候选 ref 实读为 `5c4c94022bd92da68ef544f2779527bfe065c428`，此值不是工作树无修改证明；最终 freeze 仍由 Root 完成。

证据根：`.local/worktrees/desktop-installed-delivery-20261025`；下文源码路径均相对此根。规格：外部 `19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md:202-212`、`14_CLI_DESKTOP_PRODUCT.md:95-117` 和 `contracts/delivery.contract.json:94-103`。不扩大 C57 frozen 权限。

## 按优先级排列的 findings

### F01 / P1：PID 消失检查不能阻止新的 CLI/GUI 启动，维护互斥是必须的消费者改动

`apps/cli/product_host_windows.go:601-628` 在 ABSENT/DEAD 时可再次启动 Electron；`apps/desktop/main/main.js:31-38,69-85` 在自己的单实例锁外先处理 userData；目前没有安装维护门。两个入口在安装器检查 PID 后均可启动，在程序重命名、data snapshot、binding 替换之间产生 race。Electron singleton 保护两个 Electron 的主实例选择，安装器没有取得该锁，且该锁依赖正要快照/交换的 Chromium profile，不能作为现成安装事务锁。

最小必要修正：在**不参与程序/data/profile rename 的稳定安装管理目录**定义一个跨 CLI、Desktop、安装器/卸载器的 OS-backed gate。普通消费者持共享使用租约，维护持独占租约；或者提供有等价并发证明的启动登记协议。门必须覆盖首次读取/验证产品身份、配置/数据写入与启动直到相关进程退出；不得“检查维护文件不存在后继续”，不得“拿锁检查后释放再启动”。同用户所有会话需同一 gate，不能只锁一个 NSIS 进程。维护 journal 非终态时，普通启动必须拒绝，即使安装器崩溃导致 OS 锁释放。

建议最小实现为共享 Go gate 包和随包 native guard/broker，由 CLI 与 Electron 显式接入。Electron 的 guard 成功握手必须发生在修改 userData/witness/binding 和启动 Core 之前；guard 异常消失时主进程必须 fail closed。具体采用长寿命 guard 还是统一 Go 启动 broker可由实现者选择，但必须覆盖用户直接运行已安装 Electron+app 的入口，不能只保护开始菜单。若保留 Core 直接启动/管理入口，则该入口也须消费同一稳定 gate；否则不能声称安装事务覆盖它。

精确必须登记：`apps/desktop/main/main.js`、`apps/desktop/main/lib/product-layout.js`、`apps/cli/product_host_windows.go`、相关测试，以及新增 gate/guard 源码（见 PATH-REVISION.json）。这不是“仅未来版本变更才需要”的 conditional 项。

### F02 / P1：既有 coordinator 锁应复用检查写入排他，但不能代替维护门跨目录交换

`adapters/runtime/data_root_windows.go:13-30`、`bridge_windows.go:163-177`、`process_windows.go:185-194` 表明 Core 持有 data/coordinator.lock 的非继承、share-mode-zero 句柄；`apps/control/main.go:103-118` 在打开后续数据前取得 lease。可复用它证明旧 Core 不再持有数据写租约，并在稳定门保护下做 snapshot/验证。它位于会被更名的 data 根内，持有时不能假设 data rename 能成功；释放后则不足以阻止新 Core 在固定路径创建/取得另一文件锁。即使旧目录 rename 成功，旧文件句柄也不会自动锁住新目录中的 coordinator.lock。

顺序应为：取得稳定维护独占门 → 确认宿主安全退出及身份 → 取得旧 data lease → 验证/快照 → 在稳定门仍持有时按已验证 Windows 顺序释放内部 lease 并交换目录 → 取得新 data lease/执行验证。必要时在 Core 数据 lease 入口加稳定 gate，使直接 Core 也不能绕过。禁止改掉既有 coordinator 锁语义或把 lease 对象借给不同进程。

还需修正停机证据：`product-layout.js:216-223,240-250` 在正常 Safe Exit 中删除 witness，再退出 Electron。安装器不能要求“退出后必须仍读到 witness”；应在退出前捕获/核对身份，之后验证该身份退出并由维护门排除新启动，或新增持久、受核验的停机回执。witness 缺失本身既不是失败停机，也不是安全停机证明。

### F03 / P1：同版本新 build 是真实升级，且 verifier 的持久注册不随 product-binding 自动迁移

`product-layout.js:45-50,160-162` 和 `product_host_windows.go:313-320` 明确把 source/inventory/binary hashes 纳入 installation ID 并拒绝旧 ID。因此 version=2.4.0/schema=24 相同但 payload 不同也必须走升级事务；只能把完全同 payload、同根、同 provenance 的第二媒体识别为幂等入口补全。以 DisplayVersion 相同就跳过替换将造成旧内容或数据冲突。

更关键：`internal/host/runtime_qualification_windows.go:70-93` 在 data/host/runtime-verifier-installation.json 保存 verifier executable、image hash、source_commit 及其安装 hash，变化时拒绝并要求 explicit replacement。新 build 的 source_commit 或 verifier hash 变化即触发；从候选路径迁到正式路径也会触发。只改 product-binding.json，READY 与项目读取即使成功，后续 qualification 仍可失败。

P1 最小安全边界：先支持新装、完全同 payload 重装，以及**明确没有历史 verifier 注册/未完成 verifier replacement journal**的 schema24 非空数据升级；存在注册的旧数据在修改前明确阻断。它是被阻断的升级支路，不能被写成“全部非空升级完成”。后续若 Root 获得现有 C57 管理接口的调用授权/接受，再评估只调用 `apps/control/runtime_verifier_replacement_windows.go:17-74` 的 preflight/commit/recover，遵守其 plan/hash/history 和规范路径要求；本审查没有执行权限，也不建议删除/改写数据内的注册或 frozen journal。新副本路径上做 preflight 后再换回最终路径不能预设仍有效，须由该协议审查确认。

schema24 本身也不是兼容证明。升级白名单应至少绑定 old/new payload digest、协议、实际 migration inventory/hashes 和数据 schema；不支持跨 schema 的 P1 要在任何 rename 前拒绝。

### F04 / P1：事务还缺失崩溃恢复与首次启动隔离的可执行协议

程序根、data、profile、cli-config、HKCU、shortcut/PATH 不构成一个原子提交。原方案只有正向叙述，尚不能处理“两次 rename 之间断电”或“注册表更新中断”。append-only 回执必须升级为可恢复的状态 journal：每个 intent/完成记录含 transaction ID、旧/新 payload 和 installation ID、固定路径、快照/目录身份、已完成 side effects 与下一动作；重启以文件事实与 hash核验后恢复，不能仅相信最后一行。必须写明持久化/刷新边界与中断记录损坏时的保守拒绝。

建议最小状态：PREPARED → OLD_PROGRAM_SAVED → NEW_PROGRAM_PLACED → DATA_PLACED → INTEGRATION_APPLIED → VERIFYING → COMMITTED，另有 ROLLING_BACK / ROLLED_BACK / NEEDS_RECOVERY；细分 profile/config 的子步骤，不能将其隐藏在一个不可重放操作里。每个外部副作用都有 compare-and-restore 规则，避免回滚覆盖用户后来修改的 PATH 或 shortcut。

“隔离首次启动窗口”目前没有代码路径。若独占维护门持有时无例外入口则新程序无法验证；若释放门则普通 CLI/GUI 能开始新写入。须实现仅该事务拥有的一次性验证 admission/授权委派，明确排除普通用户入口；验证至少包含原项目/session 读回和明确可回滚的写读。COMMITTED 之后不允许自动恢复旧 snapshot；新版本已有用户写入时回滚只能另走明确的保留/迁移决策。无法证明新 owned processes 安全退出时保留双份及 journal，NEEDS_RECOVERY，不宣称已恢复旧版。

### F05 / P2：来源 hash pin 必须绑定到实际 helper 和 payload，不能靠旁置可替换 manifest

可采用 Go 编译 finalizer，无用户开发运行时依赖。但实现合同应明确：发布审批/签名绑定安装 exe；exe 内封装 helper；helper 编译时嵌入批准 payload-manifest digest（或完整清单），不得接受任意命令行 `--manifest` 自证。工具链固定、编译输入/Go module/vendor 闭包、helper SHA-256 与两媒体 SHA-256 留回执。独立打包 helper 尽量使用标准库与已锁定 x/sys，避免因导入大包而意外引入本机动态依赖；干净 Windows 执行才证明自包含。

NSIS 必须检查 helper 每阶段退出码及事务终态，再建快捷方式/报告成功。helper/manifest/卸载器和安装 journal 置于产品库存之外；所有辅助文件仍需各自 ownership/hash 清单。重绑定生成前后均核验无未知文件、路径大小写/重解析/硬链接等不允许别名。新安装根不存在应是合法 fresh-install 状态，先验证父链并 create-new；不要把“根必须现存”直接实现为拒绝新安装。

### F06 / P2：卸载 ownership 清单需持久化，且只删除匹配的项

只有根内 installed-product.json 不足以管理卸载器本身、shim 外入口、快捷方式、PATH 与 HKCU。在稳定管理目录保存受发布链与安装回执约束的 owner 清单，逐项记录 canonical path/type/hash、key/value before/after、是否由安装器新增。卸载时校验 final marker/owner 清单，然后仅删除仍匹配的已拥有文件；未知文件、修改文件、目录别名保留并列明。目录只在空时删除；不用 `RMDir /r` 清理程序根或整个 LocalAppData/ResearchOS。安装数据默认完整保留，外部项目/workspace 即使注册在产品数据中也不得删除。

PATH 撤销应重新读取当前值，仅删除自己曾新增且仍可唯一识别的项，不恢复安装时的整串旧 PATH；旧条目本来存在则不能删除。共享单卸载登记意味着第二媒体不应覆盖 owner provenance。重装保留数据须走 F03 明确迁移，不能删 binding“变成新装”。

### F07 / P2：重绑定不破坏 validator，但后续源码改动必须重新闭合，133 不是永远固定计数

可采用：仅去掉 candidate marker 与 control/runtime-verifier-installation.json，保持其余 bytes；最终路径重建 verifier manifest，再计算 inventory，最后生成 marker。`apps/desktop/main/lib/http-wire.js:25-50` 只检验 validator exe、main/preload 全量精确模块和 schema/build digest；`apps/desktop/build-validator.py:129-171` 把 buildInputDigest 编译进 validator，并产生 descriptor。重写的 verifier manifest 不在 main/preload 中，因此不触发其 module hash。不应改 descriptor 里的历史 build paths 或编译 provenance；它们不是用户机必须具备的执行路径。

但 F01 改 main/lib 后，保留旧 descriptor 会触发 VALIDATOR_MODULE_DIGEST；必须先重新运行受控 build-validator/build-product-layout 得到新的闭包再取 payload，不能只更新 descriptor JSON 或 marker。版本仍 2.4.0 不影响这一点。

`build-product-layout.py:197-216` 先 inventory 后写 marker，所以 file_count 指 marker.files 条目，不包含 marker 自身。按清单证明 133 基线，排除 verifier 项后再重加，不要把“移除两个物理文件”错误实现成从 files 删两个条目。增加 `bin/researchos.cmd`、gate helper、品牌资源都会改变实际计数、库存和 ID；固定数字应改成已冻结清单的精确集合。对原始 Electron PE 改图标/元数据会改 hash；首批可采用自有 ResearchOS launcher/icon，若要改 Electron PE，必须在 payload freeze 前另走 source/tool/binary hash 闭包。不得安装时再修改 PE 资源。

## Root 可直接选择的最小范围

1. **现在可施工**：静态 payload 提取、Go finalizer、两 NSIS 构建、owner 清单及文档；仍只做构建/离线机制证据，不进行真实安装或升级接受。两媒体完整同 payload，CLI 自带 Electron 是现有消费者下可行选择。
2. **真实发行前必须加入**：CLI/GUI/Core 可达入口的稳定维护门、journal startup gate、同版本 build 的迁移分流、崩溃恢复及事务内验证 admission。先把消费者变化纳入新候选，重建 validator→产品闭包，再冻结 payload。不可把这些推迟到“以后换版本”。
3. **P1 可显式排除并阻断**：跨 schema、任意安装目录、自动热更新、历史 verifier 注册迁移（C57 未授权）、未知/篡改旧根。排除后交付范围必须如实记录；这些未闭合时不写“完整安装升级验收通过”。

## 必要验证与先后依赖

A. 冻结源码/工具 → 新消费者维护门 → 重建 validator+descriptor+产品闭包 → payload freeze → finalizer/NSIS。纯 finalizer 原型可以提前基于冻结旧闭包实现，最终发行须换成门已闭合的新闭包。

B. 静态/单元：Python/Go/JS 相同 path ordering、换行、绝对路径和 ID；中文空格/长路径/大小写别名/reparse/未知项/错误 hash；同 payload 第二媒体幂等；同 version 不同 payload 走升级；有 verifier registration/不支持 schema 在首次写入前拒绝；卸载未知文件和既有 PATH 不删除。

C. Windows 并发真实检查：在 old PID 最后检查后、每次 rename 前后启动 CLI/GUI；两个安装器/卸载器互斥；直接 Electron 入口；Core 直接入口若保留；安装器崩溃后普通启动被 journal 拦住；验证 admission 不能给其他客户端借用。原宿主生命周期未验证，不可用 mock lock 代替。

D. 每个 journal intent/side effect/完成边界注入失败，验证恢复前后旧/新程序与数据配对、profile/config、HKCU/PATH，并保留失败原始证据。至少一次非空 schema24 同版本新 build 升级与失败回滚；有历史注册的支路须证明提前拒绝，或另有授权的完整 replacement 证据。

E. 无开发 Node/Go/Bun 的 Windows 11 普通用户真实安装双媒体，单 host、双端同 project/session、卸载后数据 hash/读取恢复。安装件 hash 与实际运行 binary hashes 一致，再交独立 W20/A15/U08。A/B 通过不代替 C/D/E。