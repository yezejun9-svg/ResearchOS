# W11 产品结果入库独立安全审查

结论：**PASS_IN_PRODUCT_ADMISSION_FIXTURE_SCOPE**。冻结版本 `f4833c2236fcd922802d52abebe51c0207e4f24c` 的已审查入库边界未发现阻断漏洞。独立新增 30 个审查场景通过；作者相关回归也通过。本结论只覆盖源码、公开夹具、临时 SQLite、真实 HTTP 拒绝/声明路径及本地凭据文件 ACL，不签发 W11 完成、A08 正式验收、真实模型资格或自动决策授权。

审查者：`/root/workbench_verifier`。独立工作树 `.local/worktrees/w11-admission-review`，产品源码未修改。该工作树只增加两个审查测试文件；可复现副本存于本包 `probes/`。测试复用作者的公开夹具构造 helper，但请求、攻击变体、期望值和结果断言由审查者独立编写。

## 验证结果

| 边界 | 独立证据 | 结果 |
|---|---|---|
| HTTP 身份及 schema | 实际 loopback httptest.Server、真实 handler 与临时 SQLite：匿名、无效凭据、已撤销主体、错误角色、无 restricted grant、客户端 proof 字段 | 401/403/400；零 AcceptanceReceipt，资格仍 DRAFT/ADVISORY |
| HTTP 前置条件 | 缺 Idempotency-Key、缺 If-Match、旧 revision、弱 ETag | 428/428/412/400；零业务接受副作用 |
| 客户端不能授予资格 | FIXTURE 声明接受 LIVE/PASS 请求；完美分数及 BOUNDED_AUTO result 请求 | 503；客户端字段不能绕过 native proof |
| 声明与幂等 | 实际 HTTP createQualification，客户端 jev_called=true；完全相同重放；同 key 不同 body | 201 DRAFT/ADVISORY、服务存 false、重放完全一致；冲突 409 |
| proof 与冻结合同 | nil proof、非 COMPLETED、无 dataset、总数/留出数、对象 hash、冻结时间、标签依据、policy、contract、subject ref 变体 | 全部拒绝；没有新增接受回执 |
| 结果引用及当前授权 | receipt 后 policy 改变、错误证据 ref、另一个合法独立 verifier、二次 result | 全部拒绝；保留原一条回执 |
| 可公开结果 | 内部真实事务 accept→result；检查 sealed PROJECT artifact 与 SQLite | 仅固定 SafeSummary；input_refs/source_refs 为空；无私密 canary 或本次凭据；最终 FAILED/ADVISORY |
| 本地凭据管理 | 临时 DB 新建 VERIFIER；Windows 实际 DACL；重复路径；同 ID 尝试升级 OWNER | DACL 禁止继承且仅当前用户；已有文件逐字节不变；已有角色及授权不变；失败文件不存在；仅一条 hash 凭据 |

`independent-probes.raw.txt` 含 29 个独立场景（12 HTTP 拒绝、1 HTTP 声明/幂等组合、16 proof 场景）。`targeted-regression.raw.txt` 含第 30 个独立 CLI 场景及作者指定回归：冻结声明双 scope 幂等、成功 FAILED/ADVISORY 入库、14 个漂移/篡改变体、本地管理员入口。

首轮审查测试有夹具错误：客户端 PASS check 未附 evidence_ref，schema 在发 HTTP 前拒绝。修正为引用公开开发 artifact 后重跑全套独立探针通过。首轮原始输出保留于 `independent-probes.initial-harness-error.raw.txt`；它不是产品失败，也没有作为通过证据。

## 源码证据与边界判断

