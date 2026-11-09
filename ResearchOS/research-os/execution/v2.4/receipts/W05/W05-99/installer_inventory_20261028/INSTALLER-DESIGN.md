# ResearchOS Windows 双入口发行最小设计（源码审查，2026-10-28）

## 决策建议

首版做**一个每用户安装、两个离线安装介质**。`ResearchOS-Desktop-2.4.0-win-x64.exe` 与 `ResearchOS-CLI-2.4.0-win-x64.exe` 使用同一内容哈希的完整 payload，同一个 HKCU 卸载登记和 `%LOCALAPPDATA%\Programs\ResearchOS` 安装根；两者都安装 Desktop、Core、CLI、Mu worker、Node、Electron 和 verifier。介质只改变默认启动/入口提示，第二个介质遇到相同版本时只补入口，不重写程序或数据。CLI-only 小包需要先改产品宿主发现方式；当前 CLI 从自身 `bin` 父目录读 `installed-product.json` 并启动其中的 Electron（候选 `apps/cli/product_host_windows.go:179-232,255-258,624-650`），故现在不能用单个 exe 满足真实 CLI 安装。此安排满足两个可安装入口，但不是两个独立数据实例。禁止把独立 Mu 的 installer、appId 或 GitHub 更新 feed 当 ResearchOS 发行（`third_party/mu/desktop/packages/desktop/electron-builder.yml:1-5,129-146,245-255`）。

固定首版安装根，`RequestExecutionLevel user`，HKCU 卸载登记与当前用户开始菜单；不需要管理员权限，也不需要用户机 Go/Node/Python。`bin/researchos.cmd` 使用 W05-03 已验证的 `%~dp0` 引号写法（`ops/cli_distribution/main.go:165-175`），由安装器将 `bin` 追加到 HKCU 用户 PATH 并记录“本安装器添加”状态；卸载只撤销自身添加的段。Desktop 快捷方式指向产品根的 `runtime/electron/electron.exe`，参数为产品根 `apps/desktop`，工作目录为产品根，与当前 CLI 启动方式一致。桌面应用的 ResearchOS 名称、图标和 exe 元数据需在发行门单独检查；目前 `apps/desktop/package.json:2-8` 有产品名而原始 Electron 二进制仍需品牌处理。

本机 `C:/Program Files (x86)/NSIS/Bin/makensis.exe` 文件存在，468,992 bytes，SHA-256 `25d1aa7081db1a9de9690b59983f9652b7409a189c3444328cc1841eff693e8d`；未运行编译。建议先用**独立 ResearchOS NSIS 脚本**，以现有 `third_party/mu/desktop/packages/desktop/electron-builder.yml:129-146` 的界面、快捷方式和卸载能力为参考。现有 `electron-builder` 包在两个相关 node_modules 均缺席，Mu 的 builder 还会准备 Mu/AionCore 资源、处理其更新源；直接运行它不是最小路径。NSIS 仅做 UI、解包、入口/注册和调用受控安装 helper，不自行决定业务安装身份。

## 信任链和最终路径定稿

构建机先用 `apps/desktop/build-product-layout.py` 现有冻结路径产出源绑定候选（`:33-51,72-79,87-101,115-139,177-196`）；再在新的发行 staging 中**去掉候选的 `installed-product.json` 与 `apps/desktop/resources/control/runtime-verifier-installation.json`**，生成 `payload-manifest.json`：精确相对路径、大小、SHA-256、五个二进制路径/哈希、`source_commit`、`source_digest`、产品/协议/schema 版本、工具/构建摘要。安装器同时嵌入该 manifest 和一个在构建机编译的独立 Go finalizer；用户机无需开发工具。外部批准的安装器 SHA-256 或签名是来源信任根；内部哈希只能证明同一发行物内的字节未漂移，不能独立证明发布者身份（参照 `docs/installation/README.md:16`）。冻结的 manifest 与 finalizer 作为安装器自身的验证输入，不从用户数据目录读取。

NSIS 解包到同卷新 staging，finalizer 先逐项验证 payload，拒绝缺失、别名、重定向、额外文件、覆盖既有非本产品目录。对新装，staging 进入最终根后生成最终路径绑定文件；对升级，旧根保留为同卷 `.previous-<transaction>`，新 staging 原子改名为最终根。finalizer 的输入是**最终规范绝对路径**，不接受从环境变量推断的来源路径：先写 `runtime-verifier-installation.json`，其 `executable` 必须为最终根下 `runtime-verifier.exe`，`executable_hash` 取冻结二进制哈希（现有生成位置 `build-product-layout.py:162-169`）；然后枚举最终根全部常规文件，允许集仅为 payload 文件加这个路径绑定文件和本安装器生成的卸载程序，按一个规范排序并重算 `inventory_digest`；最后用 `install_root + source_commit + source_digest + inventory_digest + version + protocol + schema_version + cli/control/electron/verifier/validator hashes` 重算 `installation_id`（`:54-65,197-216`），原子提交 `installed-product.json`。校验时排除 marker 自身。卸载程序必须在定稿前产生并纳入最终库存，或者保存在产品根外且单独登记哈希；不能定稿后悄悄往根目录加文件。路径字节采用 Windows 规范绝对路径的原样字符串，跨 Python/Go/JS 计算须一致。安装器不得把用户选定根的大小写、斜杠或尾部斜杠另行改写。

