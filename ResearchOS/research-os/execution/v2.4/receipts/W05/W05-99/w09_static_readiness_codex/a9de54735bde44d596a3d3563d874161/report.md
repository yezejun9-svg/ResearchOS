# W09-99 静态接续卡

当前 W09-01、W09-02、W17-01、W03-99、W07-99 均已在 step_state 登记 ACCEPTED，W09-99 未登记，依赖上可推进；父任务 W09 和正式 C19/A06 仍未接受。C02 只是关联回归，最终 owner 为 W17。

W09-99 的冻结入口共 6 条：W09-G01/G02 各 1 条，C19 两条，A06 两条；W09 子卡另有 2 条。当前 v2.4 命令登记包含同名 key，却没有这些 W09-99 的精确 selectors。dispatcher 在 current_spec=v2.4 且 plan hash 对齐时优先选 v2.4，不能回退调用旧版 W09 同名 handler 视作正式验证。

已有 domain Evidence/retrieval/local-root/FTS 与 Go 断言源码；W09-01/02 的独立复核留有限制，且 W09-02 post-review 记录了纠正。Root 下一步先按冻结 task_packet.py 的 show W09-99 实际读包，再由登记 owner 让当前 v2.4 入口能真实运行冻结断言与 G02 本机 Windows 检查，独立复核后才签收。task_packet 未在本盘点中执行。

C19、A06 是 FIXTURE；W09-G02 需要真实本机 Windows 文件验证。B01 严格费用门只挡付费 provider LIVE，不挡这些本地工作。Sirchmunk 当前仅 NOT_SELECTED；需固定源码资格或明确采用已规定 FTS/rg 替代并留证。

本报告只读，没有运行 Git、task_packet、dispatcher、Go、CLI、provider 或产品，也没有领取 lease、修改源码或 canonical；新增正式接受数 0。
