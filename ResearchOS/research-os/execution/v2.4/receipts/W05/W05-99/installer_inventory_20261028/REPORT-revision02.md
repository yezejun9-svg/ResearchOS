# Windows CLI / Desktop 安装发行盘点（2026-10-28，只读源码审查）

## 结论

当前**没有可直接使用的 ResearchOS 正式安装器**。`ops/release/build.py:1,18-39,287-312,320-344` 只产出 R1 开发夹具 ZIP，固定源目录与四个 Go 二进制，不含当前 Desktop 产品布局；`docs/installation/README.md:1-3,16-35` 明确排除干净 Windows 安装、升级、回滚和 A15。`ops/cli_distribution/main.go:1-7,90-93,129-175,179-210` 是 W05-03 构建并复制 `researchos.exe`/cmd shim 到测试目录、启动验证的候选，不生成安装包，报告自身标注 `DISTRIBUTION_CANDIDATE_NOT_FINAL_RELEASE`（:118-122）。

上游 Mu **有可复用 NSIS 配置，不是已可用的 ResearchOS 打包器**：`third_party/mu/desktop/packages/desktop/electron-builder.yml:1-5,21-28,111-145` 仍是 Mu 的 appId、名称、payload 和 NSIS 快捷方式/卸载；`:245-255` 的自动更新仍指向 Mu GitHub。`third_party/mu/desktop/package.json:208-209` 声明 `electron-builder` 26.15.2；当前 `third_party/mu/desktop/node_modules/electron-builder/package.json`、`apps/desktop/node_modules/electron-builder/package.json` 和两处 `.bin/electron-builder.cmd` 均不存在。本机 NSIS 有 `C:/Program Files (x86)/NSIS/Bin/makensis.exe`（468,992 bytes）及 `Examples/`；根目录另有 2,560-byte `makensis.exe`。仅查文件元数据，未编译验证。Mu 的 `scripts/build-with-builder.js:775-860` 会走 Mu 资源/上游构建，并含清理与终止同名进程逻辑；不能直接拿来构建当前 ResearchOS 布局。

当前候选 `.local/worktrees/desktop-installed-delivery-20261025/apps/desktop/build-product-layout.py:1-5,68-71,140-176,197-225` 可复用**payload 组装、输入冻结、五个可执行文件及完整库存算法**，但只在工作树 `.local` 创建位置绑定的 `OWNED_PRODUCT_LAYOUT_NOT_INSTALLER` 候选。`docs/installation/desktop-product-host.md:3-11` 同样明确不是安装/升级/卸载包，也没有真实 GUI、开始菜单或 W20 证据。

## 必须先解决的绑定点

`build-product-layout.py:162-169` 把 `runtime-verifier-installation.json.executable` 写成构建目录的绝对路径；随后 :197-216 将它纳入完整库存，`install_root` 和 `installation_id` 也绑定构建目录。简单复制或让 NSIS 改安装目录会破坏身份。`apps/desktop/main/lib/product-layout.js:45-55,58-113` 和 `apps/cli/product_host_windows.go:179-232` 在启动前逐文件核验库存、二进制、安装根与 ID；`:235-258` 的 CLI 还依赖安装内 Electron/桌面路径。因此独立的“只有 CLI exe”安装件不能直接作为当前可用产品入口。

最小实现是将**可信构建 payload**与**最终路径定稿**分成两步：先构建所有不含绝对安装路径的文件并冻结源、工具、完整文件哈希；安装器将它们放到选择的最终绝对根后，核对分发 payload 哈希，在该根生成指向最终 `runtime-verifier.exe` 的 verifier manifest，再按最终文件重算完整库存、五二进制哈希、`inventory_digest` 与 `installation_id`，最后原子写 `installed-product.json` 并让 CLI 与 Desktop 在该根复核。定稿生成的 verifier manifest 必须先于库存计算；marker 自身仍按现有算法排除。安装/升级也要拒绝非空目标中的不明文件，防止旧文件游离于库存外。路径、文件和身份算法应共用一个规范，避免 Python/JS/Go 结果漂移。打包器不能要求普通用户机有 Go、Node 或源码。默认根与数据根见 `desktop-product-host.md:5`；可变安装目录须逐路径实测。`electron-builder` 默认 ASAR/资源目录与当前 `root/apps/desktop`、`root/runtime/electron` 形状不同；若使用其 NSIS 外壳，必须保留当前物理目录布局或同步修改消费者，不能直接打 Mu app。

