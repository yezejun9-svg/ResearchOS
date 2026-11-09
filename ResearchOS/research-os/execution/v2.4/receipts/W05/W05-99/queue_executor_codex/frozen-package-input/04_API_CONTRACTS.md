# 04 API 与适配器合同

## v2.4 本地客户端操作对接

本HTTP OpenAPI与22的本地协议并存：HTTP承载领域操作；CLI/Desktop经同一宿主适配调用。不能把新增本地method当作上游Mu现成API或另建一套领域HTTP真值。client.protocol.schema.json定义researchos-client/2请求、按method约束的返回、SessionSnapshot和按type约束的事件。product.contract.json提供methods/payload/result映射；ui.contract.json将控件绑定到这些方法。

凭据输入与系统目录选择为受限native桥，检查sender/frame和本机身份；密钥不会通过普通CommandEnvelope、Artifact、事件或日志。host.configure只接受脱敏引用和已验证配置。普通permission.respond仅处理当前作用域待决请求，不能清除系统policy拒绝或提升调用者权限。

同一command_id不同请求拒绝；写入校验revision/epoch和文件hash。请求接受、工具完成、独立验收分别返回/投影；所有缺失handler非零NOT_IMPLEMENTED，不允许空成功响应。接口与错误的逐项详情及生产者见22。

版本：2.4.0。规范日期：2026-10-01。机器定义：`contracts/openapi.json`，OpenAPI 3.1.0，JSON Schema 2020-12，全部本地 `$ref` 可解析。以下 **都是我们定义的 ResearchOS `/v1` 接口**；不是第三方现有接口，也不表示服务已实现/启动。实现和真实接口验收状态：**NOT_RUN**。

## 1. 认证、权限与作用域

除配对redeem和会话refresh以专用凭据证明外，所有接口要求有效 Bearer token。令牌携带主体、角色、授权项目和可选task/run范围及过期时间，服务每次读取当前撤销状态；短期worker令牌不能调用用户设置或发布服务。OWNER由受保护的本机OS身份bootstrap一次性建立；远程设备配对、撤销和TLS流程由07运维合同定义，不将随机公开URL当认证。令牌明文、密钥、cookie不能进入日志、事件、ContextBundle或候选模型上下文。

| 角色 | 能力 | 排除的写入 |
|---|---|---|
| OWNER | 导入项目、授权资源范围、预算/策略、业务选择、暂停取消 | 不能以角色绕过未通过的正式验收 |
| PLANNER | 需求/Goal/Task/变更草案、证据组织和候选判断 | 不能自授范围、直接ACCEPTED、晋升系统 |
| EXECUTOR | 仅获派task/run范围的工具执行、当前租约心跳/回执 | 不能修改自己的验收标准、提交AcceptanceReceipt |
| VERIFIER | 独立核验来源/产物、资格评测与验收回执 | 不能验收自身所执行结果；不能直接发布候选 |
| SCHEDULER | 唯一领取/派单/预算预留/恢复/确定性状态迁移 | 不能伪造检查通过或生成独立验证者身份 |
| RELEASE_SERVICE | 独立的候选试用、晋升、回退与成果发布 | 候选代码及普通执行者没有其凭据 |
| SOURCE_ADAPTER | 授权来源只读采集、原始证据、游标 | 不能改需求/正式判断、接受任务、任意宿主文件访问 |
| READER | 已授权项目的侧栏、结果、证据、本人通知 | 没有执行/配置/验收权限 |

OpenAPI的`x-required-roles`表示可调用角色集合，**不是只要带其中一个字符串就获权限**。还必须匹配当前grant、project/task/run范围及动作策略；同主体叠加EXECUTOR与VERIFIER也不能验收自己的Run。GET列表按授权过滤，单对象跨项目读不泄露对象是否存在。全局策略端点不带project_id，写入仅OWNER；项目策略不能放宽全局限制。

## 2. 条件写、幂等与事务

