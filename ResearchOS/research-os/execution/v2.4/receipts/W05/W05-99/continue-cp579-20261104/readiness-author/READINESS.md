# 普通 Mu 编码业务闭环：下一施工依据

作者 codex:/root/runtime_readiness；2026-11-04。证据类别 SOURCE_READINESS_AND_PUBLIC_RESOURCE_METADATA；无源码修改、测试、native/product 启动或推理；formal_increment=0。此报告不是运行许可、独立接受或已实现声明。主仓库的旧成果、失败计数、UNKNOWN 费用和 scope 均保留。

## 结论与最小下一施工范围

建议下一里程碑只支持一种版本化业务合同 `coding.workspace-delivery-v1`：单 Goal、单 delivery mu_turn、一个新建且已合法授权的离线 Go 包、一份允许修改的业务 .go 文件、冻结且不许修改的业务测试与依赖。沿用 CLI/Desktop → ClientService → sole RuntimeCoordinator → Host broker 的执行路径；通过真实 Mu turn、完整 Host 检查证据、最终交付源码及独立 Task/Goal 接受形成闭环。不得宣称一般程序修复正确性或整个 ResearchOS 已完成。

下一 SOURCE_ONLY scope 建议为 `NEXT-CODING-DELIVERY-CONTRACT-V1`：在当前两个施工 owner 完成并串行整合后，冻结业务合同和当前 HEAD，由独立 source reviewer 先审该合同与证据边界，再实现专用快照/检查器及精确 Goal 例外。此 scope 不启动 Ollama、产品、native chooser、qualification 或真实编码，不重放旧失败，不覆盖原数据，不改变冻结规范、正式阈值或计数。

最低业务合同应独立确认以下字段和含义：版本、Goal/Task 身份、Requirement/input refs、contract hash、当前 Workspace/profile/model binding、原始业务需求、允许变更路径、固定只读测试和依赖 hash、要求真正执行的 test names/check IDs、资源限额、最终源码交付格式、接受规则、原 origin/candidate/input 身份与失败 lineage。该绑定由服务在正常 Goal/Task 创建事务写入，只读合同 Artifact 可作为输入；模型输出、验收请求和外部 PASS 文件不能临时创建或改变业务类型。

## 三个不同的门

1. Workspace 首次授权：CLI init 在 apps/cli/cli_contract.go:356 获取本地身份，:364 调 cliChooseWorkspace，:376 用单次 selection_ref 调 workspace.register。internal/domain/project_workspace.go:5-7 明确 trusted chooser → selection_ref → register → bootstrap；:238 复核 ConfirmPath。现有 coding 步骤只复核已存在 binding（client_runtime_coding_windows.go:129,535），但新 root 的首次注册不能靠任意 --path、伪 selection 或直接 DB 写入替代 chooser。旧 CP575 C/D 两次 scope 已消费；这不证明当前候选必然失败，也不授权重跑旧 helper。
2. 普通 Mu 资格：新 root 自己的 Owner/project/session/config/READ_WRITE Workspace 与 coding 确认；codingConfirm 后仅 REGISTERED（client_runtime_coding_windows.go:360）。随后真实单次资格执行、独立 verifier、有限期 mu_turn purpose（internal/host/runtime_qualification_windows.go:157-232）。自动配置仅 credential=nil 与 numeric-loopback（client_runtime_setup_windows.go:46-71）；既有 DPAPI record 的只读引用不转移权限或资格。旧10月资格不能当11月当前资格。C57 backup/SACL/不同 SID 不是该普通链的通用前置；更换已经登记的 verifier 才有单独管理员门（runtime_qualification_windows.go:90）。
3. 业务接受：任务级 LIVE native acceptance 已存在；通用 LIVE Goal 仍在 acceptance_goal.go:71-81 返回503，仅 exact planning binding 例外。必须先有专用业务 checker 与受支持的精确绑定，再对白名单合同开放；不能直接移除503、按 mu_turn 一概放行，或改成 FIXTURE。

## 可复用的可信执行和证据

