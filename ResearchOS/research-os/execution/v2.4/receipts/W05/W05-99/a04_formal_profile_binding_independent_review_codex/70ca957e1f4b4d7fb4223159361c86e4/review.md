# A04 三项 Source 修订独立复核

结论：**REQUEST_CHANGES**。两项可复现的 Source 级缺口需要同一轮修订；既有四个缺失 decoder、六个 selector 的无条件 OPEN 仍在，没有端到端验收绕过、Main 采用或新的 Root grant。

审查者 codex:/root/command_queue_impl；作者 codex:/root/f08_whole_scope_review。本轮只写独立审查目录，未改被审 Source、Main、旧 seal 或 canonical。

## 确证问题

### BIND-R01（P2）：完整原始响应的比较未保留 JSON 类型

文件 formal_profile_w05.binding.v3.proposed.py:715，函数 verify_refusal。

新链条已经把 Root issuance 的 scope refs、scope、invocation、response 和 terminal stdout 的主要身份串起；单独更换 evidence run/task/lane/condition/selected scope 会被拒绝。但最后用 Python dict 相等比较完整 original response。独立数据中，原始 response 的 details.exit_detail 为整数 1，terminal stdout 同一位置改为 true，guard 仍接受；改成 1.0 也接受。1 与 true 不是同一 JSON 值，不能称为完整原始响应逐值绑定。

独立反例：independent-controls.v2.json 的 NEGATIVE_response_bool_integer_alias、NEGATIVE_response_float_integer_alias。完整上下文、各原始对象和真实计算的合成 ref SHA 均保留；未借用作者 fixture、未调用 producer。

修订要求：完整对象比较使用递归类型严格的 JSON 值比较，或经过严格 JSON 解析后的确定性编码比较；明确拒绝 bool/int 等类型别名。该比较应覆盖终端 response 与原件，以及新 scope/identity 链中声称逐值相等的对象。保留 v3 的全部身份字段和原有拒绝门，不要求变更任何真实 Root authority。

### BIND-R02（P2）：允许取同一 Task 的非当前 Run 作为当前原件

文件 formal_profile_w05.binding.v3.proposed.py:533-548、:934-937；相关 verify_live_originals:637-652。

真实 Run 表名、NULL hash、完整公共 schema 与 SQL/body revision 已修复；Run.task_id 必须匹配 Task 身份。然而 Task.active_run_id 明确指向 foreign-current-run 时，reader row 检查仍接受，而选中的 Run 仍可是该 Task 的另一次 SETTLED 执行。独立组合反例保留完整有效 Task/Run/Artifact、正确 typed RUN_STATE、终态 JSONL 与合成 Root/Job 原件，只将 Task.active_run_id 改为另一个非空 Run；verify_live_originals 的 A04-01 guard 仍返回成功。

独立反例：independent-controls.v2.json 的 COMPOSITE_TASK_ACTIVE_RUN_foreign；正对照 COMPOSITE_TASK_ACTIVE_RUN_current。组合测试显式把 _database 替换为已通过 schema 的合成 row 对象，因此证明的是 guard 缺少关联检查；没有打开数据库或执行 SQL，也不声称真实运行成功。

实际生产语义：已 pin 的 internal/domain/runtime.go:276 在 report 时要求 Task.active_run_id 等于报告 Run；:279-287 设 Task.status=EXECUTION_REPORTED 并保存 output_artifact_ids，未清空 active_run_id。:59 在 Run claim 时设置当前指针。该证据足以确认本例中的“另一个非空 active Run”冲突。**不建议对所有终态强制 active_run_id 非空。** 若合法后续路径可清空指针，应该由原始终态/lease/版本链说明；最小修订至少拒绝非空且不同的 active_run_id，不能把已清空与指向其他 Run 混为同一种情况。本轮未扩大为所有生命周期证明。

## 原三项修订的处置

- A04-REV-R02-IDENTITY：主要身份链已收紧；scope 未由 Root 原始输出列出、scope/invocation/response 异域或终端身份不同的独立反例均拒绝。完整值比较仍有 BIND-R01，继续 REQUEST_CHANGES。
- A04-REV-R03-DB-SCHEMA：实际 kind=Run、Task/Run SQL content_hash=NULL、完整公共 body、严格 revision，以及 Artifact 的 sha256: 前缀、SQL/body hash 同一和当前 run 检查已通过独立纯数据正反例。跨实体当前关联还须处理 BIND-R02。没有执行完整 _database 或任何 SQL。
- A04-REV-R03-JSONL-SCHEMA：此 Source 子项通过有限独立复核。全部 14 个公开 event kinds 的完整 typed 正样本、十个必需字段逐项缺失、unknown kind、错误 payload、bool/zero sequence、重复 event id、异域 Run 检查符合预期。它不构成实际 LIVE JSONL 或完整 CLI reader 资格。

## 封存与静态核验

新 manifest 的 30 成员、旧 manifest 的 23 成员、9 个公共源码 pin 全部核对。5 个 source 的 before/after 全字节逆向恢复独立核对。profile 仅 _database/_jsonl/verify_refusal 三个旧函数变化，新增四个 helper；原冻结字面量常量不变，仅新增 PUBLIC_SCHEMAS；runtime_w05_live 恰好两次 profile SHA 替换，其余三源字节完全相同。

从三份完整公共 schema 独立遍历五个根，得到恰好 55 个定义；只删除六处 description，引用重写后的全量验证内容与嵌入闭包、作者 projection 均相同，没有未处理关键字被丢弃。未运行作者构造/测试/封存脚本。

作者首轮 78/79 与 v2 79/79 原件都保留；独立比较 fixture 唯一数据差异是 /Task/stage 从 IMPLEMENTATION 改成 delivery，脚本另只换 v2 输出文件名。作者控制结果仅作为可核查的历史，不充当本审查的独立证据。

本审查自行构造第一轮 72 项：四个正样本的生成器漏了 allOf 所要求的字段，属于审查 fixture 问题，原件不覆盖。新 v2 补齐该生成器并增加两个显式 DB-stub 组合检查，共 74 项，70 项符合预期，4 项“应拒绝却接受”对应上述两个问题。四种事件正样本修正后均通过。两个版本、完整输入及每条异常均保留。

静态核对 verify_capture_bundle 最后一条仍是无条件 OPEN；六个 selector 为 A04/W05-G01/W05-G02/W05-H08/W05-P01/W05-U02。recovery/H08/P01/U02 四语义 decoder 仍无条件 OPEN，新的 Root 负向 v3 producer 未实施。不能批准 Main、grant、runtime qualification、source acceptance 或 formal count 增量。

## 工具原件和边界

本轮新实际工具 origin f05575 已由 Root 计为 674：只读 rg 第二段无匹配，outer exit=1，Python/native=NULL；完整输入、完整输出和终态元数据保留于 failure.origin.f05575.json。旧 668 不重计，Root 673 不属于本审查。其余审查 Python 原始 native bridge 为 0；这些是元数据/纯数据审查退出，不能替代产品 native 退出。

SQL、Go、CLI、SDK、model、native 产品、Git、CAS、网络、候选模块 import 均为 0。没有重跑作者 controls，没有读取 Root 当前桌面进程支路。审查结束，交 Root 决定让原作者一次性修复这两项 Source 问题。