- GET单对象返回强ETag，例如 `"r7"`。修改现有聚合或创建会影响父对象的子资源需 `If-Match: "r7"`。OpenAPI每操作的`x-precondition-target`说明ETag对象；不要用ProjectState ETag代替Task/Run/Goal版本。多对象apply另带expected_project_state_revision，仍由一次域事务校验。
- 所有POST/PUT带至少16字符的`Idempotency-Key`。初次合法执行保存主体、项目、operationId、key、规范化业务请求hash、目标及响应；至少保留7天，不可变成果创建映射随成果保留。客户端每个逻辑动作只生成一个key，传输重试复用原key。配对/refresh响应含秘密，是例外：响应仅加密保留至多5分钟且标no-store，长期只留消费/重放指纹；过期后拒绝重做发凭据副作用。
- 幂等重放先查记录：相同key、请求内容与目标完全相同，返回第一次状态码/响应和`Idempotency-Replayed: true`，不因当前revision已变而再次执行。对同key改变body/目标/If-Match返回409。修订计划或重新获取版本后应使用新key，禁止先覆盖旧响应。
- 首次请求缺条件头返回428；ETag过期返回412，附current_revision和当前ETag；幂等冲突、非法状态、已有有效租约、未验收依赖返回409。业务资格/预算/证据门失败通常422。认证和权限仍每次校验，包括幂等重放，撤销的主体不能借缓存取回数据。
- `recordAcceptance`的PASS、Task/Goal最终状态、依赖释放和outbox必须同事务完成。所选复用路线必须补足同步强制门；失败保留资格结果并按具体缺口处置，不能以异步补验收绕过。
- `uploadContent`先写受限临时内容；`sealArtifact`重算hash/size并封存。Artifact内容不可修改，后续纠正创建新对象。上传不接受任意宿主路径。
- `searchEvidence`是只读POST：幂等键只合并同一请求；输入必须snapshot_ids和state revision，不把用户字符串映射成磁盘路径。
- 对外网调用不能与本地数据库形成真正单事务。先写持久意图/预算预留/outbox，再以供应商支持的幂等键调用；若供应商不支持幂等且结果未知，必须对账/阻塞该支路，不能盲重试非幂等副作用。

## 3. HTTP结果与错误

201为资源已创建，202为取消等命令已接收，200为读取或命令回执。它们都不自动等于Task/Goal ACCEPTED。错误统一为`Error`：code、message、correlation_id、retryable、current_revision、details。详细枚举见schema；不把正常REJECT/INCONCLUSIVE实验结论当HTTP500。

| HTTP | 典型code | 客户端动作 |
|---|---|---|
| 400 | INVALID_REQUEST | 修正字段，不能原样无限重试 |
| 401/403 | UNAUTHENTICATED/FORBIDDEN | 刷新既有授权或停止越权动作，不能自动扩大权限 |
| 404 | NOT_FOUND | 核对项目和引用，不遍历其他项目猜ID |
| 409 | STATE_CONFLICT/IDEMPOTENCY_CONFLICT/DEPENDENCY_NOT_ACCEPTED | 读当前状态，对账或建立明确新动作 |
| 412 | STALE_REVISION/STALE_INPUT | 保留旧成果，获取新上下文并整合，不自动覆盖 |
| 422 | GATE_FAILED/UNQUALIFIED/BUDGET_BLOCKED/CONFLICT_OPEN | 保存实际阻塞及可继续部分 |
| 428 | PRECONDITION_REQUIRED | 补If-Match/幂等键；不是服务可随意放行的警告 |
| 429 | RATE_LIMITED | 遵守Retry-After，保留来源窗口；不记为成功扫描 |
| 503 | RESOURCE_UNAVAILABLE | 合格替代或去重ResourceRequest，独立支路继续 |
| 410（事件） | CURSOR_EXPIRED | 拉state/progress快照，以其sequence恢复订阅 |

失败写入不留下半个业务状态。Error不得包含秘密、跨项目实体内容、完整供应商凭据。未预期服务错误以INTERNAL_ERROR记录相关ID，不能伪造successful结果。

## 4. 规范操作清单

下表由同包OpenAPI生成，避免手写名称漂移。读取权限还需对象范围；表中实体Page含items、next_cursor、snapshot_event_sequence。默认page limit=50、上限100。列表可选过滤条件若实现，应显式升级OpenAPI，不能凭空暗加客户端约定。

