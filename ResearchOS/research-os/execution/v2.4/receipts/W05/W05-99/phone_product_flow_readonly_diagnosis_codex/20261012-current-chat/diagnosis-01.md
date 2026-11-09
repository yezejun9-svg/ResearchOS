# 手机配对与监督：只读产品路径诊断

状态：READ_ONLY_DIAGNOSIS_COMPLETE / PRODUCT_NOT_READY。输入 Main `b806a06fb62576c18dfd1e7174c1dfd929677506`。这是 Root 的 Source 范围决策材料，不是施工接受或真实手机验收。用户偏好已经是 `USE_REAL_PHONE_AFTER_READY`，不再次询问。此轮没有启动手机、隧道、GUI、API、模型或产品进程，没有读取凭据或产品数据库，没有修改 Source/Canon。

## 结论与合同边界

当前产品已有可用的 V1 设备配对、短会话轮换和指定项目授权机制；缺的是经过当前构建验证、可直接给用户操作的手机入口和监督界面。不能把网关开放 `/v2/command` 当作全部修复。当前 V2 至少还缺远程边界、会话读取的委托鉴权和手机独立客户端身份。

最关键的冻结限制：`22_CLIENT_INTERFACE_DETAILS.md:132` 明文禁止把本机 `session.attach(true)` 接管能力授予远程 READER/手机；`:147` 的 `session.handoff` 目标也必须属于同一本机主体。手机即使被授予指定项目 OWNER，也不是本机 OS 主体。不得把 device principal 替换成 issuing owner、沿用 `desktop-renderer` client_id，或把本机 writer_epoch 复制给手机。冻结 V2/Native3/schema 均保持不变。

因此最小可推进范围是：电脑生成单次配对入口 → 手机默认只读 → 读取已授权项目与既有会话的监督投影 → 电脑显式给予指定项目控制权限 → 使用已有 V1 任务/Run/资源监督动作及其真实服务端回执。V1 监督动作是否已正确接入当前 Mu 会话的暂停、原动作资源许可和恢复，必须用当前真实任务链补证；下文列出尚未闭合点。不能把 V1 研究周期暂停冒充 V2 Mu 会话暂停。

## 当前调用链与明确阻塞