- runtime_model_verification.go:397-398 明说 verifyMuTurn 只证明有限 turn 执行。它验证 sealed SDK result 的 Task/Run/epoch/model，broker PREPARED/STARTED/CONFIRMED 历史，冻结 route、预算、实际 MODEL/TOOL 数与顺序、SSE 与 SDK 历史相等（:418,438,474,511,638,686,733,753）。:756 的 PASS 不证明业务修复正确。
- internal/host/runtime_check_windows.go:24-27 已允许变更业务源码捕获当前 bytes，而固定依赖带 hash；:124-130 的 argv allowlist 目前是普通 go test，没有 -json。:504-544 对 staging source manifest 再读防竞态，:551-569 真实离线 sandbox、完整 source/toolchain/vendor manifest、原始 stdout/stderr 和 cleanup 证据。进程未启动、UNKNOWN、超时、清理不完整不能作为检查通过。
- runtime_tools_windows.go:197-217 将完整 host_evidence 从模型可见结果移走，绑定到受保护 effect fact；runtime_broker_windows.go:362-414 核对 dispatch/epoch/request/receipt/evidence hash；runtime_session_events_windows.go:167-232 对照 canonical effect，并封存 REPORT/LOG Artifact。可复用这条来源，不能信任模型提交的报告或任意 Artifact ref。
- Host write/edit 使用 expected_hash 和 durable intent，发布前重新验证权限及 root（internal/host/runtime_tools_windows.go:189-200,398-436）。保留已有唯一写入器。

## 建议代码落点与精确新增规则

A. `internal/domain/client_protocol_goal.go` + 新 `coding_delivery_binding.go`：正常创建事务记录版本化私有业务绑定。保持 stable Requirement/origin/candidate/input 身份及既有 NoProgress lineage，不用新 Task/namespace 获得零失败记录。

B. 新 `internal/domain/coding_delivery_acceptance.go`，接入 `acceptance.go:244-248,275-295`：增加独立快照和 `coding.workspace-delivery-v1` 确定性 checker；现有 `mu.turn-output-v1` 仍是必选执行检查。快照只从当前受保护 Run/dispatch/effect 和已封存 Host REPORT/LOG/source Artifacts 推导，绑定完整来源，不把 TOOL_RESULT UI 投影本身当权威。

C. `internal/host/runtime_check_windows.go`、`runtime_coding_windows.go`：以新版本检查模式支持严格固定 `go test -json -count=1`，沿用离线/无 cgo/资源限制。解析完整原始事件，要求预先登记的每个业务 test 真正 start 并 pass；无测试、只 package pass、skip、missing test、额外失败、截断或无完整终态均不能 PASS。旧冻结检查和旧 argv 行为保持兼容。

D. 交付证据：全部要求 check IDs 均有同一 Task/Run/epoch/profile 的 CONFIRMED Host 事实；最终检查位于最后一次 write/edit 之后；检查的业务源码 manifest 与最终封存交付源码逐字节一致；测试、go.mod/go.sum、依赖/toolchain hash 均未改变；之后出现写入或当前快照漂移即失效。需要把最终源码 bytes 或有内容寻址的 source bundle 保留为 sealed Artifact，不能只保留可变目录路径。保留原始输出及 sandbox 清理证明，费用 UNKNOWN 不能变0或被释放。

E. `runtime_model_verification.go` 当前 :410 要求恰好一个 sealed SDK result；新增交付 Artifact 时必须按 Host 冻结的 SDK result 身份/角色精确分离，继续要求唯一 SDK result，不可把 len(artifacts)==1 简单删掉或允许模型选择哪份是结果。业务 source/report 由专用 checker 验证，完整 Task 输出向量仍与 Runtime provenance 一致。

F. `internal/domain/acceptance_goal.go:71-81`：仅对服务端私有 binding 精确匹配的单 Goal/单 Task、新业务合同及当前独立 PASS Task receipt 开放例外；对该类型同样执行 nativeDispatchProof/currentDispatchAdmission（目前 :124-148 的分支要抽取复用），然后执行所有原有 Goal 检查。未支持普通 LIVE Goal 仍503。

G. CLI：`apps/cli/coding_task.go:53,414` 仍固定 NotRoutedWriter，错误文字称无 workspace.write 已落后于当前 v2 源码。当前真实 workspace.write 已有（client_workspace_write.go:113），但它只允许 DRAFT/READY/BLOCKED/NEEDS_REVALIDATION 且同 root 所有 Run 已停止并 reconciled（:45-100），是手动编辑路径，不可拿来替换活动 Mu 的 broker 写入。建议为新的 `task <objective> --project ...` 形状委托已有 goal.start/shared Host 路径，保留旧 deterministic -replace/-check 形状及其真实拒绝；参考 cli_run_contract.go:40 的兼容分派。禁止 os.WriteFile fallback 或 CLI 直接打开 DB。CLI 任意 -check 命令不能成为业务验收来源。

