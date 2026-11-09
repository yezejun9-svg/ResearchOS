# Desktop managed qualification client 独立审查

**REQUEST_CHANGES**，候选 `fc350c97cddbf7d54e37b88ece25b0e8be8f1d87`，两项 P2。

1. PREPARE 后切换会话或权限 generation，未确认请求即使已过 TTL 也无法恢复：STATUS/CONFIRM 因 context 拒绝，新的 PREPARE 因旧 intent 拒绝。页面隐藏原 request ID，复核按钮禁用，准备按钮只能再次报错。
2. 主机切换后，`qualificationCurrent` 仍可返回旧主机 `authorized:true`，因为 summary 只验证会话 context。后续执行接口仍会拒绝 HOST_CHANGED，因此未宣称已发生越权执行。

两项均有最终绑定模块与实际 Chromium DOM 反例。见 `independent-review.json`、`lifecycle-edge-results.json`、`lifecycle-dom-results.json` 和两组 DOM/截图。

6491/6491 绑定检查通过，包含全部6435构建输入与最终8文件。管理边界7/7、原 UI v5 边界23/23通过。实际最终 Electron 缺安装 smoke 显示 React 挂载、RESOURCE_UNAVAILABLE、spawns0；真实冻结 Core 耦合仅 READY、OWNER_NOT_INITIALIZED 的 PREPARE 拒绝、SHUTDOWN并确认退出。没有 CONFIRM、模型调用或 native 正常首用到资格成功的 whole flow 接受。

0 actual model / external / public tunnel，formal/parent +0。nvm shim 原失败及 canonical Node 成功观测均保留；未改 Main/Canon/候选/旧证据，未杀生产或作者旧 fixture。Vite缓存定向删除被自动审批审查 `blocked by policy` 拒绝，保留并排除证据清单，未换工具绕过。
