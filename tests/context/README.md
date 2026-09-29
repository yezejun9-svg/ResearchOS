# W04 上下文、影响和导入验证

`python ops/ci/context.py` 运行真实领域 HTTP handler 和持久 SQLite 夹具，逐条输出 `expected / actual / evidence`。支持 `RESEARCHOS_TASK_ID=W04`、`RESEARCHOS_CHECK_ID=W04-G01|W04-G02|W04-G03`、`RESEARCHOS_CASE_ID=C03|C04|A01`；未知或空交集返回非零，原始 stdout、stderr 和 FAIL 永久保留在 execution/receipts/W04/context。施工独立接受、GLOBAL_EVIDENCE_V1 和正式登记由根集成者及独立 Verifier 完成。

- C03：真实不可变 DecisionReceipt 谱系，独立 principal 校验 ChangeProposal 后原子应用；只有相关 Task/Artifact 失效，无关 Task 使用有效 bundle 产生消息回执；旧输出封存 STALE，旧 If-Match 为 412，状态冲突为 409。旧 CURRENT 版本的 Artifact 不能再次作为提案有效输入。
- C04：两个真实并发请求争用同一 ProjectState；保留候选，使用实际 integration Task/context 和密封候选值，独立检查后唯一决定生效。持久 inbox 乱序等待、event_id 去重、项目序号连续应用；每事件冻结 ProjectState 快照，投影不能回退。
- A01：在隔离临时目录复制完整冻结包，以外部固定的 manifest digest 校验全部文件。导入为独立 Profile、源 Artifact、Requirement、初始 DRAFT Goal；四种来源标签可区分。篡改、穿越、伪造授权、错误 manifest 均拒绝且计数不变；原包 validator 真运行，输出仅 SPECIFICATION_PACKAGE_ONLY / NOT_RUN。
- G03：新 Service 从持久 bundle 恢复并材料化只读输入和可写 candidates；Profile 的实际复制内容进入版本向量与自动影响链。事实改变、当前权限撤销及受限引用有正负控制。

本地导入入口（credential JSON 只从私有文件读取，token 不进入 argv/stdout）：

```powershell
control.exe -import-spec spec/v2.0 -manifest-sha256 'sha256:<pinned manifest digest>' -credential-file '<private owner credential file>'
```

W05 可直接使用：

```go
GetTaskContext(ctx context.Context, token, project, taskID string) (Object, error)
MaterializeTaskContext(ctx context.Context, token, project, taskID, newDirectory string) (Object, error)
```

材料化重新检查当前授权、最新任务 bundle 指针、版本向量和内容 hash；目录必须尚不存在。bundle.json、manifest.json、inputs/* 为只读，candidates/ 可写。ContextBundle 的 ProjectState revision 是观察水位，实际有效性由 Profile/Task 输入/策略版本决定；无关全局事件不会让有效输入失效。只携带该任务真正引用的当前决定；历史决定仍通过不可变 receipt 和 supersedes_id 追溯。

边界：模型决策信号/BOUNDED_AUTO 仍为 W11，Run 消息/语义审查等待 W05，Task/Goal 正式接受仍为 W06。recordAcceptance 这里只支持服务器重算冻结检查的 ChangeProposal 接受，不信任客户端 PASS/checks/executor 列表。受限内容材料化保持 W17 未绑定 503。事件消费者为持久顺序应用基础，不代表 W12 全生命周期完成。

预审回归：DecisionReceipt 的 subject_ref、rubric_ref、evidence_refs 和检查证据统一进入语义依赖遍历与影响链接，supersedes_id 只保留历史追溯。新增候选作者从持久 DecisionReceipt.recorded_by 与实际候选 Artifact 作者解析；客户端 executor 列表不构成独立性证明，未被本次晋升的历史作者不排除。A01 另注入真实未列入 manifest 的文件，验证整包拒绝且数据库不变。运行报告的 version_manifest 在执行前采样真实 HEAD、dirty 状态、环境及源码/规格/工具锁 hash。