| 方法与路径 | operationId | 角色 | 请求 → 响应 | If-Match目标 |
|---|---|---|---|---|
| `GET /v1/projects` | `listProjects` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ProjectProfilePage | — |
| `POST /v1/projects` | `createProject` | OWNER | CreateProjectRequest → ProjectProfile | — |
| `GET /v1/projects/{project_id}/profile` | `getProjectProfile` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ProjectProfile | — |
| `GET /v1/projects/{project_id}/state` | `getProjectState` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ProjectState | — |
| `GET /v1/projects/{project_id}/requirements` | `listRequirement` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → RequirementPage | — |
| `POST /v1/projects/{project_id}/requirements` | `createRequirement` | OWNER,PLANNER,SCHEDULER | CreateRequirementRequest → Requirement | ProjectState |
| `GET /v1/projects/{project_id}/requirements/{object_id}` | `getRequirement` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Requirement | — |
| `GET /v1/projects/{project_id}/goals` | `listGoal` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → GoalPage | — |
| `POST /v1/projects/{project_id}/goals` | `createGoal` | OWNER,PLANNER,SCHEDULER | CreateGoalRequest → Goal | ProjectState |
| `GET /v1/projects/{project_id}/goals/{object_id}` | `getGoal` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Goal | — |
| `GET /v1/projects/{project_id}/tasks` | `listTask` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → TaskPage | — |
| `POST /v1/projects/{project_id}/tasks` | `createTask` | OWNER,PLANNER,SCHEDULER | CreateTaskRequest → Task | Goal |
| `GET /v1/projects/{project_id}/tasks/{object_id}` | `getTask` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Task | — |
| `GET /v1/projects/{project_id}/runs` | `listRun` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → RunPage | — |
| `GET /v1/projects/{project_id}/runs/{object_id}` | `getRun` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Run | — |
| `GET /v1/projects/{project_id}/artifacts` | `listArtifact` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ArtifactPage | — |
| `POST /v1/projects/{project_id}/artifacts` | `sealArtifact` | EXECUTOR,VERIFIER,SOURCE_ADAPTER,SCHEDULER | CreateArtifactRequest → Artifact | ProjectState |
| `GET /v1/projects/{project_id}/artifacts/{object_id}` | `getArtifact` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Artifact | — |
| `GET /v1/projects/{project_id}/evidence` | `listEvidence` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → EvidencePage | — |
| `POST /v1/projects/{project_id}/evidence` | `createEvidence` | SOURCE_ADAPTER,PLANNER,SCHEDULER | CreateEvidenceRequest → Evidence | ProjectState |
| `GET /v1/projects/{project_id}/evidence/{object_id}` | `getEvidence` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Evidence | — |
| `GET /v1/projects/{project_id}/research-cycles` | `listResearchCycle` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ResearchCyclePage | — |
| `POST /v1/projects/{project_id}/research-cycles` | `createResearchCycle` | OWNER,SCHEDULER | CreateCycleRequest → ResearchCycle | ProjectState |
| `GET /v1/projects/{project_id}/research-cycles/{object_id}` | `getResearchCycle` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ResearchCycle | — |
| `GET /v1/projects/{project_id}/experiments` | `listExperiment` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ExperimentPage | — |
| `POST /v1/projects/{project_id}/experiments` | `createExperiment` | OWNER,PLANNER,SCHEDULER | CreateExperimentRequest → Experiment | ProjectState |
| `GET /v1/projects/{project_id}/experiments/{object_id}` | `getExperiment` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Experiment | — |
| `GET /v1/projects/{project_id}/decisions` | `listDecisionReceipt` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → DecisionReceiptPage | — |
| `POST /v1/projects/{project_id}/decisions` | `recordDecision` | PLANNER,VERIFIER,SCHEDULER | CreateDecisionRequest → DecisionReceipt | ProjectState |
| `GET /v1/projects/{project_id}/decisions/{object_id}` | `getDecisionReceipt` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → DecisionReceipt | — |
| `GET /v1/projects/{project_id}/qualifications` | `listQualification` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → QualificationPage | — |
| `POST /v1/projects/{project_id}/qualifications` | `createQualification` | VERIFIER | CreateQualificationRequest → Qualification | ProjectState |
| `GET /v1/projects/{project_id}/qualifications/{object_id}` | `getQualification` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Qualification | — |
| `GET /v1/projects/{project_id}/context-bundles` | `listContextBundle` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ContextBundlePage | — |
| `POST /v1/projects/{project_id}/context-bundles` | `createContextBundle` | SCHEDULER,PLANNER | ContextRequest → ContextBundle | ProjectState |
| `GET /v1/projects/{project_id}/context-bundles/{object_id}` | `getContextBundle` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ContextBundle | — |
| `GET /v1/projects/{project_id}/change-proposals` | `listChangeProposal` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ChangeProposalPage | — |
| `POST /v1/projects/{project_id}/change-proposals` | `createChangeProposal` | OWNER,PLANNER,SCHEDULER | CreateChangeRequest → ChangeProposal | ProjectState |
| `GET /v1/projects/{project_id}/change-proposals/{object_id}` | `getChangeProposal` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ChangeProposal | — |
| `GET /v1/projects/{project_id}/impact-links` | `listImpactLink` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ImpactLinkPage | — |
| `POST /v1/projects/{project_id}/impact-links` | `createImpactLink` | PLANNER,VERIFIER,SCHEDULER | CreateImpactLinkRequest → ImpactLink | ProjectState |
| `GET /v1/projects/{project_id}/impact-links/{object_id}` | `getImpactLink` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ImpactLink | — |
| `GET /v1/projects/{project_id}/resource-requests` | `listResourceRequest` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ResourceRequestPage | — |
| `POST /v1/projects/{project_id}/resource-requests` | `createResourceRequest` | SCHEDULER,PLANNER | CreateResourceRequest → ResourceRequest | ProjectState |
| `GET /v1/projects/{project_id}/resource-requests/{object_id}` | `getResourceRequest` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ResourceRequest | — |
| `GET /v1/projects/{project_id}/releases` | `listMilestoneRelease` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → MilestoneReleasePage | — |
| `POST /v1/projects/{project_id}/releases` | `createMilestoneRelease` | SCHEDULER,RELEASE_SERVICE | CreateMilestoneRequest → MilestoneRelease | ProjectState |
| `GET /v1/projects/{project_id}/releases/{object_id}` | `getMilestoneRelease` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → MilestoneRelease | — |
| `GET /v1/projects/{project_id}/skills` | `listSkillVersion` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SkillVersionPage | — |
| `POST /v1/projects/{project_id}/skills` | `createSkillCandidate` | PLANNER,SCHEDULER | CreateSkillRequest → SkillVersion | ProjectState |
| `GET /v1/projects/{project_id}/skills/{object_id}` | `getSkillVersion` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SkillVersion | — |
| `GET /v1/projects/{project_id}/system-candidates` | `listSystemCandidate` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SystemCandidatePage | — |
| `POST /v1/projects/{project_id}/system-candidates` | `createSystemCandidate` | PLANNER,SCHEDULER | CreateSystemCandidateRequest → SystemCandidate | ProjectState |
| `GET /v1/projects/{project_id}/system-candidates/{object_id}` | `getSystemCandidate` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SystemCandidate | — |
| `GET /v1/projects/{project_id}/acceptances` | `listAcceptanceReceipt` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → AcceptanceReceiptPage | — |
| `POST /v1/projects/{project_id}/acceptances` | `recordAcceptance` | VERIFIER | CreateAcceptanceRequest → AcceptanceReceipt | subject_ref |
| `GET /v1/projects/{project_id}/acceptances/{object_id}` | `getAcceptanceReceipt` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → AcceptanceReceipt | — |
| `GET /v1/projects/{project_id}/messages` | `listAgentMessage` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → AgentMessagePage | — |
| `POST /v1/projects/{project_id}/messages` | `sendAgentMessage` | PLANNER,EXECUTOR,VERIFIER,SCHEDULER | CreateMessageRequest → AgentMessage | ProjectState |
| `GET /v1/projects/{project_id}/messages/{object_id}` | `getAgentMessage` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → AgentMessage | — |
| `GET /v1/projects/{project_id}/source-cursors` | `listSourceCursor` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SourceCursorPage | — |
| `GET /v1/projects/{project_id}/source-cursors/{object_id}` | `getSourceCursor` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → SourceCursor | — |
| `PUT /v1/projects/{project_id}/source-cursors/{object_id}` | `advanceSourceCursor` | SOURCE_ADAPTER,SCHEDULER | UpdateCursorRequest → SourceCursor | SourceCursor |
| `GET /v1/projects/{project_id}/budget-ledger` | `listBudgetLedgerEntry` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → BudgetLedgerEntryPage | — |
| `POST /v1/projects/{project_id}/budget-ledger` | `appendBudgetLedger` | SCHEDULER | CostEntryRequest → BudgetLedgerEntry | BudgetPolicy |
| `GET /v1/projects/{project_id}/budget-ledger/{object_id}` | `getBudgetLedgerEntry` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → BudgetLedgerEntry | — |
| `GET /v1/projects/{project_id}/no-progress-records` | `listNoProgressRecord` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → NoProgressRecordPage | — |
| `GET /v1/projects/{project_id}/no-progress-records/{object_id}` | `getNoProgressRecord` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → NoProgressRecord | — |
| `GET /v1/projects/{project_id}/runtimes` | `listRuntimeRegistration` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → RuntimeRegistrationPage | — |
| `POST /v1/projects/{project_id}/runtimes` | `registerRuntime` | OWNER,SCHEDULER | CreateRuntimeRequest → RuntimeRegistration | ProjectState |
| `GET /v1/projects/{project_id}/runtimes/{object_id}` | `getRuntimeRegistration` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → RuntimeRegistration | — |
| `GET /v1/projects/{project_id}/conflicts` | `listConflict` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ConflictPage | — |
| `POST /v1/projects/{project_id}/conflicts` | `createConflict` | PLANNER,VERIFIER,SCHEDULER | CreateConflictRequest → Conflict | ProjectState |
| `GET /v1/projects/{project_id}/conflicts/{object_id}` | `getConflict` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Conflict | — |
| `GET /v1/projects/{project_id}/notifications` | `listNotification` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → NotificationPage | — |
| `GET /v1/projects/{project_id}/notifications/{object_id}` | `getNotification` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → Notification | — |
| `POST /v1/projects/{project_id}/requirements/{object_id}/actions` | `actOnRequirement` | OWNER,PLANNER,SCHEDULER | RequirementActionRequest → Requirement | Requirement |
| `POST /v1/projects/{project_id}/goals/{object_id}/actions` | `actOnGoal` | OWNER,PLANNER,SCHEDULER | ActionRequest → Goal | Goal |
| `POST /v1/projects/{project_id}/tasks/{object_id}/actions` | `actOnTask` | OWNER,PLANNER,SCHEDULER | TaskActionRequest → Task | Task |
| `POST /v1/projects/{project_id}/tasks/{object_id}/claim` | `claimTask` | SCHEDULER | ClaimTaskRequest → TaskClaimResponse | Task |
| `POST /v1/projects/{project_id}/runs/{object_id}/heartbeat` | `heartbeatRun` | EXECUTOR | HeartbeatRequest → Run | Run |
| `POST /v1/projects/{project_id}/runs/{object_id}/report` | `reportRun` | EXECUTOR | RunReportRequest → Run | Run |
| `POST /v1/projects/{project_id}/runs/{object_id}/cancel` | `cancelRun` | OWNER,SCHEDULER | CancelRunRequest → Run | Run |
| `POST /v1/projects/{project_id}/runs/{object_id}/cancel-ack` | `acknowledgeRunCancellation` | EXECUTOR | CancelAckRequest → Run | Run |
| `POST /v1/projects/{project_id}/runs/{object_id}/reconcile` | `reconcileRun` | SCHEDULER | ReconcileRunRequest → Run | Run |
| `POST /v1/projects/{project_id}/content` | `uploadContent` | OWNER,PLANNER,EXECUTOR,VERIFIER,SOURCE_ADAPTER,SCHEDULER | — → ContentUploadResponse | — |
| `GET /v1/projects/{project_id}/artifacts/{object_id}/content` | `getArtifactContent` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → bytes / SSE | — |
| `POST /v1/projects/{project_id}/evidence/{object_id}/verify` | `verifyEvidence` | VERIFIER | VerifyEvidenceRequest → Evidence | Evidence |
| `POST /v1/projects/{project_id}/research-cycles/{object_id}/checkpoint` | `checkpointResearchCycle` | SCHEDULER | CycleCheckpointRequest → ResearchCycle | ResearchCycle |
| `POST /v1/projects/{project_id}/research-cycles/{object_id}/close` | `closeResearchCycle` | SCHEDULER | CloseCycleRequest → ResearchCycle | ResearchCycle |
| `POST /v1/projects/{project_id}/experiments/{object_id}/register` | `registerExperiment` | OWNER,PLANNER,SCHEDULER | RegisterExperimentRequest → Experiment | Experiment |
| `POST /v1/projects/{project_id}/experiments/{object_id}/result` | `recordExperimentResult` | SCHEDULER | ExperimentResultRequest → Experiment | Experiment |
| `POST /v1/projects/{project_id}/change-proposals/{object_id}/analyze` | `analyzeChangeImpact` | PLANNER,SCHEDULER | ImpactReviewRequest → ChangeProposal | ChangeProposal |
| `POST /v1/projects/{project_id}/change-proposals/{object_id}/apply` | `applyChangeProposal` | SCHEDULER | ApplyChangeRequest → ChangeProposal | ChangeProposal |
| `GET /v1/projects/{project_id}/budget-policy` | `getBudgetPolicy` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → BudgetPolicy | — |
| `PUT /v1/projects/{project_id}/budget-policy` | `updateBudgetPolicy` | OWNER | UpdateBudgetRequest → BudgetPolicy | BudgetPolicy |
| `GET /v1/projects/{project_id}/run-policy` | `getRunPolicy` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → RunPolicy | — |
| `PUT /v1/projects/{project_id}/run-policy` | `updateRunPolicy` | OWNER | UpdateRunPolicyRequest → RunPolicy | RunPolicy |
| `POST /v1/projects/{project_id}/resource-requests/{object_id}/resolve` | `resolveResourceRequest` | OWNER,SCHEDULER | ResolveResourceRequest → ResourceRequest | ResourceRequest |
| `GET /v1/projects/{project_id}/progress` | `getProgressProjection` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → ProgressProjection | — |
| `POST /v1/projects/{project_id}/skills/{object_id}/promote` | `promoteSkill` | SCHEDULER,RELEASE_SERVICE | PromoteSkillRequest → SkillVersion | SkillVersion |
| `POST /v1/projects/{project_id}/system-candidates/{object_id}/actions` | `actOnSystemCandidate` | RELEASE_SERVICE | CandidateActionRequest → SystemCandidate | SystemCandidate |
| `POST /v1/projects/{project_id}/qualifications/{object_id}/result` | `recordQualificationResult` | VERIFIER | QualificationResultRequest → Qualification | Qualification |
| `POST /v1/projects/{project_id}/no-progress-records/{object_id}/advance` | `advanceNoProgress` | SCHEDULER | AdvanceNoProgressRequest → NoProgressRecord | NoProgressRecord |
| `POST /v1/projects/{project_id}/runtimes/{object_id}/qualify` | `qualifyRuntime` | VERIFIER | QualifyRuntimeRequest → RuntimeRegistration | RuntimeRegistration |
| `POST /v1/projects/{project_id}/conflicts/{object_id}/resolve` | `resolveConflict` | SCHEDULER | ResolveConflictRequest → Conflict | Conflict |
| `POST /v1/projects/{project_id}/notifications/{object_id}/read` | `markNotificationRead` | OWNER,READER | AcknowledgeRequest → Notification | Notification |
| `POST /v1/projects/{project_id}/search` | `searchEvidence` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | SearchRequest → SearchResponse | — |
| `GET /v1/projects/{project_id}/events` | `listEvents` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → EventEnvelopePage | — |
| `GET /v1/projects/{project_id}/events/stream` | `streamEvents` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → bytes / SSE | — |
| `GET /v1/policies/budget` | `getGlobalBudgetPolicy` | OWNER,SCHEDULER | — → BudgetPolicy | — |
| `PUT /v1/policies/budget` | `updateGlobalBudgetPolicy` | OWNER | UpdateBudgetRequest → BudgetPolicy | BudgetPolicy |
| `GET /v1/policies/run` | `getGlobalRunPolicy` | OWNER,SCHEDULER | — → RunPolicy | — |
| `PUT /v1/policies/run` | `updateGlobalRunPolicy` | OWNER | UpdateRunPolicyRequest → RunPolicy | RunPolicy |
| `GET /v1/projects/{project_id}/goals/{object_id}/budget-policy` | `getGoalBudgetPolicy` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → BudgetPolicy | — |
| `PUT /v1/projects/{project_id}/goals/{object_id}/budget-policy` | `updateGoalBudgetPolicy` | OWNER | UpdateBudgetRequest → BudgetPolicy | BudgetPolicy |
| `GET /v1/projects/{project_id}/experiments/{object_id}/budget-policy` | `getExperimentBudgetPolicy` | OWNER,PLANNER,EXECUTOR,VERIFIER,SCHEDULER,RELEASE_SERVICE,SOURCE_ADAPTER,READER | — → BudgetPolicy | — |
| `PUT /v1/projects/{project_id}/experiments/{object_id}/budget-policy` | `updateExperimentBudgetPolicy` | OWNER | UpdateBudgetRequest → BudgetPolicy | BudgetPolicy |
| `POST /v1/device-pairings` | `createDevicePairing` | OWNER | CreatePairingRequest → PairingChallengeResponse | — |
| `POST /v1/device-pairings/redeem` | `redeemDevicePairing` | 一次性/刷新凭据证明 | RedeemPairingRequest → DeviceSessionResponse | — |
| `POST /v1/device-sessions/refresh` | `refreshDeviceSession` | 一次性/刷新凭据证明 | RefreshDeviceSessionRequest → DeviceSessionResponse | — |
| `GET /v1/devices` | `listDevices` | OWNER | — → DevicePage | — |
| `PUT /v1/devices/{device_id}/grants` | `updateDeviceGrants` | OWNER | UpdateDeviceGrantRequest → DeviceRecord | DeviceRecord |
| `POST /v1/devices/{device_id}/revoke` | `revokeDevice` | OWNER | AcknowledgeRequest → DeviceRecord | DeviceRecord |

