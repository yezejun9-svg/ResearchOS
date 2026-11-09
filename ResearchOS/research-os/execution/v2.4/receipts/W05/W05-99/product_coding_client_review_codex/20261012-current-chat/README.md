# Desktop coding client 独立审查

**REQUEST_CHANGES — Source + fixture**。候选 `eb7f712d21268c87f9af9428048313c9361c52d6`，登记8路径、实变7文件。

四项反例已复现并保留原始证据：

1. **P1 / 001：缺少主进程明确确认。** 同origin renderer可绕过页面确认，直接调用最终bound IPC发送原CONFIRM并得到CODING_CONFIGURED。
2. **P2 / 002：共享pending期间提前退役。** 原请求真实过期并STATUS确证后，第二STATUS尚未返回时prepare先清codingIntent，再报MANAGEMENT_COMMAND_PENDING；late reply之后已无法复核原请求。
3. **P2 / 003：PREPARE期间切会话丢原请求。** 原结果到达后在保存id/hash之前抛CONTEXT_CHANGED；返回原会话可另发PREPARE，旧id/hash不在active或history。
4. **P2 / 004：STATUS恢复提交结果未刷新V2视图。** 实际bound React DOM在确认结果不确定后复核得到CODING_CONFIGURED，但刷新回调仍为0。

8183/8183绑定检查通过，包含6439完整构建输入、1699冻结证据、7份Git源码及bound模块/UI资产。独立复跑原6个coding边界测试通过；另3个bound IPC/manager反例及1个实际Chromium DOM反例成立。负例脚本exit0表示成功复现缺陷，不表示候选通过。

本轮真实模型/工具/外部/付费/隧道调用0，formal/parent +0。没有控制主线程浏览器或进程。主线程现有host.status revision与Native3目录选择阻塞属于另行修复的真实首用支路，不归入本候选7文件，也不能据本轮宣布完整流程通过。

新Vite缓存定向删除被自动审批审查以 `blocked by policy` 拒绝，保留并排除清单。另一次误操作创建的仓库旁空文件已立即删除；残留带前导空格的空目录清理同样被拒绝，真实仓库未受影响。两项均未改用其他删除方式。
