# Read lane V2 独立审查

结论：**CONDITIONAL_APPROVE_SOURCE_WIP**。原 R1（P2，IPC 只读分类边界）在本次冻结 WIP 中已修复；独立执行的 34 个 qualification 用例与 20 个补充用例全部通过。未发现本次 exact-three-file 范围内的新阻断缺陷。此结论仅允许 Root 继续受控集成，不是组合包、正常桌面 UI、真实模型、W05 或 Main24 正式验收。

源码为 `cbe5404367e2ea1f00e1ea4552d59d5d0d8eedf9` 基础上的冻结未提交 WIP，当前只修改 `apps/desktop/main/lib/ipc.js` 与 `tests/ui/desktop/http-wire-boundary.test.mjs`；`apps/desktop/main/main.js` 保持 cbe 原字节。三文件逐字节绑定作者 manifest、完整 compiler input 与构建产物；6444 输入重新哈希无漂移。新 validator 的 build metadata 如实记录 `vcs.revision=cbe54043…`、`vcs.modified=true` 与本次 input digest，不能称为新的已提交 Source。

| 核对项 | 结果与边界 |
| --- | --- |
| 显式展示读取 | 只有列举的方法及 `provider.models(refresh=false)` 获得展示读取豁免；`allow_network=true` 本身不构成刷新。`session.attach(false)` 保守纳入 activity。 |
| 非 CAS activity | probe、workspace register、session create、attach false、catalog refresh 均参与 generation 与 lifetime barrier；未扩大 `v2.WRITE_METHODS` 或既有 writer/CAS 适用范围。 |
| 进入时已有 activity | 独立用例让 activity 在 authority ensureCore 等待期间完成，entry barrier 仍拒绝该次 scope，未发出 authority HTTP。 |
| 两段 authority 等待 | activity 在 session.get 或 host.status 凭据等待中完成后，generation 仍使 scope 失效。普通展示读取先完成不会使独立 authority read 被抢占。 |
| ACK / 不确定响应 | ACK 和真实 malformed HTTP 后，GET/status/events、凭据丢失及后续 NOT_SENT 都不能清除原 lifetime；不同 payload 被挡住，原请求原 command ID 与原 bytes 重放后才释放。 |
| native origin | nonwrite activity 的原重放遇到不同 host/data root 被拒绝；回到原 host 后原 bytes 可完成。 |
| writer 与 Proxy | 非 CAS probe 不强加 writer；既有 session.send 仍要求有效 writer。真实 Main Proxy 对 project/writer ABA 的 generation 仍挡住 scope。 |
| 原有写入与取消 | send/CANCEL ACK、stale-CAS REJECTED、attach 原重放及 GET 不能收养 pending snapshot 的独立回归通过；作者原 writer、shutdown、TTL、consumed 用例日志通过。 |

独审实际执行 `author-targeted` 34/34 与 `supplemental` 20/20，两个 Node 进程 exit 0，无 skip/cancel。每个 fixture 使用一个实际 `createTransport` 和构建出的 validator；Main 函数及 Proxy 从当前源码直接提取并保存哈希。health/native identities 与 HTTP host 为公共 fixture，因此这些是 IPC/传输边界证据，不是生产 Core 外部效果。单个生产 transport 串行发送；所谓两个合法 HTTP 完成逆序不作为真实 Main 单 transport 的可达路径。本次用真实队列及 authority 凭据等待构造可达交错。

作者四入口最终日志已按哈希核对：HTTP180 + qualification34 + renderer2 = 216，另 coding21、management11、w13-react5，共253个用例；本轮34个重跑属于该253子集，20个独立用例单列，不将重复执行累加为新的正式用例。作者首次全量为215/216、exit1；后续 renderer 隔离2/2和完整216/216为独立后续观察，不覆盖首次失败。

首次 React renderer 日志确有 `Invoke in DisallowJavascriptExecutionScope` fatal、`DESKTOP_RENDERER_PASS react` 标记和 numeric exit `4294930435`，同时有 fixture 未注册 qualification/coding current handler 的日志。现有证据不能证明崩溃根因就是 teardown。`rendererProcess` 在两用例间共用 `electron.stdout/stderr/invocation.json`，最终这些文件均是 legacy；React 的独立 native invocation/raw 没有按用例保存。首次顶层失败 stdout 仍保留 fatal 堆栈与数值退出，不能声称历史失败的全部子进程原始文件齐全。此为既有 fixture 证据限制；正常 Root UI 必须另获独立原进程 handle、数值退出及逐子进程证据。

旧 R1 的更正继续有效：当前 Core provider.probe/provider.models 未实现 handler；workspace.register 对当前 Session envelope 会被 first-use all-null gate 拒绝。反例及补测证明 IPC/契约分类，未证明这些当前生产动作可以发出模型调用。原 V1 report、addendum 与失败断言均未改写。

Root 后续接受条件：冻结本次精确源码并按授权完成正式 commit/sourcebundle；在组合 Main tree 上 fresh build，逐项绑定 Core/UI/validator/descriptor/input/compiler/package，不手改旧 descriptor；正常桌面重试在另一个明确 scope 中进行。当前 Root Main/安装包未改，本审查未启动产品、读取真实 SQLite、调用外部网络/模型或改正式接受状态。

作者称清理旧目录被 automatic approval review 拒绝并保留目录；本轮未尝试该清理，也未绕过。独审自身 prepare 第一次误把 Node spec reporter 当 TAP，断言失败后用 prepare02 更正；第一次 `go version` 因 PATH 无 go 失败，再按 descriptor 中的原 Go tool 路径只读成功，均保留脚本与诊断。这些不记为产品缺陷。

证据入口：`report.json`、`binding-before.json`、`verification-final.json`、`author-raw-verification.json`、两个 `*.invocation.json` 与原始 stdout/stderr、`supplemental-cases.json`、各 UUID raw 目录；`manifest.json` 与 `seal.json` 封存本目录。所有新增证据在 C 盘，D 盘写入、源码修改、Canon 修改、模型调用与正式验收增量均为0。
