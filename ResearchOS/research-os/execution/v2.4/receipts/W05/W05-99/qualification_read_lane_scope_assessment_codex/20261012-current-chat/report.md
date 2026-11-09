# Qualification read-lane scope assessment

结论：建议登记 **exact 3 paths**。本轮只完成独立只读范围评估；未实现修复、未重试 Root 资格准备、未启动模型或 GUI。

1. `apps/desktop/main/lib/ipc.js`：分开只读展示顺序与 Main 资格读取的有效性；保留并补足真实上下文、写入代次和原命令生命周期检查。
2. `apps/desktop/main/main.js`：仅在 `prepareQualificationScope()` 的 `session.get` 与 `host.status` 两处调用传入仅 Main 可设置的资格读用途。保留现有上下文、宿主、writer 和模型匹配检查。
3. `tests/ui/desktop/http-wire-boundary.test.mjs`：确定性并发矩阵和既有 write/ACK/host-origin 回归。

当前基线为 `c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0`。这 3 路径与 Mu M0/V2 的 9 路径不重叠；仍只有 Root 负责登记、整合与后续构建。

## 为什么第 3 路径必要

`ipc.js:136–175` 对所有请求使用同一个 `WeakMap<sessionState,ticket>`；任何后发请求都让先前完成的请求返回 `STALE_RESPONSE`。`main.js:205,216` 的资格准备调用与 renderer 的普通 `session.get`/`host.status` 完全相同，没有调用用途标识。当前 `main.js:218–221` 因此把 poll 的票据变化解释为 `HOST_OR_CONTEXT_CHANGED`。

仅按 method 分票据的两文件方案能修复已复现的 events/status 交错，但普通 `host.status` 展示刷新仍能否决资格 `host.status`；普通 `session.get` 同理。让所有读都绕过顺序票据又会扩大现有展示更新语义。本建议保留展示读取的顺序约束，用 Main 本地参数标明资格读取，避免这两种缺口。标识不得来自 renderer payload，不新增 IPC channel、协议字段或 renderer 授权能力；`registerV2` 继续只传原有参数。

## 已复核证据

独立读取当前 Source 和诊断脚本、结果及两组原始 HTTP/validator observations。诊断 `interleaving-diagnostic-result-04.json` SHA-256 为 `d922833eebd173f1562ccd5cbf50fc911a55efa1d830c0c6bdfb2f744f589a53`，与当前 `main.js`、`ipc.js` 和绑定 C381 应用一致。

- 隔离资格 scope：2 个本地公共 fixture HTTP 请求、4 个实际 validator 子进程，成功取得 `fixture_config_1`。
- 后台 `session.events` 插入资格 `host.status`：ticket 2→3，原资格 scope 失败 `HOST_OR_CONTEXT_CHANGED`；所有 session/Host/writer/config 状态未改变，events 本身成功。3 个 HTTP 请求、6 个 validator 子进程。
- 原始 observations 中 10 个 validator 子进程均 exit 0、close/stdin/stdout/stderr 已结束；这属于既有诊断证据的独立复核，本评估未重新执行 fixture，也未把它记作真实资格成功。

## 必须保留的边界

资格读用途只能影响展示票据是否使结果失效，不能跳过 schema/validator、credential、native origin、write owner 或 CAS。`qualificationContext()` 已包含 project/session、revision、writer epoch/client/expiry、selectionGeneration、authorityGeneration；IPC 应绑定这些原始值及实际读写代次，不能只比较当前四元组，否则 A→B→A 会被放过。仅事件游标、相同值快照回填和另一个展示读开始，不应被当成真实上下文变化。

资格读不竞争同方法展示票据，但真实 context/authority 变化、另一真实写入的保留/发送、宿主替换仍使旧读失效。每个 snapshot 的 state adoption 必须单独受当前 context 与 pending/write lifetime 约束，不能因读返回 `COMPLETED` 就认领 writer 或终结旧命令。新的展示读不得释放或使原写命令失效；原写仍以自己的 command ID、原 envelope、原 host origin 和原上下文决定终局。

保留 `operations`/`pendingOperation`、`possiblySent`、`acknowledged`、`inFlight`、同 payload replay、credential refresh 后原命令重试、跨宿主拒绝及 `local_terminal_result` 的原宿主归属。`host.configure` 在别的宿主状态返回后即使终局到达，也不能被套到新宿主。保留 Main `currentHost()` 对真实 control/parent 进程的检查；IPC 允许同逻辑宿主换端口，不代表 Main 可接受 control 进程替换。

不关闭或暂停 polling；不增加 sleep/debounce 碰运气；不删除全部 ticket；不更改私有管理 prepare/confirm/status、expiry、consumed、pending 或 consent 屏障。不改 renderer、preload、Go、协议 schema、contracts、canonical pin、生产数据或模型配置。只读分类必须显式限定；不能把 `!WRITE_METHODS.includes(method)` 当作所有方法都无副作用的证明。

