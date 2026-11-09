# A04 JSON identity 修订：窄独立复核

结论：**PASS_IN_SCOPE_SOURCE_ONLY_WITH_OPEN**。本轮范围内两个 P2 已解决；没有新的可执行授权或产品验收。

- **A04-BIND-R01 已解决。** formal_profile_w05.identity.v4.proposed.py:716 使用 :960 的 _same_json 递归比较完整原始 response。原先整数 1 与 true／1.0 的两项反例现在被拒绝；新增嵌套对象、数组中的类型别名和数组换序也拒绝。相同类型值、合法 NULL、对象键顺序不同仍能通过。
- **A04-BIND-R02 已解决。** :938 的 row guard 和 :639 的组合 guard 均调用 :980 的 _current_run。不同的非空 active_run_id 被拒绝；当前 Run 和合法 NULL 终态可通过。NULL 下的错误 Run revision、非 SETTLED 状态、children_stopped=false 仍被拒绝，没有把 NULL 当作自动通过。

独立检查 30/30 符合预期，其中四条直接使用上一轮由本审查者保存的完整反例输入，其余是窄范围新增或正对照。未运行作者 controls。组合检查明确使用 DB row stub；没有打开 SQLite、运行 SQL 或导入完整候选模块。这些检查证明 Source guard 行为，不证明真实产物或 Runtime 资格。

新 Source 的 24 个 manifest 成员与必要基准原件均已 pin。五个 source 的 before/after 完整字节逆向恢复吻合。profile 恰好改变 verify_refusal、_database_row、verify_live_originals 三个既有函数并新增 _same_json、_current_run；既有赋值与 55 定义闭包字节不变。runtime_w05_live 只有两次 profile SHA 更新，其余三源字节复制。_database、_jsonl、_event_schema、_schema_value、_root_pair、_grant_original 和 verify_capture_bundle 均未改变。本轮未重跑上一轮已完成的全 schema 验证。

作者 failure 677 原始输入、完整 NameError: IDS traceback、outer=1、metadata Python=1、native product=NULL 均保留，且与其 original-tool-io.json 中的结果一致。旧失败控制脚本未覆盖；v2 仅补 IDS 提取依赖并另存输出，26/26 是作者记录。本审查没有新增错误，也没有重复计数 677。

六个 selector 仍终止于无条件 OPEN；recovery/H08/P01/U02 四个语义 decoder 与 Root negative v3 producer 仍 OPEN。Main、canonical、旧 seal 未修改，SQL／Go／CLI／SDK／model／native 产品／Git／CAS 调用均为 0。有限 Source review PASS 不批准 Main adoption、Root grant、runtime qualification、source acceptance 或 formal count 增量。

本轮完成并停止，交 Root 收录独立复核原件。

