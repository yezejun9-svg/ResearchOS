# CP562 metadata envelope delta 的回归影响判断

结论：若实际 diff 仅对 v2EnvelopeFor 中 host.status / workspace.list 两个方法省略 SessionID、ExpectedRevision、WriterEpoch，并保留 ProjectID 与原 ctx 完全不变，则无需重跑 CP561 已通过的全部 7 项 ModelStream，也没有必须抽取的 ModelStream 代表。该判断等待实际 delta 复核；一旦改动扩到其他方法、输入解析或共享状态，必须重新评估。

静态路径依据：ModelStream 共享 testCLIModelStream 先以真实 CLI init 发送 workspace.register / project.bootstrap，随后启动无 argv 的 CLI，发送普通 stdin；cliInteractive 执行 session.list/create/send，follow / 取消走 session.events/control 等。模型 profile 在 fixture 内通过 queueCLIFixtureModelProfile /服务端API准备，而不是 CLI config 或 status。其生产 cli_flow / cli_stream 代码未调用 host.status 或 workspace.list。TestCLIModelStream 的七种输出/失败模式不改变这一方法路径。

CP562 应运行：新增 metadata envelope 单元矩阵，以及原 TestW18ContinuationStatusProcess 真实API/CLI子进程用例。矩阵需同时检验 metadata 省略三字段、保留 ProjectID、ctx不变、session读写的原revision/epoch语义和host.configure既有规则未改变。可结合已有同范围相关作用域测试；不为使统计全绿而重复所有ModelStream。

证据表达：原 exact7 的实际执行绑定冻结commit 5ee2c694ee275a72f40e8aa1d6c377d719fb8631，7 top-level与5 semantic子项通过。后续新commit只能引用此旧基线证明，并附本受影响分支分析和新的目标测试；不得称7项在后续commit下重新执行或抹去此前缺env失败。

CP562不放宽Core合同，不改controller忽略exit，不声称另一条CONTINUATION_HTTP_403已解决。本报告本身未运行测试或修改源码。