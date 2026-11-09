# 原 cli_contract 26 条失败只读诊断

结论：NO_SOURCE_READY_DIAGNOSTIC_ONLY。69 是原成功 check IDs，26 是失败 entries；原 harness exit1、status FAIL 不变。此次未执行任何产品或测试。

当前冻结 handler source 22752 的38个文件逐字节匹配 Git blobs。61项公开输入在本次扩展捕获后 before/after 无漂移。原 harness 两文件与原运行 SHA 相同；旧报告不变为当前通过。

|#|原失败ID|分类|原因与边界|
|---|---|---|---|
|1|W0503-INIT-ACCEPTS-CHINESE-AND-SPACE-PATH|FIXTURE_PRECONDITION|原 exit=3/reason=INIT_REQUIRES_HOST_PROJECT_BOOTSTRAP 正确；失败的是旧 workspace_ref 回显及 WORKSPACE_VALIDATED_AND_RECORDED 断言。生产此时仅路径校验、不落盘配置、不把绝对路径冒充授权引用。|
|2|W0503-CONFIG-SHOW-AFTER-REFUSALS-IS-UNCHANGED|FIXTURE_CHAIN|main 从删除配置开始；hostless init 不创建配置，随后 config show 实际 CONFIG_UNREADABLE/1。旧行把不存在的配置当已存在且应 unchanged。|
|3|W0503-GOAL-SENDS-GOAL-START|FIXTURE_PROTOCOL_AND_SCOPE|goal.start 确已上 wire，原 reply 缺 method，先 REPLY_IDENTITY_MISMATCH；同时此案没有 Session，旧预期 revision=7/epoch=2 与生产 project-level null 分支不符。|
|4|W0503-GO-ALIASES-GOAL-START|FIXTURE_PROTOCOL|go 请求 goal.start，但 generic reply 缺 method，身份验证提前拒绝；当前 detail 来自额外 go x 调用，不是闭包内同一次 check the citations 调用。|
|5|W0503-RESUME-SENDS-SESSION-ATTACH|FIXTURE_PROTOCOL_AND_PRODUCT_OPEN|attach 已送出，generic AttachResult 缺 method/真实snapshot，exit1，control未发生。修response后还存在本报告 P02 RESUME 恢复语义缺口。|
|6|W0503-RESUME-WITHOUT-EPOCH-IS-USAGE-ERROR|OBSOLETE_USAGE_EXPECTATION_AND_PRODUCT_OPEN|无writer-epoch现在走session.get→attach(true)接管，先被旧snapshot缺method拒绝；旧测试要求 MISSING_WRITER_EPOCH。detail另一次SID=s调用，不能替代闭包SID=sess-42原raw。|
|7|W0503-CANCEL-SENDS-SESSION-CONTROL|FIXTURE_PROTOCOL_AND_HELD_F08|cancel先真实读取session.get；旧generic snapshot缺method，退出1，未到session.control。不是已证明取消生产路径失效。|
|8|W0503-SLASH-STATUS-SENDS-HOST-STATUS|FIXTURE_STATE_AND_PROTOCOL|/status继承前案保存的Session，先session.get被旧reply拒绝，故没有host.status。|
|9|W0503-SLASH-GOAL-SENDS-GOAL-START|FIXTURE_STATE_AND_PROTOCOL|/goal继承Session，先session.get被旧reply拒绝，尚未goal.start。|
|10|W0503-SLASH-RESUME-SENDS-SESSION-ATTACH|FIXTURE_PROTOCOL_AND_PRODUCT_OPEN|/resume实际session.attach已发但reply缺method而code1，旧行要求code0。|
|11|W0503-SLASH-CANCEL-SENDS-SESSION-CONTROL|FIXTURE_STATE_AND_PROTOCOL|/cancel先session.get被旧reply拒绝，没有control；当前SID来自前案而非本案独立setup。|
|12|W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY|FIXTURE_PROTOCOL_AND_EXIT_EXPECTATION|旧REJECTED WRITER_BUSY reply缺method，实际先identity mismatch/1。补method仍不能把WRITER_BUSY资源/授权阻塞要求为1：生产映射3。|
|13|W0503-HOST-NOT-IMPLEMENTED-IS-NOT-EXIT-ZERO|FIXTURE_INVALID_STATUS_AND_PRODUCT_MAPPING_GAP|原顶层status NOT_IMPLEMENTED缺method而exit1；冻结CommandResponse仅三种status，不允许这个顶层状态。且当前先session.get，旧期望reason host.status不对应真实故障方法。|
|14|W0503-HOST-HTTP-500-IS-NOT-A-COMPLETION|OBSOLETE_REASON_EXPECTATION|原HTTP500已经exit1/HOST_HTTP_500；仅旧 UNKNOWN_STATUS 前缀不匹配，未发生completion。|
|15|W0503-NO-CREDENTIAL-REFUSES-WITHOUT-PRETENDING|FIXTURE_ENV_AND_RAW_GAP|原记录只给exit3/saw[]，没有实际reason。调用使用移除credential后的os.Environ，而非base()，丢本阶段discovery/config/client注入；因此不能证明失败确在CREDENTIAL_ABSENT。|
|16|W0503-STATUS-COMPLETES-AGAINST-THE-STRICT-HOST|FIXTURE_PROTOCOL|strict模式只验证请求，回复仍generic且缺method；session.get REPLY_IDENTITY_MISMATCH使status失败。|
|17|W0503-GOAL-CARRIES-ALL-CAS-FIELDS-ON-THE-WIRE|FIXTURE_PROTOCOL_AND_SCOPE|原最后envelope是失败的session.get，根本未goal.start；检查p.last CAS并不是目标方法的原证据。|
|18|W0503-IN-PROGRESS-IS-ACCEPTED-NOT-FAILED|FIXTURE_INVALID_STATUS_AND_ADMISSION|HTTP202原IN_PROGRESS缺method/result，先identity mismatch。即便修method，IN_PROGRESS不是冻结/v2合法status；持久接收也不授权立即RESUME控制或称完成。|
|19|W0503-EVERY-CLAIMED-OPERATION-LEG-WAS-OBSERVED-ON-THE-WIRE|AGGREGATE_DOWNSTREAM|wire map确缺session.control，前面attach/get皆被旧fixture截断。该汇总继承前项，不是第19个独立生产故障。|
|20|W0503-INIT-BOOTSTRAPS-PROJECT-WITH-HOST|FIXTURE_NATIVE_AUTHORITY|init实际NATIVE_WORKSPACE_CHOICE_FAILED/HOST_NATIVE_DISCOVERY_INCOMPLETE，project.bootstrap没有发出。probe只写url/pid/data_dir=x，无真实native Host identity/选择授权；旧预期authorized_workspace_ref=目录字符串亦不合法。|
|21|W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS|FIXTURE_PROTOCOL_AND_RUNTIME_EVIDENCE|run先session.get identity mismatch，未send/events。原endsWith send,events也不足证明真正Task结果/不可变模型工具产物。|
|22|W0503-INTERACTIVE-SENDS-LIST-CREATE-SEND|FIXTURE_STATE_AND_STREAM_SHAPE|前run把sess-probe保存到同config，interactive继承它，实际list→get而非create，再被旧reply拒绝。jsonOf取第一JSONL，不适用于现在多条事件/每turn summary；messages_read_from_stdin并非当前输出。|
|23|W0503-INTERACTIVE-ATTACHES-WHEN-A-SESSION-IS-GIVEN|FIXTURE_PROTOCOL_AND_PRODUCT_GAP|实际list→get在reply拒绝；另外完整静态interactive分支没有session.attach调用。修合法snapshot后仍不能保证该必需leg，不能删掉原attach断言。|
|24|W0503-INTERACTIVE-NEVER-SUBSTITUTES-THE-CREATED-SESSION|FIXTURE_PROTOCOL_AND_IDENTITY_GUARD|新建Session的generic reply缺method，exit1。伪list返回Session字段但未被采用，真正create尚未合法通过；无法证明整条不替换会话。|
|25|W0503-INTERRUPT-EXITS-130|OBSOLETE_STATUS_EXPECTATION|实际code130/exit_code130均成立，失败仅顶层status INTERRUPTED_READ_ONLY而旧期望INTERRUPTED。reason为READ_INTERRUPTED；这是只读status中断，不是活动Run取消证明。|
|26|W0503-TABLE-ROWS-ALL-PROVEN|AGGREGATE_DOWNSTREAM|tableRowsProven只收ok成功IDs；上述失败ID不在成功集合，逐row映射失败。因此本条是依赖汇总，不是另一未知业务故障。detail每参数最多600bytes，原表gap字符串已截断。|

修订建议分两层：先独立登记 main.go/v2verbs.go 的合法 typed fixture、native 前提、配置隔离、原JSONL/exit语义；另审 interactive attach、真实 RESUME、generic response验真/ACK admission 与合法 NOT_IMPLEMENTED 错误映射。不得通过只修改fixture隐藏产品缺口。

每行的精确 raw JSON pointer、源码行号、最小兼容提案和未验证项见 diagnostic_matrix.json。未重新执行原正式harness；作者身份不构成 handler接受。
