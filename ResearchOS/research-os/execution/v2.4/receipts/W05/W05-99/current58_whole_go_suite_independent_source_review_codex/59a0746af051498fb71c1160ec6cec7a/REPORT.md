## Review Summary

**Verdict:** REQUEST CHANGES

745 个测试在六 lane 中各归属一次，58 个目录完整列出，含 31 个 build-only。提案保留 actual Go roster、SourceSigner、资格与正式接受为未完成。runner 的三个接口缺口需要先修，才能进入 Root literal 准备。

### Critical Issues

无。

### Important Issues

- **GO58-R01-DEADLINE-FAILURE-CLOSURE** — whole58_finite_runner.proposed.py:123、231、244、272。总期限仅启动前检查，child 仍得到完整单次时间；kill/wait、两次 join、最终文件 IO 未扣剩余时间。异常可绕过 aggregate report，未终结的非 daemon drainer 可继续阻止退出。修复：贯穿整阶段的 monotonic deadline、显式 cleanup/finalization/IO reserve、每次 min(per, remaining)、终结后再校验；try/finally 保存 first cause、secondary、原 raw 和真实 nullable exit，外层 Job 真正控制后代。近截止启动、继承 pipe、超限、kill/wait/IO 失败控制目前 NOT_RUN。
- **GO58-R02-W14-DIRECTORY-ABI** — runner:81、110。runtime.members 全部必须 regular file，W14_GO_TOOLCHAIN 却必须等其中一条 path。实际 runtime_check_windows_test.go:178、189 消费 toolchain_root 目录，runtime_check_windows.go:204、215 对目录递归形成 tree hash。真实目录通不过，go.exe 又不满足真实测试 ABI；省略会 SKIP。修复：单独的 typed directory/tree manifest，严格连接 root、完整成员和真实 executable/tree/build hash；Node/Mu 继续按文件 pin。合法目录、单 executable 替代、树漂移/别名/缺资源控制目前 NOT_RUN。
- **GO58-R03-ACTUAL-AUTHORITY-AND-CONTRACT** — runner:67、74、223。仅有 execution_authorized=true 和 11 个文件哈希，没有消费真实注册/grant/lease/current source/外层 meter 的语义；CONTRACT 也未按 scope pin，只核 58/745 数值。变动 import_arg/regex/选集可改变实际执行。修复：执行前真实 typed Root gate，或已审 Root wrapper 的精确绑定验证收据；冻结 runner/contract/MF、当前 source/CAS/lease、独审、grant、有限 argv/lane/test、环境及资源根、实际 Job/process/HTTP caps 和预算。所有未知必须 OPEN，运行授权不应依赖预先 source_acceptance，以免循环。

### Suggestions

Go JSON 应按 actual import path 核事件归属，拒绝重复 terminal、任何 fail/skip、缺损/外来事件；当前 dictionary 会覆盖重复 test terminal。为无 selected lane 的包标记 NOT_APPLICABLE，并记录计划/实际调用数；空 all() 可以表示选定支路无任务，但不能变成整包测试通过。现 report qualified=false 已保留，未声称全套 PASS。

### What's Done Well

745 ID/partition 完整且唯一，58 目录无重复，也无同目录重名测试。原 raw 使用 exclusive writes，-count=1 与 exact selectors 清晰，SKIP/timeout/overflow 阻断候选通过。19 future literals 为 NULL，SourceSigner consumer 仍为 NULL，model cost 保持 NULL，原失败和旧 false sinks 保留。

### Verification Story

16 个 frozen member/provenance refs 全字节核验零漂移，runner 与 generator Python AST 解析成功。20 个项目 init 正文实读并与 public catalog hash 对应，直接内容为注册 map；这不验证依赖全 init 或 top-level 初始化。383 个调用图达到 cap，其中 STATIC_NO_RESOURCE_SIGNAL_REVIEW 的 520 个测试里有 272 个 capped；不能证明 SDK/外部效应为零。

实际 Windows Go graph/list、编译、测试、运行时、外层 Job 与 HTTP/process 计量全部 NOT_RUN。未导入或执行候选，无 Go/Node/Git/model/HTTP/CAS/source/canonical 操作；本轮新工具失败 0，作者旧 origin 不重计，固定 43→575 不变。

Root 后续需先独立冻结真实 authority/资源/预算和 preflight scope；go test -list 会启动含测试的包的 init/TestMain，不属于只读 census。全部 local slices 授权时静态计划为 58 list +78 lane calls=136 primary Go calls；后代数仍待真实资源/预算证明。两真实模型测试仍 B01 HOLD，local slices 可以独立推进。

SourceSigner 的真实 consumer 尚未建立。合法后续入口是新注册 Root scope 内不可变 W05 owner receipt、不同身份的独立 verifier 与明确 schema/consumer；task_packet list/show/next、旧 false sinks 和 development 资格不构成签署。source_acceptance、whole58_test_suite_qualified、42 formal 接受增量均为 0。
