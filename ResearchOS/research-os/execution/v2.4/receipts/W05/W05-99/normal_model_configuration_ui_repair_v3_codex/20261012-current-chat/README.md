# W05 Desktop 模型配置 UI repair-v3 候选

隔离 worktree：`D:\作品集\ResearchOS\research-os\.local\worktrees\w05-normal-model-ui-repair-v3-20261012`。基线是冻结的 v2 候选 `9602f61c05325fc9bd1b523398a8f9721eded72e`；本候选提交 `2f48ad7d4cd3cececf06a2a9a059a36ba157032c`。仅修改 `apps/desktop/main/lib/ipc.js`、`apps/web/src/workbench.jsx` 和现有 `tests/ui/desktop/http-wire-boundary.test.mjs`。Main 产品源码、Core、CLI、Canon 与旧候选均未修改。

修复两项独立审查指出的边界。模型配置命令的公开 payload 与终态保存在同一 renderer 生命周期内可订阅的项目状态中；旧组件在请求在途时卸载后，新组件会收到完成结果。若 IPC 返回 `STALE_RESPONSE`，只有 `host.status` 中存在与原五字段及配置修订完全一致的记录，页面才展示保存成功；无法证明时保留原意图并继续锁住输入，核对动作不产生第二次 `host.configure`。主进程把待重放命令绑定到可信发现文件中的原生 `host_instance_id` 与 `data_dir`；端口/PID 改变可重放，切换实例或数据目录时拒绝向新 Host 重放并保留屏障。获取凭据后、传输前再次读取发现文件。

验证：`desktop-boundary-expanded.log` 42/42，通过 23 个协议方法完成态、模型配置、ACK/不确定屏障、Host A→B→A、凭据期间换 Host、初始配置和活动 session 范围。`dom-final3.log` 与 `reviewer-dom-results.json` 是实际 Chromium DOM + v3 IPC + 已有 v2 Go validator + 合成 HTTP 的五条场景，包含原 P1 在途卸载反例与无法确认保存时的锁定反例；原 P1 路径只有一次配置 HTTP。`web-build-final2.log` 是最终 React/Vite 生产构建，`ipc-syntax.log` 与 `diff-check.log` 通过。模型调用与外部调用均为 0。

证据等级为本地合成 HTTP 和 Web 构建。边界/DOM 测试复用了冻结 v2 的 Go validator 资源，因此**不是** v3 源码全输入绑定构建，也不是正常 Electron/Core 端到端配置、运行时模型资格或 W05 正式接受。`web-dist/index.html` 指向最终 `index-Bnv9NRkJ.js`；目录中还保留较早构建的 `index-DYUHP8xp.js`，它不被最终入口引用。初次 DOM 扩展测试因合成响应的 `RESPONSE_IDENTITY` 无法用于预期 `STALE_RESPONSE` 场景，已修正响应生成器并保留原失败日志。前一次构建失败于稀疏 worktree 缺少 `design-tokens.json`，补入原版文件后成功。

自动审批审查拒绝了对隔离 worktree 临时构建目录的递归删除，之后对收据中旧单个构建文件的删除也返回 `blocked by policy`，无更细说明。因此临时输出保留在 worktree，收据中旧文件保留但不属于最终入口。`receipt_manifest.json` 记录本目录文件哈希。
