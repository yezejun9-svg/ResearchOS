# 2026-10-25 只读 DAG 与下一支路盘点

结论：当前没有可以直接登记正式接受的下一张卡。`task_packet.py next` 在当前 `VALIDATED_FILE` 上选出 `W05-99`，其输出明确 `read_only: true`、`product_acceptance: NOT_ASSERTED`；它是当前指针，并不证明原 C57 数据恢复、真实 Host 链或正式验收已具备资源。独立可执行的首支路只有 **Main `7d1e3ff` 的原生 Desktop 开发产物源绑定构建预验证**。它只能形成 `DEVELOPMENT_ONLY / BUILT_NOT_TESTED` 证据，不能登记 W20-01 或 C/A 用例通过。

## 依据

本次读取 `execution/v2.4/current_spec.json` 指向的 `.local/worktrees/v24-continuation/spec/v2.4/contracts/execution.plan.json`、当前 `step_state.json`、`commands.json`、`path_ownership.json` 和 CP550 `RESUME.current.json`。各自 SHA-256 在 `dag-overlay.json`；计划 SHA-256 与状态的 `plan_sha256` 一致。机器视图为 71 卡、46 条状态（41 `ACCEPTED`、4 `BLOCKED`、1 `IN_PROGRESS`）。所有直接依赖已接受而自身未接受的仅 `W10-02`、`W11-02`、`W13-03`、`W14-01`、`W05-99`；四张子卡各有已记录阻塞，W05-99 缺原 C57 正向完整链和真实运行资源。未重试这些分支，旧失败计数未动。

`W20-01` 当前无状态记录，直接依赖 `W13-03` (`BLOCKED`)、`W17-03` (无状态)、`W18-02` (`ACCEPTED`)。`W17-03` 又依赖 `W13-03`。W20-01 卡还要求干净 Windows 用户或 VM 中的真实 CLI/Desktop 安装、升级、卸载和数据保留；`desktop.installer_build` 为 `UNBOUND`，`release.reproduce` 不在当前命令表。`desktop.shell_launch` 也为 `UNBOUND`。因此目前不能以现有开发树替代安装产物或卡接受。`W13-03` 的物理 NVDA 前台与此前独立工作区审查阻塞仍保留；React Main 交付说明也明确原 Desktop/Core 未切换。

## 可执行首支路：隔离的 Desktop 构建与入口盘点

输入固定 Main `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`，在新独立 worktree 内运行 `apps/desktop/build-validator.py`，仅写该 worktree 的新 `.local` 输出和新回执。工具参数使用 `execution/toolchains/locked.json` 已登记的 Go `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe`、Node `C:/nvm4w/nodejs/node.exe`；Electron 可用文件 `apps/desktop/node_modules/electron/dist/electron.exe`、Vite 模块 `apps/web/node_modules`、Go 模块缓存 `.local/tools/gopath/pkg/mod` 已在本次做路径存在检查，实际文件哈希由构建器再验。不要运行已登录原 Desktop/Core 或指向原业务数据目录。

建议在新 worktree 中按以下参数构造唯一新目录；实际绝对路径和锁定工具哈希写进独立构建回执后再执行：

```text
python -B -X utf8 apps/desktop/build-validator.py
  --go D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe
  --node C:/nvm4w/nodejs/node.exe
  --electron D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe
  --module-cache D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod
  --web-modules D:/作品集/ResearchOS/research-os/apps/web/node_modules
  --output <new-worktree>/.local/desktop-main7d-build-<id>
  --receipts <new-worktree>/.local/desktop-main7d-build-receipts-<id>
```

该脚本会独立编译 React 资源、Go validator，生成资源清单与输入散列，并明确写 `BUILT_NOT_TESTED`。随后只读检查生成树与 `apps/desktop/main/main.js` 的运行入口：当前 `ROOT=apps/desktop`、`REPO=ROOT/../..`，`WEB_DIST=REPO/apps/web/dist`，默认 Core 与数据目录也从 `REPO` 推导。这个布局适用于仓库内开发树，却不足以证明安装后脱离源码目录可运行。`apps/desktop/resources/control/researchos-control.exe` 在当前 Main 不存在，`ops/release/build.py` 是开发 zip 构建器，不能当 W20 安装器。预验证的交付是**相对路径、随包 Core/运行时、入口/卸载/更新缺口清单和源绑定构建证据**，然后由 Root 依据 W20 依赖与路径所有权另定最小实现范围。

边界：此次只盘点，不修改 Main、卡状态、命令注册、源文件、原数据、ACL 或进程；不把 CP550 的旧 `live_core_pid`/`live_desktop_pid` 当现态。Root 新资源审查显示旧两 PID 均已不在，但没有证明系统不存在其他 Core；当前也没有已验证不同 SID 的提升管理主体。该资源缺口只阻塞原 C57 正向 Host/恢复链，不阻塞上述隔离构建。

## 回执

- `task-packet-next.recipe.txt` 为运行前命令；`task-packet-next.stdout.raw`、`.stderr.raw`、`.exit.txt` 保留原始输出，退出码 0。
- `derive_dag.py` 为只读状态与依赖推导，`dag-overlay.json` 为机器视图。首次运行脚本因 receipt 层级取错而 `FileNotFoundError`，改正为第 7 层后推导成功；该开发诊断不影响源状态、卡或正式计数。
