# P1 Windows 双发行件实施设计（只读方案，2026-10-28）

## 结论与范围

在 exact14 / ASAR exact2 的产品布局冻结后，新建一个**独立发行施工分支**。P1 不改正在修正的 product host：从它已核对的 133 文件位置绑定布局提取一份位置无关 payload，用本机 NSIS 编出 Desktop/CLI 两个每用户安装介质；两者安装到同一 `%LOCALAPPDATA%\Programs\ResearchOS`，共用一个安装 ID、一个 `%LOCALAPPDATA%\ResearchOS` 数据根、一个 HKCU 卸载登记。CLI 介质也携带 Electron 与完整宿主，因为当前 CLI 的安装模式必须从自身 `bin` 上溯读取 marker 并启动内置 Electron（`apps/cli/product_host_windows.go:179-232,255-258,624-650`）；仅 `researchos.exe` 加 shim 无法独立工作。两个介质都不是第二个 Core 实例。

来源合同：`14_CLI_DESKTOP_PRODUCT.md:95-117` 要求可安装、自己品牌和 P07/A15 两发行件；`19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md:202-212` 固定 Windows 11 x64 每用户默认目录、无开发工具、升级失败保留旧版、卸载默认保留数据，并要求本地安装包更新、不用 Mu 更新源；`contracts/delivery.contract.json:94-103` 的 U08/A15 仍为 `NOT_RUN`。既有独立审查 `desktop_main7d_independent_review_codex/20261025-current-chat/owned-host-design-review/HOST-DESIGN-REVIEW.md:34-42` 接受共享 Electron 宿主路线并明确安装绑定须在最终位置生成；`FINAL-SCOPE-ADDENDUM.md:1-20` 的 exact14 范围由宿主 owner 管理。本报告是下一施工者的源码范围建议，不签发该范围或任何验收。

## P1a：可信 payload 到最终绝对路径

**构建机输入**：冻结 exact14 的 `build-product-layout.py` 候选目录、它的 create-new receipts/`installed-product.json`、固定 Go/Node/Electron/Mu/编译输入和 git 版本。该 builder 已构建 Core、CLI、runtime verifier、client-wire validator 和 Electron，写 133 文件的 marker；`:33-51,72-79,87-101,115-139,140-176,177-225` 已有冻结、逐文件复制、完整库存与身份算法。发行构建器先核对候选 receipt 的 marker hash、逐项文件大小/hash、五个 exe、源码/工具摘要以及发行输入前后不变；不把候选 `.local` 路径原样发给用户。`ops/release/build.py:18-39,287-312,320-344` 仍是 R1 fixture ZIP，只借其确定性归档、依赖/许可清单与冻结思路，不改其语义。

**发行 payload**：复制候选完整物理目录树，但排除两项只对候选目录有效的文件：根 `installed-product.json`、`apps/desktop/resources/control/runtime-verifier-installation.json`（原生成位置 `build-product-layout.py:162-169,197-216`）。新增发行侧 `payload-manifest.json`，按大小写敏感的规范相对路径排序，列出所有其余常规文件的 bytes/SHA-256、五 exe 相对路径与 hash、`source_commit`/`source_digest`、版本/协议/schema、builder 输入摘要、来源/许可缺口；该清单只放在安装器内，不放入产品根。尤其保留 `apps/desktop/main`、preload、web/dist、contracts、migrations、Mu worker、Node、Electron 和已冻结的 client-wire descriptor；不能让 electron-builder 默认 ASAR 改动目录结构。上游 Mu `electron-builder.yml:1-5,21-28,111-145,245-255` 只用作 NSIS 体验参考，不继承 appId、品牌、AionCore 资源或 GitHub 更新地址。

