# CP558 product host 独立复核准备

结论：`PREPARATION_COMPLETE_IMPLEMENTATION_NOT_ACCEPTED`。本包冻结的是审查判据及一次可变源码观察，不是产品实现接受。尚待 Root 提供 frozen commit、最终 build 路径和闭包证据，再做最终独立复核。`source_acceptance=false`、`native_runs=0`、`formal_increment=0`。

执行身份：`codex:/root/product_host_independent_20261028`；按项目 AGENTS.md 独立验收策略使用 `gpt-6-astra/high`。本轮只读实现 worktree；写入只在此独立 receipt 目录。没有编辑实现、Main 源码、shared canonical 状态或历史失败回执。

审查输入为 CP558 `Product-host-exact14-source-scope.json`、其引用的 `REVIEW-PACKAGE-SEAL.json`、设计报告、`FINAL-SCOPE-ADDENDUM.md` 与 `CLOSE-SEMANTICS-CLARIFICATION.md`，以及 v2.4 的 08/14/22 和 `contracts/product.contract.json`。`PREP-INPUTS.json` 记录 scope hash、设计 seal 及全部 33 个引用的实读 hash/bytes；设计 seal 与引用均匹配。exact14 一次性只读副本在 `prep-source-snapshot/`，每个文件复制期间均未变动，但这不证明整棵 mutable worktree 原子冻结。

以下行号指 `prep-source-snapshot/` 捕获版本；实现者修复后应以新 frozen commit 重新确认。支持链来自同 worktree 的既有私有管理、Core 和 Native3 源码，详见 `SUPPORT-INPUTS.json`。

| ID / 优先级 | 可观察影响与触发 | 源码依据 | 当前证据与完成条件 |
|---|---|---|---|
| F01 / P1 | 合法 builder inventory 含大写文件名时，Desktop loader 报 `PRODUCT_MANIFEST_ALIAS`，产品无法启动。 | JS `product-layout.js:83-86` 把 path 转小写后要求严格升序；Go `product_host_windows.go:208-209` 与 `build-development.py:153` 按原 path 排序；builder 使用 `dev.inventory(output)`。 | **独立 fixture 已复现**：101 项清单含 `runtime/LICENSE`，所有 bytes/hash/installation_id 正确，JS 仍拒绝；全小写对照通过。见 `prep-probes.cjs`、`PREP-PROBES.json`。修复须使 builder、Go、JS 对排序和 case alias 使用一致规则，并用真实 build inventory 验证两个 loader。 |
| F02 / P1 | 正常退出后的再次 CLI 启动，在新 STARTING witness 已写、旧 discovery 尚未被新 Core 覆盖的窗口，可能被误判 orphan 并退出。 | `main.js:409` 先写 STARTING；既有 `desktop-management.js:421-427` 在启动前探测旧 discovery/HTTP；`product_host_windows.go:455-464` 对 dead discovery + existing witness 一律返回 `PRODUCT_ORPHAN_RECORD`，`:615-617` 遇 FOREIGN 立即结束。Core `main.go:241-244` 写 discovery，没有受控退出时删除该文件的路径。 | **源码路径推演，未运行 Go/native**。补 mock：同安装 binding + 非空数据 + dead old discovery + 当前可信 STARTING parent，随后切到新 READY；允许 bounded wait，不删 discovery、不杀 PID、不接管 live orphan。负向 old PID 仍活、未知权限、其他 parent 必须继续拒绝。 |
| F03 / P1 | 第一次裸 `researchos` 取得 token 后无项目引导；可能等待 stdin，首条消息携空 workspace/model 进入 session.create，无法达到可用首日入口。 | `cli_verbs.go:225-241` 空 cfg 后直接 `session.list`；`:350-357` 用空 `cfg.WorkspaceRef`/`cfg.Model` 建 session。改动只扩展凭据 bootstrap，未增加项目选择或下一步说明。 | **源码确认**。空配置应提供明确 `researchos init <path>`/项目选择路径；既有项目不得重置 cfg 或重复目录授权；首用和缺资源必须使用准确退出码。加入 hermetic 空 cfg 与已有 cfg 分支。 |
| F04 / P1 | CLI 后台启动失败且 child 退出未确认时，可留下持有 singleton 的无窗口、无 tray 宿主；后续 Desktop 无法打开诊断。 | `main.js:442-443` 在 tray/window/productSafeExit 建立前 await 启动；`:588-591` unconfirmed child 仅记录并 return；`:60-63` show/safeExit 仍 null；`:70-81` 第二实例和 before-quit 没有可用动作。`product_host_windows.go:633-639` 宿主日志接 NUL。 | **源码确认**。启动中及失败后必须有用户可见的诊断/可操作入口，保留 uncertain child 不强杀、不宣称 safe exit。用纯 Electron API mock 触发启动超时/失败/拒绝，并检查第二次打开可见诊断。 |
| F05 / P2 | 单独 `/model` 别名在 Core 已退出时不确保共享宿主就绪，与 `config set-model` 行为不同。 | `main.go:75-86` 依据 `needs` 判 host-bound；`cli_contract.go:72` `/model` 的 needs 仅 `config file`；`:486-487` 实际调用 `configureCLIModel`，需 Native3/host.configure。 | **源码确认**。核对所有实际 host-bound verb 和合法 interactive leading flags，针对别名断言启动一次；help/version/doctor/commands 保持不启动。不能靠修改共享 command registry 掩盖入口遗漏。 |
| F06 / P1 | 产品布局的 marker 被删除后，Desktop 可静默退回开发数据根，从而绕过 product inventory 校验并打开一套 fresh 数据；CLI 对同状态已拒绝。 | `product-layout.js:61` 缺 marker 返回 null；`main.js:29-53` null 选择 dev 控制路径及 `REPO/.local/data`；Go `product_host_windows.go:192-193` bin 产品入口缺 marker 返回 `PRODUCT_MANIFEST_UNAVAILABLE`。 | **源码确认**。区分合法源码开发树与生成产品树；后者 marker 缺失必须在 Core start 前拒绝。保留源码开发入口。补 marker removal mock，验证没有 Core、data/witness 写入。 |

