# 一次性有限决策

状态 FINITE_BLOCKED_NO_IMPLEMENTABLE_SOURCE_CARD_YET；不是永久不可施工。57个路径已完整列出，具体接线与失败边界已冻结，但实际阻断目标、完整入口与可信管理/恢复资源未定值，故不能签发“可实施且覆盖实际旧包”的完整Source卡。资源mapping绝不升格为完整launchsurface证明。

一次性所需资源见minimal-resource-package.md：
1. Root另行只读取得完整官方启动图、目标native identities/hash/ACL/ancestor/有效token、当前Windows支持范围、在线备份生产接口合同；
2. 确定可信管理部署/恢复主体，保证普通产品token不能改围栏，支持所有正常官方入口有产品专属必经阻断文件；
3. 若全部成立，可直接把现有设计定值为精确Source卡，**无需提前执行真实fence或Restart**。DACL有效阻断、crash/rollback、跨Restart、真实安装入口均是未来Source/native fixture与actual资格门槛，不是读资源阶段必须已经存在的证据。

资源齐全仍不保证本机制适用：任一入口没有可冻结专属文件、普通官方更新路径能绕过、管理/恢复权限无法安全区分、或同SID可信假设与真实合同冲突，则本机制明确退出。本轮不自动转向系统服务/驱动/全机策略；Root保留此支路BLOCKED，只推进独立支路。旧Wait无法恢复，Core-only不足，新根不能替代旧根。

单独依赖：ONLINE阶段需要另行接受、能在旧Core持lease时工作的可用一致性backup生产接口。没有该接口可为其另行定卡，不得偷偷复用需要exclusive lease的C backup/upgrade。actual backup与恢复可用性在arm前证明；不能为补备份抢lease/停Core。未来一次明确用户FullRestart窗口不可由代理代替，但本轮不向用户询问。

作者交付不构成设计接受；Root须安排独立设计审查。actual_authority=false，formal_increment=0，旧失败/ACK/费用/UNKNOWN/父任务全保留。