**安装机**：NSIS 解包 payload 和发行时编译的 Go `install-helper.exe` 到同卷 staging；用户机不用 Python、Go、Node/Bun 开发环境。helper 对 staging 与嵌入的 payload-manifest 做精确集合比对，拒绝缺项、多项、大小写别名、reparse point、hash 漂移和路径越界。安装根必须是规范、现存同卷的绝对路径，首版建议固定默认路径，不开放换目录。进入最终根前不启动 Core/Electron；原有根只可经升级事务处理，不覆盖。helper 到最终根后先生成 `runtime-verifier-installation.json`：`executable` 是最终根下的绝对 `runtime-verifier.exe`、hash 是冻结 verifier hash、source_commit 与原候选一致、arguments 为空。再枚举最终根所有产品文件（marker 尚不存在；卸载程序放在根外），按现有 Python/Go/JS 一致的原始相对路径顺序写 `files`，计算 `inventory_digest=SHA256("researchos.product-inventory/1\n" + 每项 path/hash/bytes 与换行)`，然后按 `schema, install_root, source_commit, source_digest, inventory_digest, version, protocol, schema_version, cli/control/electron/verifier/validator hashes` 的现有顺序和换行计算 `installation_id`（`build-product-layout.py:54-65`；`product-layout.js:45-55`；`product_host_windows.go:137-151`）。保留当前 `researchos.product-layout/1` 与 `OWNED_PRODUCT_LAYOUT_NOT_INSTALLER` marker 值，以免为 P1a 改消费者；该 mode 表示布局自身非安装器。最终 marker 还须原样保留候选的 tool_hashes、Go/Mu 编译输入与 vendor 摘要、client-wire 输入摘要；这些不是安装机重新编译的结果。最后原子写 marker、复核完整根、写安装回执。安装器外部批准的 SHA-256 或真实签名是来源信任根；自描述 manifest 只证明内部一致性，不能自证发布者（`docs/installation/README.md:16`）。

**排序 F01**：先前 Python/JS 排序冲突已有宿主 owner 修正；本报告不将其登记为新的阻断项。冻结后用实际 Electron `LICENSE` 和小写资源文件，在 Go、JS 与 helper 上做同一清单/ID 比对。候选持续变化，本文读取时 worktree HEAD 为 `5c4c9402`，不能把该值当最终冻结 revision。

## P1b：两个 NSIS 介质、一条安装登记

本机 `C:/Program Files (x86)/NSIS/Bin/makensis.exe` 存在，468,992 bytes，SHA-256 `25d1aa7081db1a9de9690b59983f9652b7409a189c3444328cc1841eff693e8d`；仅文件元数据确认，未编译。发行构建器固定其 hash 并输出两次 `makensis` 命令与产物 hash。一个 `researchos.nsi` 用媒体参数生成 `ResearchOS-Desktop-<version>-win-x64.exe` 和 `ResearchOS-CLI-<version>-win-x64.exe`，安装内容/`payload-manifest.json` hash 完全相同；媒体参数只影响入口提示或默认打开 Desktop/CLI。`RequestExecutionLevel user`、HKCU 安装/卸载登记、当前用户开始菜单、ResearchOS 自有图标；卸载器放在产品根外的安装管理目录并单独记录 hash，这样媒体差异不会改变产品库存和 canonical ID。Desktop 快捷方式指向安装根 `runtime/electron/electron.exe`，应用参数指向同根 `apps/desktop`，工作目录同根；`bin/researchos.cmd` 从构建机写入 payload，用 `%~dp0researchos.exe` 加引号（`ops/cli_distribution/main.go:165-175`）。若将 `bin` 写入 HKCU 用户 PATH，安装回执记录“本安装器新增”标志，卸载仅撤销自己添加的精确项；安装页提示新终端才看得到 PATH。相同版本/相同 payload 的第二媒体只补缺失入口，不替换数据或生成新安装 ID；不同版本走受控升级；未知或篡改的根拒绝。

Mu `electron-builder.yml:129-146` 的 NSIS 安装页、开始菜单和卸载登记可参考，但当前 `electron-builder` 依赖未安装，Mu build 脚本还处理 Mu/AionCore 和其进程；独立 NSIS 脚本比引入整套上游打包链更小。真实品牌还需 ResearchOS 图标和 exe 元数据方案；当前原始 Electron `electron.exe` 不应因快捷方式改名就宣称完整品牌。没有代码签名凭据时按规格标记未签名，不声称无 SmartScreen 提示。

## P1c：非空数据升级、失败回退、卸载

**受控停机门**：当前候选 `main.js`/`product-layout.js` 提供用户可操作的 Safe Exit，但 CLI 合同没有安装器可调用的 safe-exit 命令（`apps/cli/cli_contract.go:62-75`；`main.js:68-86,487-490`）。P1 先要求用户通过托盘安全退出，安装器验证 witness 中的 Electron/Core PID、创建时间、镜像 hash、data root 与安装 ID 均已退出；busy/uncertain/foreign/orphan/stale witness 均拒绝且保留现场，不调用夹具 `ops/release/stop.ps1` 的 Kill。这样暂不扩张宿主 IPC/API。任何带活动任务的升级必须先按现有 Safe Exit 的实际 settled/拒绝结果处理，不能把进程消失当任务安全。

