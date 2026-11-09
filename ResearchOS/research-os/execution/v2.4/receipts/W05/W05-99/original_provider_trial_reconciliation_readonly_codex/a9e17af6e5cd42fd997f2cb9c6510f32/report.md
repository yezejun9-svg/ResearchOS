# Original paid trial READONLY_RECONCILIATION

结论：本地执行关闭事实已确认；Original 账户、外部请求、服务端终止及费用仍为 UNKNOWN。外部审计来源在本次已登记公开关联范围内 UNAVAILABLE。仅阻塞 Original 模型/费用审计支路，不阻塞其他已具备资源的实现支路。authority=NONE；没有 formal acceptance。

读取范围以 CP370 已登记 public refs 为入口，跟随精确公开 HDF/MF 与 Original lifecycle/独立 review；未打开凭据、DPAPI、private lease、原 DataRoot 或其他项目。本次 account/model/paid 请求均 0，未修改账户或任何旧证据。

## 已确认的事实

| 项目 | 事实和边界 | 实际出处 |
| --- | --- | --- |
| 当前输入检查点 | CP370 SHA a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994 /4489310；本报告是该固定观察时点 | discovery.json/checkpoint_ref；discovery-source-guard.closed.json |
| 公开资源包 | HDF 33f94193879f7e3d2712467474c6719d6caa0d7b7d15b7a206cf05fa0c6efdf8 /2981；MF 6cfb4d0f7779c027cd051a9d247242258359b267104d51f278305156d80ad1b0 /14988，实际 members 为 50 项 list | CP /work_in_progress/mu_sdk_r366/public_provider_audit/handoff_ref → opa-01a11f3f/HDF.json → MF.json |
| 模型配置资源 | 实际 sealed profile 指向 deepseek-v4.1-flash、opencode-go、openai-completions、https://opencode.ai/zen/go/v1/chat/completions；两个 credential_revision 匹配允许的 opaque ref | trial-output/runtime-profile.actual-sealed.json SHA 5ae9c99d096b7b01291cc48536143b004768aa624a3fd2747936fbdf5822ce3f /2135，/credential_revision、/effect_routes/0/credential_revision、/model_config |
| 账户绑定 | sealed profile 只证明本地配置与 opaque ref 的绑定，不能证明 Original 用户、workspace、API key 归属、有效订阅或 Use balance 状态 | 同上；没有账户登录或查询调用 |
| 本地执行 | lifecycle=FAILED_EXECUTION_CLOSED；go_sent=true；provider_requests=null；automatic_retry=false | root-coordinator.lifecycle.json SHA 74cb17a2a4e4c2a09495291aaebd15fb6400dd90aaf069511a4cab85b8e6fb5c /39414 |
| 失败首因 | 独立 review 确认 FILETIME 134359521876434319 被 canonical JSON 变为 134359521876434320，Host GO 验证在 ExecuteClaimedAt/RunAdmitted 前拒绝 | model_trial_failure745_component_review_codex/18f25bd65ef34e189490677e760b9864/review.json SHA 36441f85495593ecf8533a35a746f78eb80246845fcec1211d1019ce550930b4 /4664；关联 execute.go:206,217,234,451 / contracts.go:35–52 定位见原 review |
| OwnedJob 关闭 | host-admit-only PID57664/creation 134359521871765470 actual exit0；host-execute-admitted PID23436/creation 134359521876434319 actual exit1；均 PID+creation matched、primary exit confirmed、active0、Job/primary/duplicate handles closed | lifecycle /jobs/0、/jobs/1；整数以十进制字符串记录 |
| 300s 边界 | 300s 是授权/Job 上限；此次 native_timeout=false、watchdog termination_requested=false、termination_succeeded=null。不能写成已实际等待 300s 的 provider timeout | lifecycle /jobs/*/cleanup/watchdog；原独立 review |
| 本地阶段请求 | READY_ADMISSION_PENDING 与 ADMITTED_NOT_DISPATCHED 各自 provider_requests=0，只覆盖对应阶段 | host.ready.json be48917c479876f5a39a213f5bb5cf73b0b6a1fa6b40f30ecd198bb58ced3403 /1128；host.admitted.json 0289979eb9ec1216ffc22f1031570f35678801a1578ea4d8f0c72e46fa108f4d /838 |
| 原 Run/台账 | Run 7d5bc49c4951a20d0f5b3c9c344b8b45 QUEUED、未开始/完成；dispatch PREPARED；effects、observations、uploads、该 project BudgetLedger entries、Acceptance 均 0；全试验 provider/model count 仍 null | business-state.observed.json SHA 3228f071fc6028ca4eeb313a348f39687274bc72edab9e49786515046f249250 /2606 |
| 请求上限 | qualification 1 + ordinary 2 = max3，只是声明上限。MODEL upper_bound/max_cost=null；TOOL amount0 不能当作模型费用 | host-go.authority.json /maximum_provider_requests 等；sealed profile /effect_routes、/model_config |
| 实际公开 host capture | 原 trial namespace 精确枚举包含 admit/execute 各 stdout.raw、stderr.raw、invocation.json 与 lifecycle；没有完整 provider request/response/billing audit 文件登记。它们是本机进程流，不能替代服务端审计 | original-tool-io.json 内 trialrec_original_actual_enum；coordinator Source:307,319,550,552；final-public-links.json |
| runner 计数证据 | v9 Source 中 MAX_PROVIDER_REQUESTS=3 是上限；成功路径写 provider_requests=3，不能用未执行的 Source 输出当实际计数 | mu_sdk_trial.v9.proposed.py SHA cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f /90096，:30,:1487；capture-contract.json |

## 可以使用的只读查询入口及缺口

公开包固定 commit 388406238bd5ca15564a762840a2362c3a45bd9c 的实现，仅证明该版本公开代码，不证明 Original 服务部署/账户迁移状态。完整 Source refs 见原公开包 primary-sources.json 和本包 source-pins.json，不能从某分支字段直接推断当前服务器全部能力。

| 可读入口 | 现有能力 | 不能证明/所缺具体来源 |
| --- | --- | --- |
| GET /zen/go/v1/usage | legacy Bearer key 关联 workspace/user，返回 rolling/weekly/monthly 比例和 resetsAt | 无 per-request list、终止/撤销状态或具体计费流水；新 key/迁移用户转 inference，Original 是否迁移未知 |
| 登录 console 的 usage.list / Billing.usages | 已记录 UsageTable 行，page/limit50、时间倒序 | 需 Original workspace 的已认证只读来源/导出；完整翻页、窗口覆盖、迟到记录与 finalization 未提供。缺行不能当作没有请求 |
| console billing.get、payment.list | 当前余额、monthlyUsage、订阅 useBalance；payments 最多100项 | 当前余额或充值/订阅支付不能计算该 trial 的逐请求净费用 |
| UsageTable/handler | 公共旧 Source 有 token/model/provider/cost/keyID/sessionID；handler 在收到 usage 后记账 | 缺上游 requestID/status/cancel/error/finalization/charge transaction 关联；仍需服务端原始请求审计与可对账费用来源 |

当前官方 Go 文档确认可用模型、endpoint 与 console 用量查看入口；本次读取没有找到足以恢复 Original 历史请求终止及逐请求费用的公开查询契约。见 [OpenCode Go 文档](https://opencode.ai/docs/go/)。这不是声称所有服务器不存在其他私有审计能力。

## 恢复条件（都是 Original 只读来源，不需再造一次 paid request）

1. 账户来源：同 opaque credential ref 所属 Original account/workspace/keyID 的可读归属记录，及试验时订阅/useBalance/账户迁移状态。只导出非密钥标识，不提取 key。
2. 请求来源：覆盖 root_started_utc=2026-10-08T16:56:27.158744Z 至 Job deadline=2026-10-08T17:01:27.158744Z 的 Original provider request/status/response-or-timeout/terminal 记录，以及 keyID/sessionID、上游 requestID 可关联信息；覆盖允许时钟偏差及迟到 finalization。
3. 终止来源：同 requestID 的服务端 terminal/cancel acknowledgment 或服务端确定未接收/未执行的审计证明。本机 active0/exit/handlesclosed 不能替代。
4. 费用来源：完整分页的该窗口 usage/charges/credits/refunds 与余额前后/计费事务关联、待结算终态说明。未知费用必须保持 null；本地 BudgetLedger0 不得填为外部费用0。
5. 若 Original 无现成已认证只读入口，只阻该外部审计支路，并在资源台账记录上述具体来源 unavailable；无需以新 trial、充值、换账户、另开 CLI 或重放 Host GO 来猜历史事实。

本次只读结果：original_account_binding=UNKNOWN；original_provider_requests=null；response_or_provider_timeout=UNKNOWN；provider_server_termination=UNKNOWN；actual_cost=null；billing_finality=UNKNOWN；financial_coverage=false。Original run 的 formal/model acceptance=false，原失败745和一次性 Host GO 已消费事实保持。

机械失败1008：导入 discover.py 的无条件入口重进 discovery，xb 写既存 discovery.json 触发 FileExistsError。原 chunk8fb7f9 outer/Python actual exits1/1，其余 native/dispatcher/model NULL；failed attempt 无独立 guard.closed，记录 NULL。failure-origin.1008.json SHA 62b2f89fcaf0a17aadc966dee21aa8dd4b7d2143b8ecb95ef3aa4335aea4a15d /3487。旧脚本/原 IO 保留；新 library/revision 仅剥离入口包装器并完成有限 SourceGuard 真实关闭，未重跑原输入或重置计数。

本包 original-tool-io.json 是完整 stored tool argument/result 对象的 UTF-8 JSON 重编码，不冒充 raw transport JSONL。所有已成功读阶段的 guard.closed、公开 Source pins 和最终封存清单均可独立复查；私密原件未复制。当前 reconciliation author 不自接受产品/正式用例。
