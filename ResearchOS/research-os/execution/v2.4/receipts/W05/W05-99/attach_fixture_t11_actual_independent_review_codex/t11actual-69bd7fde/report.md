# T11 actual 独立审查

结论：T11_TWO_PARENT_ACTUAL_COMPONENT_ACCEPTED_NO_FORMAL_AUTHORITY。本次两个指定父测试的实际组件证据接受；不代表 Main 已采用，不代表其他测试、迁移 Native 正向、Owner、九用例、原 trial 或正式产品验收通过。

主审查 6,165/6,165 项通过，另 5/5 项补充绑定检查通过。4,978 个已声明公开输入共 381,846,692 bytes 经本轮 SourceReadGuard 实读校验后全部关闭，没有复制输入大树。没有新增审查机械失败，也没有重跑 Git、Go、产品测试、native、SQL 或模型请求。

## 实际执行闭合

Root 稀疏隔离 invocation 为 chunk 27ca9b / session 24094 → chunk 14da82，outer/Python 0；目标验证为 chunk 972b48 / session 71603 → chunk 3623df，outer/Python 0。两个终态均有显式 ROOT_PYTHON_EXIT=0。原始回执中的每个 progress、ready、closed 引用均与实际文件 SHA/bytes 一致；Root 回执文件已逐字节复制保留。

六个 Git owned Job 与 format、compiler-list、compile、test2json 四个 owned Job，共十个实际退出均为 0。PID 和 64-bit FILETIME 使用 Python 整数核对，输出以十进制字符串保留；全部 assigned-before-resume、job idle、active process 0、primary exit confirmed、handles closed，无 timeout/termination/cleanup error。

最终测试的 owned primary 是固定官方 test2json.exe，PID 12840，FILETIME 134359901651185821；其 SHA-256 是 dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c。被运行的测试二进制为 77cdb4a8ef876da174e1646db4b50b2d39f224c19819d0316009dbc1ec02e986 / 42,542,080 bytes。二者均在 binary guard 中。没有为 test2json 的测试子进程补造独立 PID 或 FILETIME；它作为 Job 内后代受到管理。

## 完整事件与 Source 范围

真实官方 test2json JSONL 共 23 个事件：单 package start、5 次 test run、5 个 pass 终态和最终 package pass；每个 run 都有唯一终态，所有事件均属于同一 package 和两个精确选中的父测试，父子开始/结束顺序完整，时间顺序一致，stderr 为空。

- TestClientAttachSettledAcquisitionCompletesAndReplays：父测试及 unowned、expired-same-owner、other-client 三个子用例通过。
- TestClientAttachPreservesStaleAndBindingGates：父测试通过。

所以是 2 个父测试、3 个叶用例、5 PASS、0 FAIL、0 SKIP。不能把 5 个终态说成 5 个父测试。

实际 overlay 的 58 个 Source 与先前独立审查接受的组成逐项一致，补充检查验证该组成确属已接受 manifest。与当前 T9 的实际 formatted manifest 比较，只有 internal/domain/client_protocol_attach_contract_windows_test.go 改变，其余 57 个文件 SHA/bytes 完全相同。

原有 54 个候选父测试 Source 保留；本次只选中两个，其他 52 个没有执行或新接受。58 个 Source 内共有 132 个父测试声明，这不是本次执行数量。

## 编译输入与 guard

从实际 go list -test -deps -compiled 的完整 JSON 流独立重建，结果与 manifest 完全一致：

| 项目 | 数量 |
| --- | ---: |
| package 记录 | 352 |
| 唯一 build inputs | 3,731 |
| product inventory 文件 | 605 |
| compiler tools | 8 |
| embed 条目 | 39 |
| 去重后的完整 compiler guard 集合 | 3,923 |

所有 Go/Test/XTest/CompiledGo/C/汇编等字段及实际 EmbedFiles/TestEmbedFiles/XTestEmbedFiles 均纳入核对。编译命令明确使用 researchos_native_recovery_harness tag、-buildvcs=false、准确输出二进制；测试 selector 精确锚定两个父名。

隔离的 source/runtime 两层历史 guard 分别有 115/30 个成员；验证的 input/runtime/candidate/compiler/binary 五层分别有 951/29/59/3,923/2 个成员。七层均为真实 SourceReadGuard 观察，PASSED、closed、retained handles 0，无错误；本轮 guard 同样关闭。

## 保持的边界

实际稀疏检出使用 --no-checkout 后的新 worktree metadata，模式文件为真实 20 行 LF；反向 gitdir、metadata HEAD、命令级 sparse flags 和所需 toolchain 文件一致，巨大的 historical receipts/verifier 目录未检出。

隔离前 Git 实测为 13 个 tracked dirty paths，其中 11 个删除，staged 输出为空；这些原始字节与失败 894 的先前基线相同。Main HEAD 前后相同，受保护的 Main 文件与四个 canonical 文件在实际 guard 和本轮复核中均保持准确 pin。没有另跑 post-validation Git status，也不把隔离前观测冒称新增的事后 Git 观测。

checkpoint 始终绑定 CP363：9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25 / 4,223,052 bytes；正式验收仍为 0/42。Main_adopted=false，其他 52 父测试未被升级，ordinary history20/full release/program rehearsal authority 仍 BLOCKED。

失败 894 的原始 outer/Python 1、Git 128 与 ENOSPC 证据完整保留。更早 Q3 的 61 PASS/6 runtime FAIL，以及当前 T9 的 152 PASS/5 FAIL 也分别保持历史原状：当前 T9 的五个失败终态是 AF 三个及 transcript ordinary 叶/父两个。此次 AF 范围通过不表示 transcript ordinary 或其他未执行范围已修复，也不重判更早 runtime 历史。

global provider requests 与 original-trial provider requests 保持未知；本组件回执的零请求范围不外推到全局。未读取私钥或原 trial，未实施 Main/canonical 写入。审查完成后 STOP。