## 5. 关键调用顺序

### 5.1 从想法到首次研究

1. OWNER createProject（首次可无source_document_refs）产生隔离项目和默认策略；随后上传本项目资料，PLANNER生成明确basis的需求并actOnRequirement，创建Goal/Task。
2. SCHEDULER创建ResearchCycle、生成ContextBundle；SUBMIT Task经过依赖检查后READY。claimTask原子取得一个Run、lease_epoch和仅本次返回的lease_token。
3. EXECUTOR从获授权快照执行；SOURCE_ADAPTER按来源采集并封存证据，只有证据/检查点落盘后推进游标。来源缺口留在source_coverage。
4. 需要实验则先createExperiment/registerExperiment，冻结指标后开始Run。reportRun只代表执行稳定结束，产物须先sealArtifact。
5. 独立VERIFIER执行检查并recordAcceptance；服务重算所有不变量后产生PASS/FAIL/BLOCKED回执。只有合格PASS可原子完成Task，后继才获READY。
6. recordDecision记录ADOPT/REJECT/WATCH/INCONCLUSIVE；采用建议不自动部署。closeResearchCycle检查请求范围，生成成果时createMilestoneRelease写同一outbox和应用内通知。

### 5.2 变更、重启与取消

- 修改输入：createChangeProposal→analyzeChangeImpact（确定性闭包+语义补查）→独立验收→applyChangeProposal。旧版本提交获412或仅归档，不覆盖当前事实。
- 恢复：先reconcileRun、核对外部run/epoch/检查点，再恢复会话或合法新尝试；不能只因UI断连新建一份工作。
- 取消：cancelRun→CANCEL_REQUESTED；适配器清当前业务队列并终止本Run子进程→cancel-ack；服务器确认后CANCELLED。未收到ACK时仍显示待确认，恢复后对账。lease过期的旧ACK可作为历史证据归档，不能改新epoch状态。
- 暂停Goal不会让不可取消在途费用消失；预算和停止状态分别展示。UNKNOWN副作用不因同输入重试上限尚有余额而盲重发。

