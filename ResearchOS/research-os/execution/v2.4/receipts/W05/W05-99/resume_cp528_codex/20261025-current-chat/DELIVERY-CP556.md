# CP556：React 工作台与 Desktop 开发入口已整合到 Main

当前 Main 为 `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`，tree 为 `1d44a02c9483fc529b08ffe81895ec443920bdd1`。本轮从已交付 React 改版的 `7d1e3ff` 本地 fast-forward，精确引入七个文件；没有 push、部署或切换原业务数据。

React 工作台已包含项目导航、主任务区、右侧状态区及深浅色适配。此次补入 Desktop 完整开发构建器、隔离启动入口、启动与退出验证及直接开发测试。

- [开发构建器](D:/作品集/ResearchOS/research-os/apps/desktop/build-development.py)
- [开发启动器](D:/作品集/ResearchOS/research-os/apps/desktop/launch-development.mjs)
- [构建和使用说明](D:/作品集/ResearchOS/research-os/docs/installation/desktop-development.md)

下面是此前真实隔离 Core 浏览器验证中的 React 工作台截图；不是本轮 Desktop 原生运行截图。本轮七文件差异没有修改 Web 源码。

![React 研究工作台](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat/real-isolated-03/real-project-workbench.png)

## 验证与保护

整合前独立复核确认七路径无碰撞，六个新文件不覆盖 Main 文件；整合后独立复核确认 Main 提交、tree 和七个磁盘文件与候选完全一致。索引为空；原 20 条 tracked dirty 状态、48 项保护引用保留，三个共享状态文件按检查点推进。不能将包含原有改动的整个 Main 工作树视为干净候选。

此前同一候选完成完整开发构建及一次真实隔离原生验证：React 页面挂载，10 个导航入口，private management READY，真实 native `host.status` 为 COMPLETED，随后同一 Core 身份确认退出，两个所属进程 PID 均被记录为不存在。该证据已独立接受，但仍绑定原隔离构建位置与那次运行；本轮没有在 dirty Main 重跑构建或启动业务程序。

- [整合前独立复核](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_independent_review_codex/20261025-current-chat/main-integration-preflight/MAIN-INTEGRATION-PREFLIGHT.md)
- [整合后独立复核](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_independent_review_codex/20261025-current-chat/main-integration-post/POST-REVIEW.md)
- [CP556 限定采纳](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp556/Desktop-Main-integration-limited-adopted.json)
- [真实隔离 Desktop 原生验证](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/owned-native-desktop-smoke-01/native-proof.json)
- [原生证据独立复核](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop_main7d_independent_review_codex/20261025-current-chat/native-proof/NATIVE-PROOF-REVIEW.md)

`desktop.shell_launch` 和 `desktop.installer_build` 仍为 UNBOUND，`release.reproduce` 尚未登记；新增直接测试不等同于 W13 dispatcher 的正式覆盖。此交付是开发入口，未接受安装、升级、卸载或完整业务流程。

## C57 与续跑状态

Source43 和 C57 的既有限定源码接受保持原边界。C57 `03aa4d6` 工作树仍干净、冻结，未合入 Main。用户明确表示正在准备独立管理员会话，状态为 `USER_PREPARING_NOT_VERIFIED`；会话可用后先核对真实 SID、提升状态和所需权限，再限定真实恢复测试范围。同 SID 提升进程不能替代不同身份恢复测试。

没有操作原数据库、凭据、ACL 或原进程 STOP/重启；没有清除原失败、旧 Wait/exit124 或被拒绝的清理记录。混合诊断账本从 2244 追加到 2251，新增项属于只读查询或工具协议诊断，不能称为 7 次产品失败。此前临时 Git index 删除被自动审批拒绝，文件与拒绝记录继续保留，未重试。

当前 checkpoint **556**、ownership **342**。只读选择器返回 `VALIDATED_FILE`、W05-99、`product_acceptance=NOT_ASSERTED`。正式接受仍为 **0/42**，**22 个父任务全部未关闭**，总体 Goal 仍活动。

[最新续跑记录](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp556/RESUME.current.json)

本轮分类：PROGRESS。实际成果为七文件 Main 整合、前后保护验证、独立整合接受和持久检查点；没有将等待管理员会话计作验收进展。