## 确定性验收矩阵

每个并发用例使用 deferred arrival/release gate，断言实际顺序与 HTTP 数，不能用固定 sleep 模拟竞争。公共 HTTP 用绑定候选应用的真实 validator；任何资源摘要变化须通过既有构建流程产生新包，不能手改 descriptor 或回避校验。

| ID | 交错/变化 | 必须结果 |
|---|---|---|
| R01 | 无并发，资格 get→status | 成功；同原 scope，无私有 prepare/model 调用 |
| R02 | 资格 status 等待时 events 开始 | 两读成功，原资格 scope 不失效；状态不变 |
| R03 | 资格 get 等待时 events 开始 | 原 get 可完成、合法 adoption，资格后续 status 成功 |
| R04 | 普通 host.status 在资格 host.status 后开始，双完成顺序互换 | 资格读不因展示票据失效；本地宿主绑定正确 |
| R05 | 普通 session.get 在资格 session.get 后开始，返回完全相同快照 | 资格不被抢票；不误增 authorityGeneration |
| R06 | 不同展示用途读交错；同展示用途两读倒序完成 | 不同用途互不抢票；同用途仍有顺序保护，旧值不覆盖新值 |
| R07 | 资格读期间 project/session A→B；以及 A→B→A | 均失败，generation 抓住 ABA，不采纳旧 snapshot |
| R08 | revision/epoch/client/expiry 任一真实变化及变回 | 均失败；保持当前 writer/CAS，无旧权限回填 |
| R09 | 资格读期间真实写保留/发送/ACK，之后读完成 | 原读不能证明资格；写 lifetime 保持；不得发送第二个不同写 |
| R10 | 原写 in-flight 时普通 events/status/get 并发 | 展示读不抢走原写终局；ACK 仍 ACK，终局按原 command/envelope 收敛 |
| R11 | ACK attach→较新 GET→不同 send→原 attach replay | GET 不认领 writer、不解除 barrier；send 阻塞；原 replay 终局才采纳 |
| R12 | 不确定发送→本地 NOT_SENT/credential 失败→不同写 | 原 possiblySent/ACK 屏障不丢，不能换新 command 重试 |
| R13 | credential await 前后 host/data root 变化；response 等待期间变化 | 零发送或返回拒绝；local_host_origin 不跟随远端字段 |
| R14 | 同逻辑 host 仅 URL/PID 变化（IPC fixture） | 原同宿主兼容测试保留；另行保留 Main 实际进程身份失败检查 |
| R15 | host.configure 终局与异宿主 host.status 交错 | 原 terminal result/origin 可用于原命令对账，但不得赋予新宿主成功 |
| R16 | 资格 get 后 snapshot/model/writer 不匹配；status malformed/REJECTED | 原 WRITE_OWNER_REQUIRED/SESSION_MODEL_UNAVAILABLE/验证拒绝仍有效 |
| R17 | renderer payload 伪造 lane/options/context | closed payload 拒绝，不能进入 Main 资格读用途，无新 channel |
| R18 | 重复 prepare/已 consumed/pending/过期 intent；CANCEL/STATUS | 私有管理既有屏障原样有效；本修改不解锁第二次确认 |
| R19 | 资格 get/status 等待时 dispatch session.control CANCEL，或原 CANCEL 收 ACK | 资格旧读不再可用；CANCEL 不被读抢票、重复发送或误认完成；CAS 陈旧时仍拒绝 |
| R20 | Main shutdown/quiesce 开始或实际 control 进程更换，资格 HTTP 之后完成 | Main currentHost/READY 检查阻断资格继续；不得进入 private prepare/confirm；本轮不实际关闭或启动 Root |

R01–R05、R07–R09、R16 应调用从候选 `main.js` 提取并 hash 绑定的实际 `prepareQualificationScope()`，不要在测试中重写一个等价函数。Main 上下文使用真实 Proxy/generation 逻辑绑定，ABA 用例不能只替换为普通对象。R18 可继续使用既有私有管理回归，并明确区分源代码不变验证与新增执行结果；本范围评估不声称它已重新通过。

## 交付边界

建议 `SCOPE_READY_EXACT3_PENDING_ROOT_REGISTRATION`。尚未修复或验收。正式增量 0/42，parent acceptance false。后续须先完成候选修复、确定性测试、独立审查及绑定候选包；真实 Root 资格执行与模型调用仍由 Root 在其原授权流程下单独处理。

Root 已确认本评估采用 exact3 方向，登记权仍由 Root 持有。Root 通知原应用已普通 WM_CLOSE、相关 PID 已不在，因未持有退出句柄，真实 exitCode 为 NOT_OBSERVED；该消息不在本评估中提升为独立进程验证。原数据保留，未访问关闭的 CDP，也未重做生产资格或模型请求。
