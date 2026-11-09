# 原生生命周期驱动 v3：待独立审查

`driver-v3` 只改变 `run-owned.py`。`lifecycle.mjs` 和两份 PowerShell 脚本与已审 v2 逐字节相同，全部 SHA256 见 `PREPARATION.json`。本轮没有启动产品、GUI、Core 或 CLI。

控制器退出码非零时，wrapper 先写 `exit.json`，再写 `WAITING_FOR_ROOT_RECONCILIATION.json` 并保持自身进程存活。它不发关闭消息、不重启、不杀进程。正常退出码 0 时沿用 v2 直接结束。此改动仅为 Root 排查留下外层进程；attempt-02 中 Electron／Core 消失的原因仍未观察到。

Root 后续只可在 `outer_receipts_root` 新建一次 `ROOT-RELEASE.json`。文件必须逐项复制等待记录中的 `scope_sha256`、`outer_pid`、`controller_pid`、`controller_exit_sha256`、`release_nonce` 与 `known_product_identities`，并写入 `schema="researchos.native-driver-v3-root-release.v1"`、`root_confirmed_identity_absence=true`、晚于控制器退出的 `confirmed_absent_at`。Root 先独立确认列出的产品 PID 已不存在。任一字段不匹配，wrapper 持续等待。

wrapper 从受绑定安装包的 `installed-product.json` 枚举全部六个 `.exe` 路径；从控制器 `UNRESOLVED.json` 中的活跃 child 与 witness 派生已知 PID、镜像、创建时间，不能接受 Root 自填的空列表。release 出现后，它用只读 PowerShell 连续扫描两次，间隔两秒。已知 PID 仍存在、PID 被复用、任一安装包镜像仍在运行，或进程身份无法读取，都会继续等待。两次均无阻塞时才写 `ROOT-RELEASED.json`，以控制器原始非零退出码结束。release 只授权 wrapper 结束，不授权它处理产品进程。

静态验证：Python 编译 2 次、Node 语法检查 1 次、内联 PowerShell 脚本解析 1 次，均通过；纯模拟 7 项通过。只读解析 attempt-02 回执得到 6 个安装包可执行文件、已知 Electron PID 66940 与 Core PID 64080。实际 v3 运行、进程扫描和外部工具宿主生命周期仍待验证；正式验收增量为 0。