另外保留三个审查点，不把它们冒称新增已复现问题：`READY_CANDIDATE` 的首次 Native3 连接失败是否应在同一预算内等待；witness retire 失败后仍 `app.quit()` 会使下次启动因残留 witness 拒绝，必须在产品诊断与回执中准确表示；Desktop 自身启动时应在 Core start 前核对实际 Electron path/hash 与产品 marker，不能先以外部 Electron 管理产品数据、到 CLI 连接时才发现 parent image 不符。实现者已收到这些审查点。

Root 提出的 token/clientID 疑点已由源码消除：`internal/host/bootstrap.go:17-23` 的 Session 无 ClientID；`:108-125` 按 principalID 签发 token；`native.go:175-195` 仅在 bootstrap reply 回显 clientID；`internal/api/v2.go:155,188` 鉴别 token 得 principal 后执行 envelope。因此 `product-cli` readiness 与后续 CLI clientID 共用有效 token 本身不是身份冲突。这不是 Native3 实跑证明；client selection/writer epoch 和 token 轮换仍须独立验证。

本轮执行了 5 个纯 Node 探针：4 项符合预期，F01 一项复现失败。并发 safeExit helper 只调用一次 shutdown；未确认退出不会调用 retire/onExit；相同 binding 的非空文件 helper 重开保留原字节。后两者不含实际 process/discovery/native/session 行为，不能代替 F02 或真实重开验收。探针创建的临时 fixture 已在校验绝对路径后删除，证据保留。

后续执行入口和逐项完成判据见 `FROZEN-REVIEW-MATRIX.md`。真实 Electron/Core/native、安装/升级/卸载、C57、provider/业务、完整 22 父任务及 42 用例全部保留，未增加任何正式接受。