1. `apps/web/src/Pairing.jsx:55 DevicePanel` 调用 `createDevicePairing`，仅当前 project，300 秒；显示复制链接按钮，尚无 QR。链接为 HTTPS origin 的 `/pair#challenge_id.pairing_token`。`takeChallenge` 在兑换前清除 fragment，`PairingGate` 用稳定 idempotency key 兑换，`useDeviceSession` 仅内存保存 access/refresh，并用原 key 重试未定的刷新。电脑可以 `updateDeviceGrants` 切换 READER/OWNER 或 `revokeDevice`。这些能力应复用，不需要手工 Owner token。
2. `internal/domain/remote_http.go` 管理短时单次挑战、设备、兑换与轮换；`remote_auth.go:21 constrainRemotePrincipal` 每次从设备和 issuing local owner 当前状态计算项目授权交集，撤销/Owner 失效即时拒绝，禁 project creation、restricted grants。V1 的 `remoteOperationBoundary` 还要求网关请求只能使用 device credential。不要删除这些门。
3. `ops/remote_access/gateway/main.go:38 gateway` 限定精确 HTTPS origin、loopback 转发者、单值敏感头、同源 JSON，清除 Cookie/Forwarded/CF/x-forwarded 并注入 remote device marker。`:106` 仅代理 V1 的 project 路由及 redeem/refresh；`:121` 静态白名单只有 GET/HEAD。因此满足前置安全条件的 `POST /v2/command` 到静态分支后为 404。设备管理、health/admin、SSE 仍应不公开；当前 `/remote-info` 明示 poll。
4. `internal/api/v2.go:154` 认证 token，`:185` 做项目 grant 后直接 `ClientService.Execute`；没有 V1 等价的 remote-marker/device-only 检查。仅在网关放行 V2 会允许错误的本机 token 类型进入远程 V2。新增保护应同时约束 DeviceID，而不只信任 header，以覆盖直接 loopback HTTP 的 device 凭据。
5. `client_protocol_sessions.go:103 clientSessionOwner` 要求 session creation receipt principal 等于调用者；`:251` list SQL 也排除其他 principal 创建的会话。paired device 的 ID 与桌面创建会话的 Owner ID 不同，所以会话列表隐藏、直接打开拒绝。最小只读委托 resolver 必须分别保留 actor=device 与 resource owner=issuing owner，核对两者当前授权、项目和唯一 creation receipt；普通非 device 所有权保持原状。对缺少创建归属证据的旧 administratively mapped session，应明确保留本机兼容逻辑但对远程默认拒绝，不能借该兼容分支读全项目。cursor 仍绑定实际 device/project，不能跨设备复用。
6. `apps/web/src/main.jsx` 当前对所有非 native 页面展示“对话接续”；`screens.jsx:216` 路由到 `Continuity`；后者 `:60` 硬编码 `desktop-renderer`，`:75` 每次 token 刷新重建 client。不能直接把这个 23-producer 开发界面当手机产品。应传递 `device.id/role/project_ids/renewalPending`，采用服务端绑定的每设备稳定 client_id，续 token 不改变身份和未决操作。host.configure、workspace/register/read/write/import、provider probe、session.create/send/attach(true)/handoff 不进入手机首批表面。
7. `client_protocol.go:710 Execute` 在 dispatch 前就可重放幂等回执。新增 device 当前 role/project/method/identity 授权必须放在 replay 前，并在实际动作事务使用当前状态，不能只在 handler 写一次检查。设备降权/撤销/issuing owner 撤权后不得用历史 command_id 回放敏感结果。
8. `client_protocol.go:1139` 目前 writer takeover 在 live run 未 settled 时拒绝；`:1226` PAUSE 为 NOT_IMPLEMENTED，仅 CANCEL 和已完全 settled 的 session RESUME 有实现。实现本机暂停交接属于另外的本机合同增量，不能顺便让手机取得 writer。
9. 已有 V1 `actOnTask(PAUSE)` → `operations.go:256` → `orchestration_controls.go:5 controlTask` 记录 control，阻塞 task 并请求 active run cancellation；`orchestration_recovery.go:133` 在停止后保留 BLOCKED。RESUME → `orchestration.go:305 orchestrateTask` 要求无未决 Run、原 Goal ACTIVE、上下文/依赖/预算当前有效，且队列 redispatch 在 claim 阶段另有 fencing。此链是任务监督而非 V2 writer 接管。当前真实 Mu turn 的 pause/settle/resume 是否能够恢复用户预期工作，尚无本轮 live/fixture 证据，不能宣称可用。
10. V1 `resolveResourceRequest` 需要有效 evidence refs 并应用既有 recovery；`resources_recovery.go:9` 明文不授予 runtime permission。V2 `permission.respond` 保留 action digest/request revision/USER_DECIDABLE/expiry/原 task/run/input 检查，但 `client_permission.go:217` 调 `clientWorkspaceBinding`，后者 `client_workspace.go:58` 拒绝 DeviceID；随后还要求 original action principal 与调用者相同。故“手机响应一般资源请求”和“手机批准原 Mu 工具权限动作”不是同一已完成能力。后者若为本轮目标，要由所属卡单独给出不借用本机 writer/OS 权限的授权契约；不得直接把通用 resource resolved 状态当 permission allow。

## 建议 Root 冻结的最小 Source 范围

先建立一个可以独立复核的配对及只读监督增量；控制功能以现有 V1 契约为边界，真实 Mu 控制缺口单列，不能在增量中静默扩大权力。

