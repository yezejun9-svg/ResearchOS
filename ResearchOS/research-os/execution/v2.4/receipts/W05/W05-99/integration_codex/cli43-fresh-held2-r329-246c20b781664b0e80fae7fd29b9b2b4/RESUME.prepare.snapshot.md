# ResearchOS r329 续跑快照

实际 canonical 仍为 CP328 / OW156 / 469首因；r329草案已准备，待独立复核后由 Root 唯一 CAS 写入329 /157 /481。固定12条cut保留，另3条晚到首因在cut外，报告观察总数484。

上一轮13次native均0，首例测试叶运行成功但HTTP requested缓冲区引用导致SHA证据不合格，第二例未启动；原scope/grant已消耗，不得重跑。新的即时bytes.Clone修正已通过独立源码复核，须全新授权与产物执行。

下一步按本目录实际scope、草案及独审继续：Root run → seal → grant → 新caller独审 → 一次launch → 实际闭合与独立资格复核。保护旧11处删除、空index、a510 HEAD及全部旧失败。22父任务和42正式用例未全部有效接受，目标仍未完成。

F08 driver17、I17与SQL24仍未实际验证；Desktop15尚未导入。误写metadata脚本清理曾被自动审批以blocked by policy拒绝，文件保留，不换工具绕过。