## 6. 事件、进度和通知

每个EventEnvelope含稳定id、project_id、单调sequence、aggregate_ref、actor/correlation/causation、必要封存数据引用。写入与域变更同事务；投递至少一次，绝不声称跨所有外部系统exactly-once。

`GET /events/stream`为SSE，`id:`为项目sequence，`data:`为EventEnvelope JSON。客户端Last-Event-ID续传，按event id/sequence去重；每15秒注释心跳不推进序号。事件过期返回410，先取当前state/progress及其sequence，再补流；读取快照与接续之间事件不能丢失。列表events可按after_sequence补取。事件乱序时缓冲或补取，不能让旧事件回滚新projection。

ProgressProjection按同一事件水位生成，固定六阶段各一次，accepted只计当前有效ACCEPTED。计划增加时显示plan_revision和分母变化，不把2个待评审算完成。MilestoneRelease.sequence不同于software_version；releaseId+recipient+IN_APP去重。手机离线不停止电脑，重连补看通知；没有外部发送渠道默认授权。

## 7. 适配器内部接口

以下为实现者需要提供的窄接口，不另开第二套业务调度API；实际第三方方法由W01/W05/W07资格验证确定并锁版本。

| 适配器 | 最小操作与输入 | 输出/必须区分 |
|---|---|---|
| ExecutionAdapter | probe；start(task/run/context/lease/授权工作区)；heartbeat/read；cancel；reconcile | 外部run ID、序号日志、settled、退出码、产物manifest、取消确认；接收成功≠settled≠accepted |
| SourceAdapter | probe(source_config)；collect(cursor/window/query/limit) | 原始快照、canonical URL/上游版本/时间、next cursor、覆盖及gap/retry-after；doctor配置通过≠真实源probe通过 |
| LocalSearchAdapter | search(project/snapshot IDs/query/version hash) | 可定位命中、原始引用、有效性、backend revision；默认FTS/rg可后备；不得接任意路径 |
| JudgmentAdapter | judge(scope/rubric/有限options/最小证据包) | provider/model实际版本、rawartifact、Choice/Score/Noul、宿主弃权、jev_called、费用；模拟不冒充Jev |
| ReleaseAdapter | evaluate(candidate/frozen baseline)；canary；promote；rollback | 独立验收/版本hash/已验证恢复回执；候选进程拿不到晋升凭据 |