## 必须保留的接受、lease 和 RBAC invariants

acceptance.go:11-15,76-81 要求当前 VERIFIER 项目权限、可见引用和不同 authority root，executor/alias/delegate 不自验。:39-69,172-234 要求冻结合同、SETTLED/current epoch/context、native dispatch、当前资格/purpose、全部冻结 checks 和精确 sealed 输出向量。:268-269 在短事务读快照、事务外计算，:365-373 提交前重建快照并比较；当前策略、绑定或引用变化则拒绝。

acceptance_goal.go:57-69,108-122,149-198 要求冻结 Goal 合同、所有 Task 独立接受、模式一致、Goal verifier 与交付 executor authority 分离、精确输入/输出/身份向量。保留现有 cancellation、writer lease/epoch、只读 root pin、权限撤销、预算与 UNKNOWN 处理，不增加平行 scheduler、worker 或 writer。

## 最低独立复核用例

- 一次真实受支持 Go 修复：变更业务文件、全部冻结业务测试实际通过、封存源码与检查一致，Task 后 Goal 独立接受。
- assistant 自报完成、只有 Mu PASS、只有工具 exit0 或不存在/跳过测试均不得业务 PASS。
- 测试或依赖被改、业务产物 hash 不同、检查后再写、并发外部编辑、缺失 source bytes 均拒绝。
- 外项目/旧 Run/旧 epoch/profile 的 receipt、伪 Host report、UNKNOWN/NOT_APPLIED 作为成功、超时/清理失败均拒绝。
- 无当前资格/purpose、lease/authority 撤销、executor alias 自验、prepare/commit 间输入变化均沿原门拒绝。
- 未绑定的普通 LIVE Goal 仍503；旧 finite-turn、FIXTURE、planning 和旧 CLI 形状保持原语义。失败只记一次并保留 origin，无隐含自动重试。

## 资源状态和实际操作上限

本次自己的 metadata GET 实际次数=1，推理=0，凭据发送=false。目标为原来明确声明的 http://127.0.0.1:11435/api/tags；08:54:41Z 在当前普通执行上下文报 socket 访问权限拒绝（chunk6a6fdd，outer0，catch 已记录）。没有 HTTP status，不据此断言服务离线，不重试。

Root另行报告自己的 elevated GET 在08:55:43Z得到 ConnectionRefused（d81bc0/25b111，local-model-resource-elevated.json）；不是本Agent第二次GET。当前不启动Ollama。旧 exe SHA4e91d8fb44e0909ab69feec21c3699ae82843b56ce631b37491255c2dc6b0792、qwen3:4b-instruct manifest SHA0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0 已只读核对仍存在；这不是当前模型健康或资格。

后续实际闭环需要：可信 chooser 与新 Workspace 注册；当前候选的 native Core/Mu/Node/独立 verifier；冻结 Go toolchain与原始测试资源；可用且精确声明的本地模型服务；本实例一次性资格确认及明确受限 coding 任务 scope；当前 RBAC/purpose/budget policy。若使用远程付费 provider，另需精确资源/费用授权，旧 sealed record 或旧一次性试验 scope 不足。C57原数据恢复支路保持独立阻塞，不以新 root 绕过它。

## 诊断与前轮 scope 限制

前轮旧 normal scope CP494:35-40 仅指定旧root/package/userdata一次资格、最多1本地模型/tools0；bc269e77…已消费且 UNKNOWN/未接受。provider 历史 chain 的5累计history失败/9origin、P9-P12-SR01的3origin、whole9准备2origin均保留；原生CP575两helper scope已消费。Original trial once-consumed、provider_requests=null、financial_closed=false不因新scope消失。

本报告附 diagnostic-index.json。前轮多数工具只把 output 文本转发，未把 chunk_id/exit_code 转发到模型可见结果，故不能补造精确ID/exit；它们应由Root原工具记录定位。已知失败内文如实登记，不能把本轮定位错误当产品/模型失败或重置旧计数。
