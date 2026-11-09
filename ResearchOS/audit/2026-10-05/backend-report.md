# ResearchOS 后端独立审计（2026-10-05）

审查版本：`a22b73aa37cd02e257d9d4ac0ed645b980ce3d82`。
范围：当前生产注册的 `POST /v2/command`、会话交接、v1/v2 持久化互操作。只读产品源码，未改产品代码、正式数据库、卡片状态或施工回执。

下面 3 项均通过真实 Go handler + 每个测试独立的临时 SQLite 复现。没有启动监听端口、调用外部模型或访问生产数据。测试的 PASS 表示“缺陷成功复现”，不是产品验收通过。会话通过正式 `MapClientSession` 映射函数种入隔离库，用于检测已实现服务边界；本测试不证明当前用户界面可端到端创建这些会话。

## P1：project_id=null 绕过项目授权，可读私有会话并夺取 writer

- 位置：`internal/api/v2.go:180-185`；`internal/domain/client_protocol.go:819-827`、`874-887`。
- 触发：持有效凭证但对目标项目没有任何 grant，知道目标 session ID，发送 `session.get` 或接管型 `session.attach`，把 envelope 的 project_id 设为 null。
- 实测：同一凭证、同一 session，显式 project_id=p-secret 返回 HTTP 403；null 返回 HTTP 200 COMPLETED，包含 PRIVATE TITLE、workspace/model/native session 引用、writer 等完整 snapshot。随后无授权接管返回 HTTP 200 ACKNOWLEDGED。
- 根因：边界只检查客户端非空 project_id；会话查询允许空 project，找到真实行后使用行里的 project 返回数据。接管型 session.attach 未列入强制 project_id 的 writeMethods，故同样绕过。
- 影响：已有凭证可以跨项目读会话、改变 writer；不是匿名攻击，前提是知道 session ID。
- 最小修复：方法级校验必须限制哪些 host 方法允许 null；会话解析后用其真实 project 再检查 Principal 的 grant。完整 Principal 应贯穿授权层，并对写方法施加角色/设备限制，不能仅向服务传 principal.ID。
- 已有测试遗漏：`tests/contracts/check/main.go` 的 envelope helper 固定 p1（约 285-296 行），HTTP 测试也显式 p1（878 行），没有“不授权 principal + null project + 已知 session”组合。

## P1：HTTP 会话接管绕过 W06 已实现的运行中停机确认

- 位置：`internal/domain/client_protocol.go:959-964`。
- 对照正确门禁：`internal/domain/session_service.go:201-215`。
- 触发：会话关联 RUNNING run，children_stopped=false、queue_empty=false；新 client 提供当前 revision，请求 session.attach(request_write_owner=true)。
- 实测：`Service.AttachClientSession` 返回 STOP_CONFIRMATION_REQUIRED；同一数据库的当前 /v2/command 路径返回 ACKNOWLEDGED，writer_epoch 从 1 变 2、writer 换为新 client，原 run 仍 RUNNING。
- 根因：两套交接实现分叉。W06 服务检查 live run 的 stop confirmation，HTTP 使用 W03 ClientService，直接调用 HandoffEpoch，只检查 epoch/revision，并未调用 W06 门禁。
- 影响：CLI/Desktop 接管时旧执行进程未停止，新 writer 已获得会话，破坏单写者交接保障；原进程后续副作用不会因仅更新数据库 epoch 自动消失。
- 最小修复：提取一个接受现有 tx 的权威交接函数，将运行状态、停机确认、epoch、writer、lease 和事件写入放在一次事务内；HTTP 与直接服务都调用它。不要直接在已有单连接事务内调用另一个自行 BeginTx 的方法。
- 已有测试遗漏：`internal/domain/session_w0602_test.go:145-148` 验证的是直接 AttachClientSession；typed 协议测试使用另一实现，未将 live-run 负例经真实 HTTP 路径重放。

## P1：v2 事件占用 v1 outbox 序号后，后续 v1 业务写入持续 409

- 位置：`internal/domain/client_protocol_journal.go:115-125`；对照 `internal/domain/store.go:336-365`。
- 触发：同一项目先产生 v1 业务事件，再产生 typed 会话事件（例如 session.attach），然后继续 v1 需求/任务等会写事件的操作。
- 实测：v1 createProject 后 ProjectState.event_sequence=1；v2 attach 在同一 outbox 插入 sequence=2，但只推进 session watermark。下一次 v1 createRequirement（带最新 ETag）返回 HTTP 409 STATE_CONFLICT / persistent invariant rejected operation。
- 根因：v1 以 ProjectState.event_sequence+1 分配项目事件序号；v2 以 outbox MAX(sequence)+1 分配，未推进 ProjectState。outbox 的主键是 (project,sequence)，故 v1 再次申请 2 冲突并整体回滚；回滚也保留旧 event_sequence，重试无法自然恢复。
- 影响：一次会话事件就能卡住该项目后续 v1 业务变更。除编号冲突外，v1 SSE 按 EventEnvelope 解读 outbox，typed SessionEvent 的结构也不兼容，不能仅把 max 值抄回 state 当完整修复。
- 最小修复：统一项目事件编号及事件类型分发，或为 session journal 使用独立表并保持原子事务；v1 SSE 与 session replay 必须消费各自正确的事件类型。
- 已有测试遗漏：协议测试直接种 Project/Run/client_sessions，不创建 ProjectState（`tests/contracts/check/main.go:244-246`、`867-876`）；分别验证 journal 自洽，没有测试真实 v1 createProject → v2 event → v1 write。

## 复现文件及命令

- `backend-audit_test.go`：三个复现测试源。
- `backend-overlay.json`：Go overlay，仅增加虚拟测试文件，不修改仓库源码。
- `backend-results.txt`：实际命令原始输出。

工作目录 `D:\作品集\ResearchOS\research-os`，PowerShell：

```powershell
$env:GOCACHE='D:\作品集\ResearchOS\research-os\.local\gocache'
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\gopath'
& '.local/tools/go1.27.1/go/bin/go.exe' test -overlay 'D:\作品集\ResearchOS\audit\2026-10-05\backend-overlay.json' ./internal/api -run TestBackendAudit -count=1 -v
```

最终运行退出码 0，3 个测试均成功复现。SQLite 文件由 testing.T.TempDir 自动清理；另建的临时 overlay 工作目录在留存这些证据后删除。

