# V1 Workbench 独立 QA 准备

只读依据是已登记scope、Root冻结的Harness rev2和D03。作者未冻结，未读取候选变动源码/测试，也未运行它们。

24条反例见matrix.json，全部NOT_RUN。优先级为：UNKNOWN pending不重发、作用域/迟到隔离、int64/游标、窄IPC和凭据边界，再核queued/cancel状态与诚实能力、旧Mu兼容及草稿。真实IME/窄屏/reduced-motion和模型资格需Root另scope，不用pure/build通过替代。

注意：can_submit是Host对本次有限任务的策略结论，与metadata和verification独立。QA不能自创“verification未测必定can_submit=false”的协议；但不能因此显示READY或把平台策略写为已验证隔离。hooks/mcp须标PLATFORM_POLICY。

冻结后先校验10源pins再读源码、stage、运行独立fixture/必要build；不修改作者代码/测试，不恢复旧Core/capture、不运行真实CLI/Native/模型/旧DB。任何失败保留首次raw和来源计数。当前所有产品验收仍未验证。
