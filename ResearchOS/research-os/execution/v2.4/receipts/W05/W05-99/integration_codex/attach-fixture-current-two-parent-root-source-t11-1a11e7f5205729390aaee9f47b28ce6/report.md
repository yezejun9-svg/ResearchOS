# T11 two-parent Root caller Source

状态：SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL。作者无接受权，formal_acceptance=false。

该包交付新的隔离准备脚本、composition choice 与定向驱动。未创建未来的隔离目录、worktree、运行 scratch；没有运行 Git、Go、SQL、native child 或 model，也没有改 Main/canonical/旧 Source。

组合完整保留旧四组件 ATT3、Q5、LEG2、EXPIRED 及 base49；最后添加已独立 Source 接受的 AF，仅覆盖 internal/domain/client_protocol_attach_contract_windows_test.go。总计 58 个 Source 成员。完整 Source/independent handoff、manifest 及 manifest members 均精确校验。AF 只改 unowned 与 claimed-epoch fixture，原语义和 production 不变。

执行选择器只有 TestClientAttachSettledAcquisitionCompletesAndReplays 与 TestClientAttachPreservesStaleAndBindingGates，Go 会运行它们的所有子用例。旧定向范围 54 父测试中其余 52 的 Source 保留，但本次不执行、不声称新接受。全体 58 文件内 132 个声明另行列出，不能冒充定向执行范围。initial-draft 保留首次静态生成结果，refine-source-scope.py 修正范围标注后，直接运行最终驱动中的纯 Source composition 代码块确认 58/54/2/52；两个实际入口均未运行。

隔离准备的命令参数为 CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION。定向驱动为 CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES。精确路径见 execution-contract.json。Root 运行前应对 HDF/MF 中实际入口和 choice 做精确 pin 核对，并传入当时有效 checkpoint；不固定 revision 362 或 363。隔离实际完成之后才能取其 isolation.ready 精确 pin 运行定向驱动。两入口输出都指向新路径，且要求目录尚不存在。

旧五个 owned Git jobs、HEAD、project identity、13 dirty/11 deleted 与 staged-empty 判据保留。定向驱动保留 gofmt、tagged compiler list、完整编译输入和 embed 清单、go test -c、official test2json、owned process cleanup、five guards finally，以及 Main/canonical 前后字节核验。其 safety functions AST 与旧版完全一致；两脚本的变更均可按 source-replacements.json 逆向逐项恢复原文。

验证仅有 Python AST、字节逆变换、只读精确输入 hash、最终纯 Source composition 预检；这些不是 Go PASS。ordinary history20、full Release/program rehearsal authority 保持 BLOCKED；共享 recovery observation fence 的既有阻塞没有由本包解决。

本任务未发生新的实际失败。两次 Source Python 均 exit 0，native exit 为 null。初次声明范围修正保留前后草稿与原工具 IO，不增加或清零 Root 的失败计数。

