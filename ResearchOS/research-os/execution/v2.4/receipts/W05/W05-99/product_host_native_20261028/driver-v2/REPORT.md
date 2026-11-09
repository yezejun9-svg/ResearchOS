# 原生生命周期驱动 v2：待独立审查

已在本目录准备 `lifecycle.mjs` 和 `run-owned.py`；两份 PowerShell 辅助脚本从原目录逐字节复制。业务断言、CLI／桌面／重开链路保持原样。旧目录四份源文件未修改，源文件与新文件 SHA256 均见 `PREPARATION.json`。

Electron 现在由 `child_process.spawn` 直接启动，原始 stdout/stderr 从启动时写入独立文件，立即登记 PID、`error`、`exit`，并 `unref` 子进程。只从该子进程的 stderr 提取 `ws://127.0.0.1/.../devtools/browser/...`，用 `chromium.connectOverCDP` 附着唯一 `ros-app://desktop/` 页面。正常关闭通过原样复制的 `close-owned-window.ps1` 按 witness PID、创建时间、镜像和 SHA256 校验后发送 `WM_CLOSE`。失败时保存总体和每个未终止子进程的 unresolved 记录及当前 witness，只断开 CDP，不关闭或终止产品。

本机 Playwright 1.58.0 的 `lib/server/chromium/chromium.js:77-125` 显示，CDP 附着模式的 `close`／`kill` 只调用 WebSocket transport 的 `closeAndWait` 与临时目录清理；该驱动没有把启动的 Electron 进程交给 Playwright。新 wrapper 和 controller 都要求未来的 Root scope 逐个绑定本目录四份驱动文件。

验证：`node --check` 2 次、Python 静态编译 1 次，均通过；本轮 native／GUI／Core／CLI 启动 0 次，模拟运行 0 次。已读既有 `attempt-01` 的 1 次失败记录。下一步是独立源码审查、绑定新 scope，再决定真实运行。旧记录中的 `PRODUCT_PATH_TYPE` 属于产品加载错误，驱动替换没有证明它已解决；正式验收增量为 0。
