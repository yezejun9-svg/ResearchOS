# W05 Desktop 模型配置 UI 修复候选 v2

此候选来自冻结的 UI 提交 `c12847d7ee7b37a15d875929738fe84fd7ba6964`，独立 worktree 为 `D:\作品集\ResearchOS\research-os\.local\worktrees\w05-normal-model-ui-repair-v2-20261012`，修复提交为 `9602f61c05325fc9bd1b523398a8f9721eded72e`。旧候选、旧收据、Main 产品源码及 Canon 均未修改。只改了 `apps/desktop/main/lib/http-wire.js`、`ipc.js`、`apps/web/src/workbench.jsx` 和既有 Desktop 边界测试。

修复对应独立审查的两个 P1 反例。全空白字段在提交前拒绝并保持可编辑；其他真正的本地预发送失败由 `http-wire` 在调用 HTTP 前标记 `dispatch_state: NOT_SENT`，IPC 仅当该命令从未可能发送且从未 ACK 时释放写入屏障。原命令一旦 ACK 或某次尝试可能进入 HTTP，后续重试即使本地预检失败也保留原屏障，避免重复副作用。UI 在同一 renderer 生命周期内按项目保存公开的五字段配置 payload 与输入，跨 Settings/工作台组件卸载与重挂恢复原输入，并让 IPC 以原完整 envelope 和 `command_id` 重放。缓存只持有 `credential_ref` 这个不透明引用，不持有凭据值。

最终源码绑定开发构建在 worktree `.local\w05-ui-repair-validator-final3`，其 `build_input_digest` 为 `922b4372ba936828d8835ed3a8fbdf88eb03daa761054d4522fd07e76ffbd6d8`，`validator-result.json` 报 `drift: []`。构建的原始编译日志、输入清单、描述符和命令记录均在本目录。现行锁定 Node 为 `C:\nvm4w\nodejs\node.exe`，SHA256 `5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6`。

`desktop-boundary-final3.log` 通过 16/16：其中 10 条模型配置相关路径涵盖预发送拒绝后的恢复、ACK 原 envelope 重放、已尝试发送后本地拒绝仍保留屏障、凭据失效前后不同处理，另含 ACK 和 validator 生命周期回归。`w13-react-final3.log` 通过 5/5。`repair-test-results.json` 是 Chromium 实际 DOM + Desktop IPC + source-bound Go validator + 合成 HTTP 的两条原始反例复测：空白值改正后成功；ACK 后组件重挂恢复同一请求，原始 `command_id`/envelope 完全一致。模型调用与外部调用为 0。浏览器脚本、HTML、DOM 和原始 HTTP 帧在本目录，可重复核对。

证据等级仍为本地/合成 HTTP；没有真实 Electron/Core 端到端配置成功，也没有运行时模型资格或 W05 正式接受。模块内恢复只覆盖同一 renderer 生命周期的组件重挂；整个 renderer 进程重启后还没有新的只读 shell pending 查询接口。真实 Electron 启动树除 source-bound `apps/desktop/resources/client-wire` 与 web dist 外，还须按原哈希具备 `spec/v2.0/contracts/openapi.json`；现有 `build-validator.py` 仅复制 `spec/v2.0/ui`。本候选没有修改合同或 validator inventory 来掩盖此资产缺口。

一次扩展测试把包含内部空格的 `provider_id` 错误地假定为 schema-invalid，等待错误提示超时。`clientIdentityLabel` 允许内部空格；该测试假设被撤回，`repair-test-final.stdout` 保留失败原文，之后的 final2/final3/final5 成功记录分别留存。由审查生成的 Vite 缓存保留于收据；先前同类递归清理已被自动命令审查拒绝，本轮没有改用其他工具绕过。收据 `receipt_manifest.json` 列明每个文件的 SHA256。