**事务**：先复核旧 marker、产品根清单、旧 `product-binding.json` 与 schema；在程序根和数据根之外创建同卷 create-new staging/previous 目录和 append-only 事务回执。旧数据的保护范围是 `%LOCALAPPDATA%\ResearchOS\data`、`cli-config.json`、`desktop-user-data` 和安装登记/快捷方式，先逐项快照并核对 hash；`ops/backup/main.go:28-43,72-92,134-178` 的加密数据库/产物备份与已定义迁移可作为内部机制，但不覆盖整个用户数据/Chromium profile，也不自动支持从 schema24 到下一版本。新数据**副本**上运行被明确支持的迁移，临时 discovery/witness 只在副本里隔离处理；只有旧 ID 与已停进程都被验证，才将副本 `product-binding.json` 原子更新为新 ID。旧程序根重命名为 previous，新 payload staged 根重命名为固定最终根；数据根同理交换。先做静态 marker/身份验证，再在隔离的首次启动窗口做真实 READY、项目/session、迁移后的读写检查。未向用户放开新写入前若失败，确认新进程已安全停止后反向交换程序/数据/登记，复核旧安装 ID 和非空项目/session 可启动；不能确认进程归属时保留两套快照与失败记录并拒绝自动回滚。接受新版本后保留旧备份到验证完成，不能把后续新写入静默回滚。当前 `product-layout.js:142-169`、`product_host_windows.go:299-327` 对旧 ID 非空数据会拒绝；此迁移是实际缺口。

**卸载**：同样要求 Safe Exit 与 owned 进程消失，按核实的程序库存删除程序文件及安装器拥有的快捷方式、HKCU 项、PATH 项；额外文件或身份不明则留下并报明细。默认保留整个 `%LOCALAPPDATA%\ResearchOS`（含数据、配置、凭据状态、日志与证据）；删除用户数据只能另设明确选择，不放在默认卸载步骤。后续重装遇旧绑定不能当空数据绕过，须显式恢复/迁移。原 `docs/installation/desktop-product-host.md:3-11` 仍声明候选非 installer；新发行说明另建文件，不改已登记的 exact14 文档。

## 精确源码顺序与验收

路径/owner/门见同目录 `P1-EXACT-PATHS.json`。推荐只在 frozen product-host commit 的新 installer worktree 新增 `ops/release/product_installer/{build.py,payload.schema.json,finalize/main.go,transaction/main.go,nsis/researchos.nsi}` 与定向测试、`docs/installation/product-installer.md`。`build-product-layout.py:33-39` 对任何 untracked/dirty 非 exact14 文件拒绝，因此**不能在正在修正的 exact14 worktree 直接放这些新源码后重跑其 builder**；从已冻结候选/回执消费，后续在干净、已登记的 installer commit 重建。首个静态路径批次不需修改 exact14 源码。未来变更 `product_version`/schema（当前 `product-layout.js:74-80`、CLI `product_host_windows.go:198-205` 写死 `2.4.0/24`）必须另登记其 builder/双消费者/测试联动，不让新媒体自行宣称跨版本兼容。NSIS/品牌工具加入 `execution/toolchains/locked.json` 属共享整合，由 Root 串行安排。

验收按门递进：① 两次构建的 installer/payload hash、源码/工具/许可来源清单与 133 文件基线对账；② 无 Core/Electron 的绝对路径/中文空格/长路径定稿，篡改、额外文件、reparse、大小写别名、旧 verifier 路径拒绝；③ 两媒体同 payload、单 HKCU 记录、重复安装不改 ID；④ 干净 Windows 普通用户、无开发 Node/Go/Bun 的 CLI 与 GUI 首次使用、非空数据升级及注入迁移失败回退、卸载保留数据和旧数据恢复；⑤ 独立 W20/A15/U08 与产品完整链审查。前 ③ 项是构建/机制证据，不能替代真实安装；目前所有项均未执行。本轮未运行 Core、Electron、安装器或升级，也未修改任何产品源码。

待 Root 定稿的资源与选择：冻结 exact14/ASAR 候选和合法 133 文件/许可清单；批准的 NSIS 编译器 hash 与 ResearchOS 图标/可用 exe 资源编辑工具；签名凭据是否存在（可无，但须如实标注）；至少一个真实非空旧数据备份/可逆迁移样例及干净 Windows 用户环境。首版固定安装路径与手工 Safe Exit 是本报告建议；若必须自选目录或无人值守热升级，需另扩路径/宿主协议，不应混入 P1 最小 scope。
