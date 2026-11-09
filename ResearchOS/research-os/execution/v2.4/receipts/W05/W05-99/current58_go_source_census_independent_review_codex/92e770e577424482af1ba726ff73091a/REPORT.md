# Current58 Go source census

当前 e2 源码的固定公开集为 639 文件，其中 559 Go；按目录 58 个、package 声明组 60 个、顶层 Test 共 745 个。本次逐文件核对当前 bytes、SHA256 和 Git blob SHA1 全部一致，没有 Go/Git/测试/模型执行。

旧 whole38 A–E 的 selector 在当前源码仍可匹配 39 / 4 / 1 / 1 / 73 个顶层 Test。名称存在不继承旧资格；完整有限列表在 census.json 和 old-batches.current-name-map.json。58 个组合修改路径里有 45 个 Go 文件，其测试文件含 129 个顶层 Test；这是源码关联数，不是充分覆盖证明。

源码共发现 14 处 skip、187 处环境读取，逐行条件和前文已记录。真实模型的明确入口是 TestW05Live 与 TestW06ContextContinuation。Node/Mu SDK 测试中的本地 TLS fixture 与外部模型调用必须分开登记；缺少环境有些 Fatal、有些 Skip，不能统一当通过。其余测试的 matrix 是有限局部调用扫描，未证明无信号的测试无副作用。

下一最小合同应按当前 package 的精确 Test 名冻结，不继续采用旧 ^Test 宽 selector 作为完成证据。先解析目标平台新 Go 图、每包新编译和全部子进程/fixture资源，再给每lane实数预算。真实模型、私有输入、历史工具与特殊 Windows 条件先 HOLD，分别授权；不能为得到全绿省略这些用例。候选合同的预算为 NULL，execution_authorized=false。

两种静态计数交叉核对：朴素行正则 747，多出的 TestPass/TestCancellation 是 native_go_windows_test.go 的 raw-string 生成 fixture，准确排除后 745。此清单不是 go-list 的平台选择结果，不含动态子叶、Example/Fuzz/Benchmark 完整资格。

现有 implementation package/contracts/execution.plan.json 仍仅构造路由；父任务和 42 正式门保持权威。源签收 sink 沿已有 signing-map 的明确缺口，不发明新的接受命令。CLI2 两叶、Desktop Go3/Node169 和旧 whole38 都不能相加成为 whole58 已通过。
