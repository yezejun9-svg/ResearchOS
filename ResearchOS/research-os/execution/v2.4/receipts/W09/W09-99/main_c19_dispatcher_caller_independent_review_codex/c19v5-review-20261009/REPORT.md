v5 独立源码审查：REQUEST_CHANGES。

v4 三项实际反例均已关闭：Canon 实际登记与活动租约、精确独审绑定、Scope 精确字段集合。独立全 root_request 内存正例和针对性反例通过，当前静态输入与封存表也相符。

仍有一个连续性阻断：sealed_static_refs 只返回表文件 ref，未把表内八个已封存资源 ref 放入最终 SourceReadGuard。dispatcher/toolchain 在验证后又重新 pin，独立 AST 时序反例证明 A 检查通过后可把 B 当成实际期望和持锁输入。应返回并持有八个原 exact refs，expected_dispatch 直接从它们取值；后续漂移须在启动前失败。

原诊断 987/991 共两条保持 observed-only，987 不完整 stdout 未重建。没有新增原工具失败，没有 Native/dispatcher/provider 执行，没有 Source/Main/Canon 修改。SourceGuard finally closed、retained=0，正式验收增量 0。
