# Main7d 原生 Desktop 开发构建回执

结论：基于干净的 Main `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e` / tree `de59625ee5c1d360c741c95ec3f84b6f2764bb0e`，现有 `apps/desktop/build-validator.py` 在隔离 worktree **真实构建成功**。原生命令退出码 0；内部 9 条子命令均退出 0；`result.json` 明确 `BUILT_NOT_TESTED`、`source_acceptance=false`、`drift=[]`。6449 条编译与源输入前后散列一致。产物含 React 的 `index.html`、CSS、JS 和 Go client-wire validator，不构成可启动的完整 Desktop 安装树。

本次调用前固定的完整 argv、cwd、scope hash 和环境覆盖见 `build-invocation.pre.json`；二进制原始流在 `builder.stdout.raw`、`builder.stderr.raw`，退出码在 `builder.native-exit.txt`，进程与流散列在 `builder-process.json`。32 个 builder 内部原始回执和 8 个有限工件复制到 `copied/`，每一份原位置、规范回执位置、字节数和 SHA-256 见 `build-evidence-manifest.json`（SHA-256 `fedcded71f7610de47c3dd987bacf1546d99fb30b834163fd6fc35fc0b0efa32`）。未复制 Go cache 或 node_modules；内部构建树保留在 worktree `.local`。

源绑定 digest 为 `9a81f132f88faccdf33ab56b0ddcac89c4be050ece63d2a36fde175196d5e5e6`。validator 为 16,211,968 字节，SHA-256 `7d0b9c4557b9c4f726625c296f1598de96aeee30ecd0c368c614c3d0288839bd`。React 资产散列在 `copied/artifacts/client-wire/descriptor.json` 的 `compiled_React_asset_inventory`，复制时逐项核对；Go、Node、Electron、Python 的文件散列也在 descriptor 的 `tools`，与锁定值一致。构建前后 worktree 的 Git 跟踪文件均干净。

## 静态入口完整性

`apps/desktop/main/main.js` 把 `ROOT` 定在 `apps/desktop`，`REPO` 定在上两级；生成树因此正确提供 `apps/web/dist/index.html`，`apps/desktop/main/main.js`、`preload/preload.js`、client-wire validator 与 descriptor。它默认从 `apps/desktop/resources/control/researchos-control.exe` 取 Core，从同目录取 `runtime-verifier-installation.json`，从 `runtime/` 取运行资源；生成树**这三项均不存在**。`main/lib/desktop-management.js` 的 `start()` 首先调用 `installedResources()`，后者首先对 control exe 执行 `exactFile()`；按当前生成树，首次静态可确定的阻塞为 `INSTALLED_RESOURCE_UNAVAILABLE`。本次未运行入口，因此这是源代码与产物树的确定性推导，不是原生启动观测。

生成树还缺 `migrations/sqlite`、`spec/v2.0/contracts/domain.schema.json`、`internal/api/contracts/client.protocol.schema.json` 等 Core 工作目录输入。`spec/v2.0/contracts/openapi.json` 已在树内。Core 启动所需完整资源仍须按其实际 cwd 读取合同单独核定。当前 build-validator 接受外部已安装 Electron 二进制作为构建输入，却不生成 installer 或将 Electron 复制到产物树。`desktop.installer_build` 仍 `UNBOUND`；本回执不表示 W20-01、W13-03 或任何正式用例通过。

执行边界：没有启动 Electron GUI、Core 或原有 Desktop，没有读取原业务数据、凭据、ACL，没有联网安装，也没有写 Main、C57、共享卡状态或规范源码。下一步的最小源码工作须另获 Root 的精确 scope，补齐独立开发树的 Core/运行资源与工作目录合同，并用新状态目录执行受控原生观察。
