# 实际资格调用前边界审查

结论：草案可作为准备边界；尚未具备执行或 PASS 证据。Main c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0 与草案哈希已绑定。只读原数据仍为工作区 rev2、模型配置 rev1、0 Session/资格计划/Run/dispatch/effect；当前两条预算策略符合 UNKNOWN/null + UNLIMITED_AMOUNT/ALLOW_AND_RECORD，但实际 Run 的完整祖先链仍需重新绑定。

真实资格入口是 workbench.jsx 的 Chromium window.confirm，经原管理管道 CONFIRM。coding 配置的 Main 原生 consent 是另一流程。Root 继续使用普通 UI 创建/附着会话、PREPARE、明确确认及 STATUS，不直接构造 IPC/API。

PREPARE 有效60秒；应提前完成静态build、SDK和观察器准备，UI准备后快速采原始 request/id/hash、Session/config/Owner/预算并登记。Run id/epoch与含它们的真实 request/prompt hash 仅在 CONFIRM claim 后产生，不能提前编造。600秒是用途授权期限，不是确认有效期或worker超时。

evidence-matrix.json 列明 SQLite、SDK、Broker、Windows Job、native verifier 与 normalExit 的生产取证路径和缺口。Broker effect历史+原始SSE+SDK结果交叉确定调用，空Ollama日志不证明0。真实verifier需安装字节、PID创建时间、独立应用lineage、server AcceptanceReceipt和当前purpose。其私有Result帧与stderr没有独立持久化路径，不能伪造或拿fixture替代。

next-root-artifact-plan.json 给出6阶段具体原证据清单。成功须原请求一次消费、MODEL1/TOOL0、worker原生收尾、真实verifier/server接受、当前STATUS资格及UNKNOWN账目保留；任何断线/超时按原Run/effect/dispatch复核，不重复CONFIRM。正常退出须原进程观察与生产quiesce路径，不能凭窗口消失/空日志或清空UNKNOWN账目判成功。

本次没有修改Source、Canon、build或Root数据，没有GUI/模型/工具效果；没有自签正式接受。新coding配置及其另一资格、普通8MODEL/32TOOL任务不在本草案授权内。
