# Workspace epoch fixture independent Source review

Verdict: APPROVE — SOURCE_COMPONENT_ONLY_FOR_ROOT_FRESH_INTEGRATION.

结论：此次单test文件修订修正了epoch负例的fixture前置条件，可供Root全新集成及实际验证。旧epoch使用正值1，同Session实际映射的current epoch为2，使负例经过必要字段解码后能够进入STALE_WRITER_EPOCH检查。没有修改生产gate或弱化原断言；未执行Go或SQL，仍无目标实际PASS。

Source：D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c
HDF a017446bd2cf770b60696fa7c7a5e50e2fcd7f22c29179da0576bf975e0fa128 /9754 bytes
MF a0be6a8ded6b6ffa576a27e64c0bbc349905e95ae0fe110b61b379f4b03962ce /4032 bytes
candidate client_workspace_test.go 4fd0d44fcfbb3c86d095e7e163ca4f4a94e15093ab291d32c1cd7e02a3af64ae /13189 bytes

## Critical / Important Issues

本次Source范围未发现阻断问题。此结论不替代Root实际编译、目标执行和独立实际审查。

## Correctness and binding

- candidate client_workspace_test.go:64–80保持原WorkspaceBinding的principal/project/client/path/access与原事务，新增参数writerEpoch经正数校验后通过生产MapClientSession写入。同一ClientSession入库ID、project、revision=1、writerEpoch、writerClientID、workspace_ref、future lease、ProtocolV2，并非只改请求数字或事后SQL UPDATE epoch。
- T5 v24_sessions.go:78–111实际检查合法protocol、native session ref、positive revision/epoch和真实project，再同条INSERT记录上述字段。candidate192–197读回同sid六项，对currentepoch2/revision1/writer/project/workspace与未来有效租约均assert，Scan/parse错误直接失败。
- T5 client_protocol.go:1264–1268 revPtr(0)返回nil；原FULL2802实际输出MISSING_FIELD:writer_epoch。新target213使用oldEpoch1，不再生成nil；live session仍currentepoch2且revision1，与请求同writer/project，ClientService954–955比较不等时保留STALE_WRITER_EPOCH。workspace owner lease及binding检查仍在生产代码中保持。
- candidate201/220分别把content-conflict和正常import请求设为currentepoch2，使这两个正向前置条件与真实映射一致；old请求之外不错误复用epoch1。原成功revision2、后续相同命令回放语义未改。

## What's Done Well

独立核对原文件16个t断言调用、17 assertion_or_error_if、5个Test名及顺序全部保留；target原7调用/7 if完整保留。STALE_WRITER_EPOCH且port.calls不增、CONTENT_CONFLICT后无uploaded_content、COMPLETED且非replay/revision2、sealed exact bytes、identical replay且无extra IO、ARTIFACT outbox count1均保持原条件。

其他4个Test函数逐字节相同。共享clientWorkspaceFixtureFor只增加向epoch1 helper委派；新core把writerEpoch代入1后，与原core逐字节一致。默认现有fixture仍epoch1，没有扩大其他调用者语义。

Source明确这是SYNTHETIC_CURRENT_STATE_EPOCH_COMPARISON，不声称执行过公共writer handoff或证明历史切换来源。该范围符合Root窄fixture授权，未将current状态构造冒充产品历史验收。

## Verification Story

Tests reviewed: yes，先读target和sharedfixture差分，随后追MapClientSession、revPtr、ClientService epoch与workspace lease路径。固定Python独立词法核对16/17/5与7/7，sharedcore与其他Test函数字节比较均通过；28 input refs hash/bytes零漂移。原FULL2800–2804的五个真实事件与HDF逐行匹配，原失败没有被替换。
Build verified: no；Go AST/compiler/test/gofmt/native/SQL/model/provider/private/目标脚本执行均0。现有time/context/sql imports适用，无新增依赖。源码检查未发现明显语法冲突，不能据此宣称编译通过。
Security checked: static in scope。同principal/project/workspace/writer及lease gate保持，旧正epoch1负例在生产拒绝前不得到Workspace port；实际是否无IO仍由保留断言及Root执行证明。

建议Rootfresh integration后实际运行target与该文件默认fixture的相关测试，保存真实测试事件/exit并完成适用执行关闭。没有本reviewer主动执行或采纳Source。产品/native文件系统行为不由此synthetic port替代。

Main/T5/canonical/旧receipts均未编辑；原FULL1261 PASS /25 FAIL /4 SKIP FAILED不变。Root最新CP357及其他治理/Main dirty状态不由本review修改或重新宣称验证。无新机械失败，不取ordinal、不reset既有计数。独占review封存后STOP。