| 文件/候选文件 | 必要变化 | 约束 |
|---|---|---|
| `ops/remote_access/gateway/main.go` | 仅新增精确 POST `/v2/command` 的受认证通道，用于选定只读方法 | 保留所有 origin/TLS/header/path/admin/SSE 限制；不开放 `/v2/*` |
| `internal/api/v2.go` | remote marker 必须 DeviceID；绑定 canonical device client_id；在进入 execute 前拒绝不允许的 remote method | 不由 request 自报角色；拒绝 null-project/admin/native 操作 |
| 新 `internal/domain/client_remote.go` | 当前 device/issuing owner/project 交集、会话 owner 读取委托和只读方法表 | actor 保持 device；只允许 session.list/get/events/attach(false)；不扩大 writer/OS 身份 |
| `internal/domain/client_protocol.go` | 在 idempotency replay 前调用 device policy，dispatch 只读会话 owner 检查使用 resolver | attach(true)、handoff 和其他写方法继续禁止远程；不改 frozen response shape |
| `internal/domain/client_protocol_sessions.go` | list/get 的创建归属、分页 cursor 与只读委托一致 | 不能接受任意同项目会话或含糊创建证据 |
| `apps/web/src/Pairing.jsx` | 生成可本地渲染的 QR，标明项目、只读、到期时间、撤销；保持复制链接 fallback | QR/link 只含单次 capability；不发送给外部 QR 服务、不写日志/持久存储；旧 challenge 到期清理 |
| `apps/web/src/main.jsx`, `apps/web/src/screens.jsx` | 传 device context；paired device 进入监督界面，隐藏本机配置/开发生产者 | UI 禁用只是提示，授权仍由服务端执行；默认只读 |
| 新 `apps/web/src/RemoteSupervision.jsx` 与新 `apps/web/src/remote-session-client.js` | session 列表/选择、运行/阻塞/费用/通知、只读/陈旧/断网/撤销状态、分页 poll；稳定 device client_id 与 reply method/command/session 校验 | 凭据从 getter 更新，刷新 token 不重建身份；绝不复用 desktop-renderer；无自动写重发 |

若用已有本地 QR 库需要依赖变更，Root 再把 `apps/web/package.json`、lock 和具体 encoder 纳入串行精确范围；本轮未安装依赖，未指定未经检查的库。最小可先用已实现的复制链接完成配对；QR 是让用户更容易打开的准备项，不能依赖外部服务搬运 capability。

以上是文件提案，不是写授权。V1 既有 task/run/resource 控制首轮先复用其 handler 和 ETag/idempotency；`screens.jsx` 仅把明确受支持动作连接到所选会话投影的真实 task/run/resource IDs，显示当前 role 与 pending/settled 回执。若测试证实 Mu pause/resume或原许可缺口，Root 为 `orchestration_controls.go`、`orchestration_recovery.go`、`client_protocol_queue_control.go`、`runtime_permission_windows.go` 等真实拥有者另建具体问题范围；本诊断不提前允许改这些文件。

## 测试候选与接受边界

- 网关 `ops/remote_access/gateway/main_test.go`：精确 V2 POST 可达；错误 method/path/origin/TLS、双 Authorization/Origin/Content-Type、admin/SSE、Cookie/Forwarded 伪造均维持拒绝；合法 V1 pairing 未回归。
- 新 `internal/api/v2_remote_test.go`、`internal/domain/client_remote_test.go`：真 device token 可读 issuing owner 唯一归属会话；其他设备/其他 Owner/跨项目/cursor 注入拒绝；本机 token 经网关拒绝；device client_id 冒用 desktop/另一设备拒绝；无归属或冲突归属拒绝；撤销、降权、Owner grant 移除在旧 token及幂等 replay前生效；所有写/Native/host config/文件权限禁用；普通本机行为未改变。
- 复用 `remote_test.go`、`remote_isolation_test.go`：单次配对、到期、重放、刷新同 key 恢复与不同 key family revoke、默认 READER、项目 OWNER 授权、撤销当前状态。新增授权策略需复验这些相关分支，不能继承旧 PASS。
- 新 `tests/ui/mobile/remote-session-client.test.mjs` 与实际手机监督脚本：wrong method/command/session/nullability 回复不改状态；poll watermark单调、不续 writer；token 轮换身份不变；断网期间只读陈旧态；原未知写请求不换 key 重发；按钮 role gating、手机布局、清晰回执。使用当前构建，不只 snapshot/静态 fixture。
- 当前真实 Mu 任务的 V1监督专项：所选 session→project/task/run 映射唯一；pause 请求不会显示已停止直到 Run 真停止；旧 revision、重复 command、网络丢包、并发桌面操作、权限撤销时无重复执行或双 writer；resume 不重复 dispatch 原队列、不静默新模型；通用 resource resolve 不能批准原工具 permission。该组未通过不能宣称“手机监督控制准备好”。
- 手机 A10/A11 live 与模型调用由 Root 后续执行；本轮所有测试均为候选，执行数为 0。cloudflared 只运行 `--version`：本机 `C:/Program Files (x86)/cloudflared/cloudflared.exe`，输出 `2026.8.3 (built 2026-08-31T02:48 UTC)`；未启动 tunnel。