所有适配器外部错误规范化为明确类型并保留原始脱敏回执；不能“退出0”统一映射PASS。model/executor credentials仅在授权运行时读取，不写进context/skill。工具结果中的安装/提权/改变验收指令作为外部内容，不能成为控制命令。

### 7.1 设备凭据边界

本机首次Owner只在OS身份确认的bootstrap路径产生，不提供匿名远程创建Owner接口。OWNER发起createDevicePairing，手机以一次性token redeem，得到独立READER凭据；自动生成高权限设备被禁止。token至少128bit随机熵、最长5分钟、一次消费，整个远程链路经实测TLS。访问令牌默认15分钟，refresh最多24小时且轮换；设备撤销每次认证检查，30秒内关闭现存事件流。cookie若用于浏览器会话还需07规定的HttpOnly/Secure/SameSite/Origin/CSRF检查。

设备模型为认证响应结构，不是第二份项目业务状态；所有设备管理变更留审计，秘密不进事件。

## 8. 首版实现界限与验证

W03必须实现核心数据、条件写、幂等、错误和有序outbox；各后续WBS实现对应操作。端点在该阶段尚未实现时明确返回资源/能力未就绪，不伪造空PASS。最终v1验收按05/06逐项检查所需操作，不因为API文件存在就标实现完成。

