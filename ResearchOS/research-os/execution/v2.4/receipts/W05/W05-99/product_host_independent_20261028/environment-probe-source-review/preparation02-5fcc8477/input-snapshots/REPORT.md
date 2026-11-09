# CP571 native folder 环境探针修订准备

状态：`PREPARED_ONLY`。Root 的 `continuation-cp571/Native-folder-environment-preparation02-scope.json` SHA256 为 `dff6c62374875c158d612c0cf50c8cc5472a70cff789b5b1b2ce8c5f274cdfa1`，明确只准准备与离线构建。`preparation01` 及旧 helper 保留不动；本修订写在 `preparation02`，可执行文件只在 `.local/native-folder-environment-cp570/revision02`。本轮 native/GUI/Core/产品/provider 启动均为 0，正式验收增量 0。

## E1：异常后持有 helper 句柄

`controller.py` 在每个 case 的 `Popen` 之前以独占写入 `hold-contract.json`，绑定当前 scope、controller PID、一次性 nonce 和 helper image；它不伪造尚未出现的 helper PID。`Popen` 返回后，`child` 是本函数持有的唯一真实句柄，后续身份探针、首个 `spawn.json`、握手、窗口枚举、IDCANCEL、结果读取和退出确认都在同一个 `try/except BaseException` 内。发生错误时，只有这个 `child` 进入 `unresolved_hold`。

`unresolved_hold` 参考已审过的 chooser 诊断保活模式：忽略可处理的 SIGINT/SIGBREAK/SIGTERM；所有首次回执写入、打印、release 读取、child 状态检查和 sleep 均置于不逃逸的 `while True` 保护内，错误写入再失败也只重试。`WAITING_FOR_ROOT` 重试写成功后，才允许核对严格形状、Root 身份、scope/controller/helper PID、nonce、等待时间之后的独立缺席确认；原始 helper handle 自身必须已退出，且 `ROOT-RELEASED` 回执写成功，循环才返回。没有 kill、terminate、自动重试或 90 秒进程自杀；仍活着或状态未知的 helper 不因 I/O 错误被释放。

`test_controller_mock.py` 的纯 mock 故障注入覆盖首个 postspawn 回执失败仍传递同一 child、`UNRESOLVED/WAITING` 初次写失败、内层错误记录失败、sleep 抛 `KeyboardInterrupt`/`OSError`、过期 nonce release 被拒、有效 Root release 且 helper 已退出后才返回。只用 FakeChild 和临时目录，不打开 UI。实际测试命令、stdout/stderr、exit=0 保存于 `mock-tests.*`。此测试证明上述代码路径的保活行为；它不能代替实际 native 运行。

## E2：离线构建来源

`build_offline.py` 在构建前核 CP571 scope、干净 worktree、单行源码变换、固定 Go 工具和 `go.mod`/`go.sum` SHA256，给 Go 子进程显式构造环境，设置 `GOTOOLCHAIN=local`、`GOPROXY=off`、`GOSUMDB=off`、`GOENV=off`、`GOWORK=off`、`GOFLAGS=-mod=readonly`、`CGO_ENABLED=0`。`build-command.json` 原样记录 argv、cwd、全部显式环境及输入大小/哈希；`go-version.*` 与 `build.*` 保存原始 stdout/stderr，`build-result.json` 保存 exit=0 和可执行文件哈希。源码 `native_folder_windows.go` 仍只把唯一 `package host` 改为 `package main`，其余字节一致；`main.go` 与上一版相同，只定义匹配的 ErrFrameShape、一次调用原 chooser，没有 COM/回调改写。

诊断 A 保留 Core 的七个环境键，B 仅增加当前核验的 `SystemDrive`；同一隔离 profile、中文路径、隐藏启动和 helper image。它们仍需 Root 另封最多 2 次的 run scope 后才能执行。`RUN-SCOPE-TEMPLATE.json` 保持 `native_execution_authorized=false`，仅供封卷参考。任何 A/B 结果都只是直接 helper 的环境诊断，不是产品 native 初始化正式通过。