## 正式所有权和旧切片的影响

`execution/v2.4/formal_case_requirements.json` 当前映射：A02→W06/core.qualify（4 条），C10→W16/test.orchestration（3 条）；它们不是手机正式终验。手机关键是 A10→W17/test.ui（A10-01..05）、A11→W17/test.security（A11-01..05）。W17 父任务另有 C02（2 条）和 C22（4 条）；W17-03 卡注明 A10/A11/C17，C17 最终 Owner 是 W13（3 条），不能挪到 W17 擅自签收。

A10/A11 为 LIVE_WINDOWS：真实 Windows Desktop 发行候选加真实手机浏览器；须保存设备/浏览器版本、当前 build/input/hash、实际操作及独立复核。A10覆盖布局/内容/状态/独立 accessibility 及 clean Windows首次使用；本机首次使用完成也不等于手机 A10 完成。A11涵盖过期/重放/无认证/跨项目/撤销、secret隔离、TLS默认关闭和 Desktop IPC。现有 formal requirement快照里 A10/A11/C22 无 registered selector，实际执行前由注册 Owner 核对/登记，不能 aggregate PASS/零断言替代。

当前 `step_state.json`：W17-01、W17-02、W12-02 ACCEPTED；W13-03 BLOCKED；无 W17-03 已启动记录。W17-03 依赖 W17-02、W13-03、W12-02，因此本诊断和前置 Source 提案不等于卡 READY/接受。此前 W13-03 的真实 NVDA/前台及独立 workspace audit阻塞不能借本轮绕过。

变动后需当前证据重新覆盖 W17-02 的远程/egress边界、W17-01 的相关鉴权/非device隔离和 Native3不变、W13相关 UI/transport/pairing/token生命周期；W12-02 仅在改动真实Runtime暂停/队列恢复/许可路径时补受影响合同。保留旧接受和历史失败，不改旧 receipts，也不以旧 148/632 等累计断言替代新 Source 下的证明。

## 用户手机操作前的准备与后续真实步骤

准备完成的判据：Root 当前桌面安装/启动和指定项目真实会话可用；隔离候选上述小范围通过独立审查；精确 HTTPS origin 的授权通道准备好；电脑设置页能显示限定项目与权限、生成到期单次 QR/link、列出设备和撤销；手机页能通过配对进入真实项目与会话，而无需粘贴内部 token/session ID；只读/可控制/过期/断网和真实服务端回执清楚。存在Mu控制缺口时明确标记，不能提前交用户测试一套虚假按钮。

之后由 Root 按已有“准备好后用我的手机”授权操作，不重新询问是否使用手机：启动已审核 exact-origin 通道；电脑正常 UI 生成一次性 capability；用户用真实手机打开 QR/link、命名并配对；确认默认只读且仅指定项目；电脑显式授予该项目控制后做已通过预验的真实 pause/resource/resume/cancel；对照电脑同任务/费用/通知；断网重连后仅对账、不重发控制；电脑撤销后手机下一请求拒绝且不能重连/回放。配对 QR/URL 本身是单次秘密，证据只记录挑战公开 ID/到期/结果，不捕获 capability原值；浏览器只内存持有短期会话。当前手机页面刷新会丢内存会话、需要重新配对，应在用户操作提示中如实说明。

## 回执限制

先前 checkpoint `work_in_progress.phone_pairing_readonly_preflight` 只有 owner/status/preference/未启动标志，没有 receipt 路径；对 receipts 文件名检索未找到独立 phone preflight，已询问原 owner。本报告重新核对当前公开 Source/合同，未据不存在的旧回执声称已验收。探索时若干不存在路径/glob 查询与一次过宽 checkpoint搜索有非零/截断输出，均属只读定位，不是产品测试；没有据此重置测试失败。只有本目录新诊断/manifest产物被写入。