## 复用边界与缺口

- **安装/卸载框架**：可借 Mu 的 NSIS 配置模式（`electron-builder.yml:129-146`），替换 ResearchOS appId/图标/名称/资源和启动入口；NSIS 负责开始菜单、卸载登记及程序文件移除。ResearchOS 还需自有的最终路径定稿、CLI cmd/PATH 入口、精确 owned-file 清单及 data/receipt 保留策略。`ops/cli_distribution/main.go:165-175` 的引号 shim 可复用。不能把 Mu 的现成安装器或更新 feed 当 ResearchOS 成品。
- **升级/回滚**：`ops/backup/main.go:1,28-43,72-92,134-178` 有加密备份、恢复和限定 schema 迁移入口，可复用数据保护机制；`ops/supervisor/release_host/main.go:1-4` 自称同用户 R2 夹具、无 LIVE 权限。Mu `electron-builder.yml:245-255`/`src/process/services/update/` 可参考 feed 与 updater，但要改成 ResearchOS 发行源、版本和身份门。当前无产品安装 ID 从旧版到新版的受控迁移：`product-layout.js:127-155` 遇到既有 `product-binding.json` 与新 ID 不符会拒绝，升级不能只覆盖 exe。需要先安全停宿主、备份/迁移、安装新布局、原子转移数据绑定并验证同一项目/会话，再提供失败回退。
- **卸载**：`ops/release/stop.ps1:9-35` 是夹具 PID/创建时间校验后的停止，可借鉴身份确认；产品宿主有 `product-layout.js:216-237` 的受控 Safe Exit。需写安装器卸载钩子先请求同一 owned Core 安全退出，拒绝不明进程，删除仅该安装清单内程序文件及快捷方式；用户数据、凭据、日志、回执的保留/删除选项应明确，不能使用夹具 stop 的强制 kill 代替产品退出。
- **两个发行件**：`14_CLI_DESKTOP_PRODUCT.md:13-17,95-117` 与 `contracts/product.contract.json:204-209` 要求可安装 CLI 与 Desktop；`contracts/delivery.contract.json:94-103` 的 U08/A15 仍 `NOT_RUN`。当前 CLI 产品模式依赖完整 Desktop/Electron 布局。最小无重构路径是两个安装介质指向**同一完整 ResearchOS 布局和安装身份**（CLI 介质也带所需 Desktop/host 运行时），或先实现 CLI 通过已安装 Desktop 的受控发现协议再做小体积 CLI-only 包；不要把 W05-03 shim 候选宣称为后者。

## 建议文件与顺序

1. 先在可变候选工作树扩展 `apps/desktop/build-product-layout.py` 或新增独立 `apps/desktop/finalize-install.py`，把最终根作为显式输入并生成最终 verifier manifest/库存/ID；保留现行 schema 和 mode 时，`apps/desktop/main/lib/product-layout.js`、`apps/cli/product_host_windows.go`、`apps/desktop/validator/main.go` 可先作为交叉校验器，不必改消费者。若换 manifest schema、文件布局或升级绑定规则，再按需改这些消费者及其定向测试。当前 exact14 工作树仍 mutable，不在本次审查中改其源码。
2. 新增 ResearchOS 专属 `apps/desktop/installer/`（NSIS 配置/钩子）和发行构建入口；只从已审定 payload 生成 Desktop 安装包及带完整依赖的 CLI 安装包。参考 `third_party/mu/desktop/packages/desktop/electron-builder.yml` 的 NSIS 功能，不复用 Mu identity/update 地址；将 CLI shim 安装进选定入口。
3. 接入受控 Safe Exit、`ops/backup` 备份/恢复和新旧版本数据绑定转移，再实现升级/失败回退与卸载；最后补 `docs/installation/` 的普通用户安装、更新、卸载说明及独立干净 Windows A15/U08 真实证据。现有源码/布局测试只证明候选机制，不能代替这些实机结果（`desktop-product-host.md:11`）。

本次仅作文件/工具元数据审查；未执行 Core、Electron、安装器、构建或安装，未修改 Main/shared 源码与正式验收状态。
