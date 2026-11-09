# W05 Desktop 模型配置 UI repair-v5 候选

基线为冻结 v4 提交 `57ec9b4408835483bf0c4c30397968d7a11a0b2c`；隔离 worktree 提交为 `1c761174cabdd5be6fc95218eeaa502cd8c6c3f1`。本轮只改主进程 `apps/desktop/main/lib/ipc.js` 与现有边界测试，Main 产品源码、Core、CLI、Canon 和既有收据未改。`source/` 与 `cumulative-source.diff` 冻结从 `292ad860` 起的七个累计文件；其中六个进入完整构建输入，`tests/ui/continuity/surfaces_driver.js` 未进入构建输入，详见 `source-manifest.json`。

修复 v4 独审的 `W05-UI-V4-001`：`host.status` 在异步凭据获取之后、完整 validator/HTTP 调用之后，重读可信 native discovery，比较原 Host 的 `host_instance_id + data_dir`。若当前已切到别的 Host，返回明确错误，不把原 Host 的状态交给界面确认为“已保存”。同一逻辑 Host 更换 PID 或端口仍允许返回。原 `host.configure` 的在途命令和界面 pending 意图不会被清除；旧 `NOT_SENT`、possiblySent 与跨 Host 写屏障保持原语义。

`final-bound-build-log/` 是官方 `build-validator.py` 原始日志：`BUILT_NOT_TESTED`、`drift: []`、6424 个输入、构建摘要 `055b84beaf269fcc8b9a4e055e93196e9ff62f8b44203a9922d146554533dfae`、Go validator 摘要 `ba25b1dc569e6d3be910eeab1d4beaebd55db6c8b5e2dbce4b172e927338999a`。`binding-audit.json` 核对源码快照与构建清单。绑定边界 26/26、W13 5/5、原独审三条实际 Chromium 反例 3/3 修复；原五条命名页面场景及一条附加 finding、六条跨 Host 变体亦通过。DOM 使用合成 HTTP；本轮实际模型调用及外部调用为 0。首次 Chromium 运行因新收据缺 test-entry 超时，`status-race-fixed.log` 保留原失败，补齐相同入口后 `status-race-fixed-attempt2.log` 通过。

这是供新独立审查的源码候选与本地合成 HTTP 证据；没有声称真实 Electron 正常用户流、本地模型资格或 W05 正式接受。没有把此前 continuity parity `66/69` 写成整体通过。
两处 Vite 临时缓存（`vite-cache/`、`status-race-cache/`）的定向递归清理被自动审批审查以 `blocked by policy` 拒绝，现保留在收据目录，未换方法绕过；它们不作为通过证据。
