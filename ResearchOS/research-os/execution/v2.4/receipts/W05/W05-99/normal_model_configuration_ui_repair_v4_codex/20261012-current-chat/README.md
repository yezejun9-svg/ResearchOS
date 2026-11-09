# W05 Desktop 模型配置 UI repair-v4 候选

隔离 worktree：`D:\作品集\ResearchOS\research-os\.local\worktrees\w05-normal-model-ui-repair-v4-20261012`。基线为冻结的 v3 候选 `2f48ad7d4cd3cececf06a2a9a059a36ba157032c`；本候选提交 `57ec9b4408835483bf0c4c30397968d7a11a0b2c`。仅修改 `apps/desktop/main/lib/ipc.js`、`apps/web/src/workbench.jsx`、现有 `tests/ui/desktop/http-wire-boundary.test.mjs`；Main 产品源码、Core、CLI、Canon 和旧候选未改。模型调用、外部调用均为 0。

本次修复 v3 独立审查发现的跨 Host 误确认：主进程从可信 native discovery 的 `host_instance_id` 与 `data_dir` 生成仅本地使用的 Host 身份，随 `host.status` 与原 `host.configure` 结果返回；renderer 只有在原命令回执、当前 Host 身份、五个公开配置字段、修订及模型引用都吻合时，才展示“已保存”。原 Host A 命令在途时切到 Host B，即使 B 返回同一修订、字段和引用也保持锁定；回到 A 且端口/PID 变化后，可核对原命令，不产生第二次新配置。`STALE_RESPONSE` 保留原 Host 的可信终态结果供精确核对。`NOT_SENT` 只解除当前未发出的配置意图，不清除另一条已在途的 shell 屏障。

最终完整输入绑定构建的原始日志在 `final-bound-build-log/`，官方 `result.json` 为 `BUILT_NOT_TESTED`、`drift: []`，输入摘要 `392035ec6070865a2613ddbc43e777bbd732d9a1e31e46910a67419f837dcd77`，Go validator 二进制摘要 `b894eb2d6f5c67f49b491df92b01c5c03d7eb4bfc831437b422053359dc9ed7e`。绑定构建曾因稀疏 worktree 缺少 Go 包目录失败 4 次；原始失败日志保留，不作为通过证据。最终 46/46 Desktop 边界测试、5/5 W13 回归通过。`final-bound-dom/` 的实际 Chromium DOM + 本候选 IPC + 最终绑定 Go validator + 合成 HTTP 回归，原 5 场景和跨 Host 6 变体通过；第一次 DOM 运行缺少复制的 test-entry，原失败日志保留。正式接受、真实 Electron/Core 正常用户流与本地模型运行时资格仍未由这些合成 HTTP 证据证明。

`final-bound-dom/host-race-results.json` 中脚本继承了早期 `current_v4_full_build_binding: false` 字段；该字段对最终重跑已过时。最终重跑使用的 `RESEARCHOS_DESKTOP_WIRE_ROOT`、构建摘要和校验记录见 `final-bound-audit.json`，不要据该旧字段判断绑定状态。收据下 `final-bound-dom/vite-cache/` 是测试临时缓存；定向递归删除被自动审批审查以 `blocked by policy` 拒绝，故保留，未纳入证据清单。没有尝试绕过审查。