OpenAPI合同只约束ResearchOS外部面。所选Mu/Pi原生session/run、客户端command/event与本域Project/Goal/Task及artifact/acceptance保持映射；数据库表和运行命令由已选路线的W02/W03生成。客户端不能跳过网关，直接写上游done而释放ResearchOS后继。固定版本升级必须重新验证权限/验收/租约/取消/回放门。

## 9. v2.4工作台与评测映射

公开端点仍沿用本产品/v1合同，不新增第三方API假设。UI页面的operationId/字段映射见contracts/ui.contract.json。SSE至少一次投递、id去重和sequence补取；410时读取state/progress带水位快照后重订阅；客户端重放不得触发业务写入。

EvaluationReport/Summary经uploadContent与sealArtifact保存，结合既有Run、Experiment与Acceptance提交。所有API继续条件写、幂等、项目权限与独立验收；外部evalId或退出0没有接受权。

sealArtifact必须接收并由服务端核定access_class。关联内容为VERIFIER_ONLY时，列表/已知ID/下载/搜索/context/events/export/preview均按同一受保护策略过滤，不能因角色具备一般项目读取权限就返回受限正文。详细结果的公开降级必须新建经独立确认的脱敏汇总产物，不能PATCH旧封存内容。

getArtifactContent返回实际Content-Type、Digest与nosniff。客户端以固定Artifact版本/hash校验预览；HTML按10中的独立无脚本规则渲染，不能把任意产物当作同源网页执行。手机设备scope同样适用。