当前 JS/Go 两个消费者均在启动前校验清单、所有文件和五个二进制（`apps/desktop/main/lib/product-layout.js:45-113`；`apps/cli/product_host_windows.go:179-232`）；finalizer 后必须分别运行只读校验。候选源码正在修正 F01 文件排序：旧版 Python `build-development.py:138-154` 与 JS 曾采用不同排序，根 Agent 已告知当前修复为原始路径排序并用大小写折叠集合拒绝别名；此处是**历史发现，最终冻结时复核**，不作为新的未决 P1。Go/JS 当前还硬编码 `product_version=2.4.0`、`schema_version=24`（`product-layout.js:72-80`；`product_host_windows.go:198-205`），真正版本升级须随新发行同步更新兼容门。

## 安装、升级、失败回退、卸载

**新装**：预检当前用户/路径与同名安装登记；解包和核对 payload；生成定稿文件；从最终根静态复核；再写 HKCU 登记、两个入口及安装回执。安装未提交时不展示快捷方式。`%LOCALAPPDATA%\ResearchOS\data` 与 `desktop-user-data` 是数据根，不在程序根库存内（`product-layout.js:98-113`）。首次数据绑定仍由 Electron 主实例负责（`:142-169`）；安装器不伪造首启成功。

**同版本重装/第二介质**：只接受当前 marker、实际库存与已批准 payload 相同，修复缺少的开始菜单或 CLI PATH 入口；任一文件变化或数据绑定冲突，停止并保留现状。两个介质共同指向一条安装记录，卸载一次即可移除所有产品入口，避免双重拥有同一 payload。

**升级**：先验证旧程序 marker、当前数据绑定与进程身份；通过产品 Safe Exit 请求停机，确认拥有的 Core/Electron 已退出，未知进程则拒绝，不用夹具 `stop.ps1` 的强制 Kill（`ops/release/stop.ps1:19-35`；`product-layout.js:231-254`）。对程序做同卷 staged/previous 两目录交换；对非空数据做独立、可回退的快照/迁移：保留旧 `data`、配置与必要的 Chromium profile；在新数据副本上应用受支持的 schema 迁移，再把 `product-binding.json` 从**核实的旧 ID**原子改为新 ID。现有 `ops/backup/main.go:28-43,72-92,134-178` 可复用数据库/产物备份恢复和已定义 schema 升级，但**不等于整个用户数据目录/配置/Chromium profile 的快照**；需要补安装事务级保护。若迁移、重新绑定、静态验证或首次受控健康检查失败，且新宿主确认为已停止，就反向交换旧程序和旧数据，复核旧 ID/项目/会话后报告失败；若进程归属不明，保留新旧快照与失败回执并阻塞人工处理，不递归删或强杀。正式向用户交付新版本前完成健康检查，避免已产生新工作后自动回退丢写入。`product-layout.js:142-169` 和 CLI `product_host_windows.go:299-327` 目前对旧 ID 的非空数据直接拒绝，故该迁移不是可选工作。Mu 自动更新源不能复用，先做离线受控升级；`ops/supervisor/release_host/main.go:1-4` 是 R2 夹具，没有产品 LIVE 升级权限。

**卸载**：核对本安装登记、marker 和 owned 进程，安全退出；只移除该安装登记拥有的快捷方式、PATH 段、程序清单文件和 HKCU 登记。默认保留 `%LOCALAPPDATA%\ResearchOS` 下数据、凭据、日志和回执，并明确告知路径；卸载后重装若旧数据绑定旧安装 ID，须走受控恢复/迁移，不能偷偷把它认作空目录。程序根有额外或不可识别文件时留存并记录，不能递归清理它们。所有失败原始回执保留。

## 施工边界与验证门

最小代码顺序见同目录 `EXACT-PATH-PROPOSAL.json`。第一批只做 payload manifest + finalizer + 定向静态校验；第二批做 NSIS 两介质和当前用户入口；第三批做非空数据事务、迁移失败回退和卸载。`ops/release/build.py:18-39,287-312,320-344` 仍是 R1 夹具，不应悄悄改成产品发行器；新发行入口单列。`execution/toolchains/locked.json` 需要追加并冻结 NSIS 编译器（以及最终品牌工具），这属于共享输入，等候主 Agent 串行整合。

验证矩阵：① 构建机双次独立构建比对 installer/payload 清单、源码与工具哈希；② 不启动 Core/Electron 的临时目录测试：ASCII/中文空格/长路径、复制后重绑定、篡改/漏项/额外项/重定向/重复大小写别名、旧绝对 verifier 路径拒绝、Python/Go/JS 同 ID；③ NSIS 编译后的内容清单与两介质同 payload/单注册契约；④ 隔离 Windows 普通用户实际安装、开始菜单、`researchos` 命令、Desktop 真实启动、双端同项目、非空数据升级、迁移故障注入回退、卸载保留数据与重装恢复；⑤ 独立 W20/A15/U08 复核。前三项只给构建/机制证据，第四项才给真实安装行为，第五项才可讨论正式接受（合同 `contracts/delivery.contract.json:94-103`）。本次只读检查，未执行任何一项测试或安装。

未决：最终是否允许自选安装根（建议首版固定，减少身份/回退分支）；ResearchOS 品牌图标与 exe 元数据的受控工具来源；正式分发信任根采用代码签名还是外部批准哈希；不同旧 schema 的迁移矩阵与 Chromium profile 回退边界。上述由主 Agent 随发行范围定稿，不把缺口记成已经通过。
