# 追加：R1 生效层级、修复边界与测试 census

本追加保留 `report.json/report.md/manifest.json` 原字节。结论仍为 **REQUEST_CHANGES**，R1 是 P2 的 IPC 只读分类与已登记范围符合性缺陷。两个反例已经执行；它们不证明当前 Core 会产生对应真实副作用。

**纠正原 report.md 中“生产中的 provider.probe 可以发出模型探测”的表述。** 这是规格定义的动作语义，尚不是当前 Core handler 的实现事实。当前 `internal/domain/client_protocol.go` 的 provider.probe/provider.models 进入 handleRead default，返回 NOT_IMPLEMENTED。当前 `client_protocol_first_use.go:15` 对 workspace.register 要求 project/session/revision/epoch 全 null，而本反例使用当前 Session envelope，真实 Core 会拒绝。因此本轮证明的是候选 IPC 将这些有副作用语义的方法排除在 activity fence 外，并接受公共合法响应；不是证明当前生产可以完成两种动作、绕过 Core 门槛或发出真实模型调用。R1 仍违反独审 scope 已明确的“只读分类必须显式限定”，修复应守住此契约，不能靠某个当前 handler 未实现来推导无副作用。

## exact3 V2 建议

在 IPC 层定义独立的 `isPresentationRead(method,payload)` 与 activity generation/活动集合。不要扩大 `v2.WRITE_METHODS`，不要把 provider.probe、workspace.register、session.create 强行视为需要当前 session writer/CAS 的写命令。原 WRITE_METHODS、host.configure、takeover attach 的 owner/CAS/原 envelope/replay/ACK/possiblySent 规则保持原语义。

明确的只读方法可以有展示票据豁免；任何不在明确集合中的方法均不能自动继承。session.attach 只有 `request_write_owner === false` 的变体属于只读。provider.probe、workspace.register、session.create、host.configure、bootstrap、goal/start、控制/导入/写入/权限决定属于有活动语义的类别，须让已有资格读取代次失效；其请求是否符合各自作用域仍由原逻辑与 schema/Core 决定。

provider.models 必须按 payload 分：v2.4 接口规格将 `refresh=true` 定义为最多一次目录网络请求，且必须 `allow_network=true`，此组合不得获得展示读豁免；`refresh=true/allow_network=false` 本身非法，仍应走既有拒绝。`refresh=false` 是缓存读取；`allow_network=true` 只是允许联网，不等于已经发起刷新。可以将明确 `refresh=false/allow_network=false` 列入最小缓存读取豁免，也可以在严格验证 boolean 及其余字段后接受 `refresh=false` 的两种许可值；如采用前者，应记录其保守拒绝语义，不能声称后者一定有网络副作用。当前 handler 缺失的事实不改变这项契约分类。

代次增加须在实际操作被保留/准备送入 transport 的时点，而非只在副作用响应结束后。资格读必须检查入口/结束的代次，并考虑尚未结束的非展示活动。activity generation 与原写命令 lifetime 分离；普通 poll 不递增 activity、不解除 pending、不吞掉原 ACK。非展示操作未结束/不确定时，不得靠较新的普通 GET 抹去其活动边界；当前作用域变化/ABA、原生身份、expiry、consumed、CANCEL 和原命令重放仍沿原规则。

20 个编号的已通过夹具不够证明 R1 分类完整。修正版额外需要按方法/变体覆盖缓存 models、明确 refresh/probe、register/create 的正确 scope 与不合法 scope；明确哪些只读可以不干扰资格，哪些 activity 会使资格失效。使用原 Main/Proxy、真实 bound validator、唯一生产 transport 的并发路径；双 transport 倒序仅作为额外鲁棒性测试。生产单一 transport 的已排队成功响应逆序不可达；本轮使用 credential await 阶段实现后起 display 先完成。R1 修复不会授权扩大测试到真实 Core/model/GUI/SQLite。

## 测试 census

| 实际集合 | 数量 | 本轮证据 |
|---|---:|---|
| 旧 CB 四文件集 | 219 | 保存了实际 argv：coding-authorization-boundary、desktop-management-boundary、http-wire-boundary、w13-react；180 HTTP + 2 Electron + 21 coding + 11 management + 5 route/SSE/first-use |
| 作者 cbe “full-bound-desktop-03” | 203 | 日志恰为 180 HTTP + 2 Electron + 21 qualification；不是旧四文件集合 |
| 作者/独审 targeted | 21 | 203 集合内的 qualification 子集，不能额外相加为 224 个不同用例 |
| 独审 management | 11 | 本轮另行通过，原始文件/命令/退出码已保留 |
| 独审补测 | 11 | 9 通过、2 个 R1 反例失败；与作者补测分别计数 |

旧新文件和注册测试名比较：coding-authorization 21、management 11、w13-react 5 的源码字节均未变；旧 HTTP 的 180 + 2 Electron 在新 HTTP 文件中保留，另新增 21 qualification，一个 model-config 测试改名且断言按新语义改变。故完整同入口候选集应按四文件实际注册数报告（目前推算 240，未执行不标 PASS）。203 已包含两个 Electron 流程，不是缺 renderer；缺的是另外 37 个四文件用例，其中 management 11 已被单独重跑，coding 21 与 w13-react 5 未出现在作者此次 203/独审定向执行中。

缺失 26 个的执行证据不自动等于新产品缺陷，也不能用旧 CB 通过升级为 cbe 当前通过。下次 R1 修复后应明确列出实际回归入口/argv；如果宣称旧四文件全套已回归，应实际执行全部四文件并保留各项退出状态。这里按 Root 要求仅核源码、注册名和日志，没有重复全量运行。

本追加仍无产品启动、真实 DB、模型、Source/Canon 或 D 盘写入。