UI暂停/恢复/取消使用既有actOnTask/actOnGoal/cancelRun等受支持操作；Task没有PAUSED枚举，不得新增前端专有状态回写。202表示接收，完成状态须等权威回执；409/412保留草稿并处理差异。

## 10. Harness接入

复用已有创建/读取DecisionReceipt和Artifact、运行事件、检查点、条件写及服务端接受接口。Mu/QM原生met事件先作为带来源/版本的Run观察记录，不能由客户端转成recordAcceptance PASS。完整完成证据指向不可变产物并再次校验当前版本；不能以文本结束语或最后命令替换必需检查集合。新增公开接口需独立合同修订，本版不预设第三方已有同名接口。

## 11. 本地会话协议与HTTP域接口

CLI/Desktop会话、流式工具与控制走client.protocol.schema定义的本地协议，方法与域operation映射见product.contract.json。此协议由本产品实现，优先映射上游已有能力。会话send/control绑定当前项目、session、revision及writer_epoch；宿主对剩余方法执行14中的方法参数校验并在W03固化，不能接受任意payload后直接转shell。

公开/v1域接口继续处理项目、Goal、Task、Run、产物和验收。两种传输共享服务处理器、授权和幂等语义，不各建一套可绕过校验的写路径。Desktop本地协议不直接暴露给不可信预览；远程手机仍走已验证认证/TLS入口。

## 12. v2.4采用决定的接口落位

不增加公开端点。调查快照、SourceCandidatePayload与AdoptionDecisionPayload使用现有Artifact创建/读取，模型选型使用现有DecisionReceipt创建/读取与JudgmentAdapter，实际试验使用Experiment/Run，独立验收走AcceptanceReceipt；CLI/Desktop通过既有事件投影读取相同结果。

scope.task_type=reuse_selection，选项必须含拒绝/观察/补证路径。程序核对selected属于冻结options、被选源码在候选清单、输入及源码hash仍有效；对应Jev资格不从其他用途借用。未获有效接受的ReuseDecision、调查clone、Jev文本推荐或工具exit0不能触发稳定采用。并发重复提交继续服从Idempotency-Key、If-Match、项目权限和既有事务门。

W10的EvaluationAdapter可调用固定skill-up CLI。输入绑定冻结Experiment、预期样例及维度；回传原始result.json/事件和各维度EvaluationReport，不把上游summarizeResult直接写成产品PASS。对应03、11、16及contracts/adoption.contract.json。

## v2.4 完整本地方法索引

本地协议23方法、14类事件的精确定义由22和client.protocol.schema.json给出；此表为同源投影。NativeBridge仅传瞬态秘密，不属于普通命令日志。

| 方法 | 请求 | 成功结果 |
|---|---|---|
| `host.status` | `EmptyPayload` | `HostStatusResult` |
| `host.configure` | `ConfigurePayload` | `ConfigureResult` |
| `project.bootstrap` | `BootstrapPayload` | `BootstrapResult` |
| `session.list` | `ListSessionsPayload` | `SessionListResult` |
| `session.create` | `CreateSessionPayload` | `SessionSnapshot` |
| `session.get` | `EmptyPayload` | `SessionSnapshot` |
| `session.attach` | `AttachPayload` | `AttachResult` |
| `session.send` | `SendMessagePayload` | `SendMessageResult` |
| `session.control` | `ControlPayload` | `ControlResult` |
| `session.events` | `ReadEventsPayload` | `ReadEventsResult` |
| `session.handoff` | `HandoffPayload` | `HandoffResult` |
| `goal.start` | `StartGoalPayload` | `StartGoalResult` |
| `provider.models` | `ListModelsPayload` | `ListModelsResult` |
| `provider.probe` | `ProbeProviderPayload` | `ProbeProviderResult` |
| `workspace.register` | `RegisterWorkspacePayload` | `WorkspaceBinding` |
| `workspace.list` | `EmptyPayload` | `WorkspaceListResult` |
| `workspace.tree` | `WorkspaceTreePayload` | `WorkspaceTreeResult` |
| `workspace.read` | `WorkspaceReadPayload` | `WorkspaceReadResult` |
| `workspace.diff` | `WorkspaceDiffPayload` | `WorkspaceDiffResult` |
| `workspace.write` | `WorkspaceWritePayload` | `WorkspaceWriteResult` |
| `artifact.import` | `ImportArtifactPayload` | `ImportArtifactResult` |
| `session.update` | `UpdateSessionPayload` | `SessionSnapshot` |
| `permission.respond` | `RespondPermissionPayload` | `RespondPermissionResult` |