- `internal/domain/qualification_live.go:39`：prepare 先认证 VERIFIER、项目与 restricted grant，读取当前声明，结束事务后调用具体 `protectedstore.QueryFrozenService("aggregate")`。没有客户端可供注入的 proof 参数。
- `internal/domain/http.go:78`、`:106`、`:230`：prepare 后开启主事务再次认证；schema、visible、Idempotency-Key、强 ETag 在写入前检查。proof 绑定读取时对象 hash 和 principal ID；主事务中的 `qualificationBinding` 再验当前 role/grant 与输入有效性。
- `internal/domain/qualification_live.go:74`：绑定 COMPLETED、FAILED、ADVISORY、当前 DRAFT/LIVE/OBJECTIVE、固定阈值 hash/冻结时间、完整 scope、每键 45/15 样本数、有效期、有效 artifact refs、公开开发集固定 hash、私有 dataset ticket/hash/大小/media type。实际 verifier 不得是任一输入 produced_by。
- `internal/domain/qualification_live.go:144`、`:182`：服务自行生成接受 checks/PASS 回执，PASS 只表示失败评估证据完成；result 再绑 receipt hash、scope 合同、subject revision、policy、verifier、唯一 sealed summary ref 及精确统计，强制写 FAILED/ADVISORY。
- `internal/domain/qualification_import.go:11`：本地导入先限定 hash 固定开发集及 restricted OWNER；读取终态服务 aggregate，再注册 opaque private artifact，重认证后 seal 公开开发 bytes 并声明双 scope；不创建 AcceptanceReceipt。`:72` 检查现有声明合同并返回同一声明。
- `internal/domain/protected_artifacts.go`：原生 frozen provider 路径只接受服务描述符，不把受保护正文读回控制面；产物 access 固定 VERIFIER_ONLY，登记人取当前主体，拒绝普通上传替代及静默改变私有/公开分类。
- `apps/control/credentials.go:52`：创建新文件后先设置 privateFile，再 provision/issue/write；O_EXCL 阻止覆盖；`auth.go:26` INSERT 主体不能替换现存行。本地 CLI dispatch 不存在对应 HTTP route。Windows DACL 实际验证通过；写入之前的执行顺序为源码核对。
- `adapters/protectedstore/broker_windows.go:260` 及 native 调用链：固定命令、SCM 服务账户/配置、pipe 服务 PID、查询后的同 PID/Running、已安装二进制 hash 与 summary BinaryHash 绑定。本次仅静态审查，没有执行该调用链。

## 未覆盖与资格边界

未读取正式 holdout、真实 provider 密钥或安装服务状态；未发送 native IPC、未调用真实模型、未触发 UAC。HTTP 探针在 FIXTURE 声明或不具备 restricted grant 的 guard 处确定返回，避免 native 查询。成功 accept/result 的内部 proof 来自明确 PUBLIC_FIXTURE_ONLY 的测试构造，不能代表操作系统隔离或真实服务证明。

因此，**成功 HTTP accept→result 全链路及本地 ImportFrozenQualifications 的原生服务成功分支未做动态验证**；当前隔离授权下没有安全测试接缝，保持这一证据缺口，不通过替换产品原生绑定来伪造真实链路。真实入库操作后仍须由主线程在已授权独立身份/运行环境下复核 actual HTTP response、SQLite 终态和 sealed artifact。此缺口不转化为模型资格或正式 A08 PASS。

## 复现

从上述冻结 commit 创建独立 worktree；将 `probes/domain-review-test.go.txt` 复制为 `internal/domain/w11_independent_review_test.go`，`probes/control-review-test.go.txt` 复制为 `apps/control/w11_independent_review_test.go`。使用仓库固定 Go 1.27.1，设置 `GOTOOLCHAIN=local`、`GOENV=off`：

```powershell
go test ./internal/domain -run '^TestReviewerW11' -count=1 -v
go test ./internal/domain ./apps/control -run '^(TestW11Qualification|TestW11FrozenDeclarationImport|TestLocalPrincipalCredentialAdministration|TestReviewerW11LocalCredentialBoundary)' -count=1 -v
```

只运行这些明确筛选的公开夹具用例，不扩大到 native/live 测试。所有正式审查文件由 `SHA256SUMS.txt` 绑定，产品源码列表及 hash 见 `source-binding.json`。
