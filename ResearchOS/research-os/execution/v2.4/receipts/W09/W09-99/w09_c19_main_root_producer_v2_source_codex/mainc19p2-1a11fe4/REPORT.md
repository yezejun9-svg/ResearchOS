# Main C19 producer v2 — Source cleanup correction

修复 MAIN-C19-PRODUCER-01，绑定 v1 非作者 REQUEST_CHANGES 的完整 HDF/MF。旧 Source、952 原始失败、Main 七目标、Canon 和实际目录均未修改。新 run 为 9e912dfc1058454da08ae7f93f4de24d；全部 caller/module/launcher/choice/contract refs 已重绑。七目标与21项 Source roster、toolchain、351包蓝图、两项测试、240/420/180超时和 one-shot 约束不变；蓝图字节相同，只作有限编译输入清单。

receipt presence/pin/read/decode/closure 检查及 packet archive 各自捕获错误；逐 guard close 位于外层 guaranteed finally。每项 close、闭合状态判定、cleanup-save 分开隔离，保存失败不抹掉成功关闭的原始 observation。关闭后的 Job 状态取自已保护的观察，不再无保护重读 receipt。缺失、部分 JSON、不可读、pin 失败或不一致都不能证明 Job 已关闭。

invoke 保存 helper 原异常对象与异常链，stdout/stderr pin、invocation-save、progress 输出错误单独聚合。stage 同样保留 primary exception、invocation diagnostics、inspection/archive/close/save 分类；final-save/progress 失败不能遮蔽 primary。尚未创建实际目录时直接输出未保存诊断，不额外建目录；输出也失败时异常文本仍携带原错误与次级分类。私有 launcher 的 UUID 还原、观察、pin、closed-save 同样隔离并保留原 runner 异常。任何失败停止，不自动重跑，不覆盖部分原始文件。

113项最终新纯 Source 控制通过：重现旧 finally partial JSON 导致零关闭；新路径覆盖 missing/partial/unreadable/pin/presence、archive、首个/中间 close、异常 cleanup observation、cleanup-save、多重组合失败；五个 guard 关闭动作始终全部尝试。实际新 stage except/finally/postlude 的内存执行证明 primary identity/cause 保留、未知 Job 不被报 closed、final-save/progress 错误归入 secondary。invoke 精确原始 bytes/FILETIME、一调用无重试、launcher异常保全，以及未建目录的失败输出均验证。v1的107与v2初轮109只作历史，不累加为最终控制。

4047项原输入 pin 不变；准备、初轮控制、最终控制、封存的真实 Source guards 全部关闭，retained=0。Source工具均outer/Python0，无新增原始工具失败。952原始pair保持原引用；Root报告的953属于另一个独审，下一序号954，不重置。

本包仍为 SOURCE_READY_PENDING_INDEPENDENT_REVIEW，尚无Actual授权。未读取或持锁Root七目标/Canon，未执行Main producer、Go、Git、CLI、SQL、API、model、dispatcher。后续必须独立审查本v2，再由Root使用新的scope登记owner/worker及当前四文档vector；最低CP>367/OW>171不限定恰好CP368。实际producer和模式独审、两消费者及formal资格均待后续。formal_case_accepted_delta=0，W09 parent不变。
