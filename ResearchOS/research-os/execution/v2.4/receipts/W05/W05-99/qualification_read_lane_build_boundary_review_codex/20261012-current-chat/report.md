# read-lane 新 UI 与已审 Core 组合边界

结论：`CORE_REUSE_CONDITIONAL_PENDING_UI_FREEZE_REVIEW_BUILD`。允许按下列条件复用已审 Core；本回执不接受尚未冻结的新 UI、组合包或真实资格运行。

当前 Main 是 `c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0`，实际树为 `2936ca3097bc2c2d6cd6fd2e9af40756d25d32f8`。使用原 manifest `bddb0955…`、correction `12ebc13e…`、supplement `f6720ce4…` 的追加更正链；原摘要中的 `…e8` 不能成为构建依据。task_packet 本轮读取已验证状态，选中 W05-99；产品接受未作断言。

| 检查点 | 新包交付与独审要求 |
|---|---|
| Source freeze | CP440 scope `f83c964c…` 的 exact3 仅限 ipc.js、main.js、http-wire-boundary.test.mjs；冻结候选 commit/tree、文件 SHA、完整 diff 与输入前后哈希。Main 中 authority lane 只用于 prepareQualificationScope 的两个读调用。 |
| Core reuse | 实际复核旧包 control SHA `326f70d5…` 与 verifier SHA `28ea9cc1…`，来源均为 Source `cb3646d…`。复制后重新核对字节；不能将其来源改写成新 UI commit。 |
| Validator rebuild | builder 将 main/preload、React 源码及桌面测试纳入完整输入 digest，并用 `-X main.buildInputDigest` 编入 validator。exact3 改动需要重新运行现有 builder；旧 validator `12b3ba8b…` 与旧 descriptor 不适用于新 digest。 |
| Descriptor / source snapshot | 使用候选 worktree 的 builder，保留工具/依赖、compile invocation、inputs.before/after、compiler archives 及新 descriptor。核对实际 main/preload 清单、React 产物和公开 schemas；全部声明按真实字节。旧 6444 输入和 219 测试只属于旧构建。 |
| Components | fresh composition/components/source_snapshot 明确记录 `Core=cb3646d… / UI=<frozen candidate> / Mu=8dfebe3…`；绑定 Root 整合 commit/tree、各组件来源与 package 全文件哈希。新旧树不能混作单一来源。MuM0V2 的候选与失败审查不自动进入此包。 |
| Native install | 新目录产生新的绝对 executable 路径，安装清单需保留同一 Core SHA/source_commit、固定 service/protocol 与 arguments=[]；重新核对 owner SID、protected DACL、唯一 owner FullControl Allow 且非继承。旧包 ACL 本轮复核符合要求，不能替代新路径的实测。 |
| IPC review | 使用实际候选 Main prepare/Proxy/context 与真实 bound validator，执行原 scope 的 20 类确定性门控。后台和同方法展示刷新不取消 authority 读；展示 latest-wins 不退化；选择/authority ABA、host/PID、真实写入、ACK/replay、possiblySent、CANCEL CAS、shutdown 均继续阻断失效操作。 |
| Root activation | 只有 Root 整合并完成新包校验后，正常 UI 重用原数据与 Session。启动前记录新包、安装清单、Core/SDK/模型与原生进程身份；确认旧实例实际退出，不以 PID 消失补记未知退出码。 |
| PREPARE / CONFIRM | UI PREPARE 绑定原 Session/Writer/Host/model/config/budget；取得原 request id/hash、issued/expires 后在 60 秒内由正常 UI 确认一次。最多 MODEL=1、TOOL=0、UNKNOWN money=null；600 秒是后续 purpose 生命周期，不是确认期限。CONFIRM 发出后错误或缺回复仅查原请求，禁止重新确认/重建请求掩盖不确定结果。 |
| Actual evidence | 新 UI 的 Source/fixture 通过不等于实际资格成功。实际成功仍需原消费记录、单一 MODEL effect 与原 SSE/SDK 相符、worker native cleanup/drain/协议完结、安装 verifier 身份/服务器 acceptance、当前原 STATUS 的有效 purpose。历史 UNKNOWN 和失败记录保留；正式用例增量仍为 0，父任务仍未接受。 |

证据缺口继续标注 missing：私有 management stdout 正文、verifier Result 原始帧、verifier 独立数值 Wait 结果并非现有持久化产物；verifier stderr 在源码中为 io.Discard。最终 administration artifact 可以支持“实现接受了 QUALIFIED 且 Wait 成功”的推断，不能称为独立捕获的原始帧或退出码。含 token 的 verifier Job 不应导出。worker 退出、verifier 退出与整个 Desktop/Core normalExit 分别取证。

本轮没有启动产品、调用模型、访问真实 SQLite 或改动 Source/Canon。首次 Python 子进程通过 Windows PowerShell 读取 ACL 时模块加载失败，原始 stderr 和 false 观察保留；随后在当前 PowerShell 7.6.5 原生读取成功，以 installer-acl-02.json 为该项有效证据。它不表示产品 ACL 曾经失败。

附加静态审查 Root observer：`observe.py` 的 mode=ro/query_only/BEGIN/ROLLBACK、原项目/Session 范围、Run 移除 lease_token_hash、固定请求字段集，以及 `launch_and_wait.py` 保留原 Popen handle 取得 Electron 数值退出码，符合本次边界。未运行这些脚本；本回执未重新读取 readiness 数据或真实库。它们没有读取凭据表或 idempotency headers；效果体会保留原模型 payload/SSE，因此不可泛化成任意配置的全字段隐私审查。

正式取证仍须串联 request → consume_rows.body.run_ref → 实际 Run → Task/Goal → 有效 budget 祖先。当前 --run-id 可独立指定同项目 Run，脚本尚未断言该 Run 属于原消费；budget 三种 scope_type 同时存在也不证明它们就是该任务的实际祖先。原 request 的哈希比较目前是输出布尔值，正式判定必须要求 true。这些是 readiness 的使用边界，不能由“观察器返回了 JSON”代替验证。启动器也只检查 main.js 存在和 Electron hash，新组合包 digest/安装清单仍由 Root 启动前独立绑定。
