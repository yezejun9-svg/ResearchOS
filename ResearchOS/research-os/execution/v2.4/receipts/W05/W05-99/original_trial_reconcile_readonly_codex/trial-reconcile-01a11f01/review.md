原 trial 没有已核实的 provider 请求/返回回执；总数和费用仍为 UNKNOWN。原失败的 canonical-number 解码发生在 RunAdmitted 前，原本地记录为 Run QUEUED / Task RUNNING / dispatch PREPARED、epoch 1、空 worker/journal、0 observation/effect/ledger。这支持该调用没有进入已审查的 native dispatch 分支，不证明 provider 全局没有请求或费用。

现有 Source 的 ExecutePreparedAbandonmentMaintenance → AbandonPreparedQualification 是业务收尾切口：严格 Root/native authority、schema24、精确 revision/tuple/profile、空足迹条件下原子写 Run/Task FAILED 并留下不可变 tombstone。它强制 provider_requests=null、actual_cost=null、financial_closed=false，不发模型请求，也不释放预算。0024 schema 进一步固定 financial_closed=0 且禁止修改，因此它不能同时关闭 financial。

普通 reconcileRun 要求真实 observation/receipt，当前没有；ObserveEffect 只能用于已有 STARTED/UNKNOWN effect 加可信 provider receipt，当前历史快照的 effect 为零。不得为调用这些接口而造 observation/effect 或把未知费用记成零。

Root 的最小下一步资源是：一份只含白名单业务字段的原 store 当前只读快照，以及同 provider/account/route 在原 300 秒窗口内的完整请求与计费审计回执（覆盖迟到结算与分页，隐藏凭据）。本审查未开 DB、未发 API、未运行 CLI/model、未改原 trial/Main/Canon；具体 probe 白名单、原始引用与源码行号在 review.json。若外部覆盖不足，financial 保持 OPEN；若得到确定账务证据但仍无对应 effect/账务入口，则明确 financial closure contract gap，不能原地翻 tombstone。
