# CP558 static-001 初审（非冻结候选）

结论：`CHANGES_REQUIRED_STATIC_ONLY`。输入是10:22:05Z复制的14文件快照，capture内无漂移，完整SHA见SNAPSHOT.json。作者此后继续修改；本报告不对后续r2作结论。本轮没有运行候选测试/编译/CLI/Electron/Core或读取原业务数据。稳定问题ID用于r2逐项复核，不清除r1历史。

| ID / 优先级 | 具体问题与可复核源码 | 修复判据 |
|---|---|---|
| PH01 / P1 | `apps/cli/main.go:35-43` 只排除version/help/doctor，其余一律ensureProductHost；`commands`实际是本地合同列表，未知verb和旧task路径也因此启动Electron。除产品行为错误外，当前scope允许的非host `commands`检查不能安全运行。 | 正向枚举真实host-bound操作与interactive；commands/help/version/doctor、未知verb和非host帮助路径不启动；保留旧task实际语义。测试应断言spawn计数，不能只测返回字符串。 |
| PH02 / P1 | `product_host_windows.go:212-252` 在Electron单例前写共享binding.tmp，两个首启会互判非空或O_EXCL失败。`:277-320,351-385` 将活Core但缺witness判FOREIGN并立即退出；Core main先发布discovery，Electron main437-446后写witness，这是合法首启中间态。 | 由单例赢家串行claim/发布STARTING→READY；只有可交叉核验的匹配STARTING宿主才有限等。没有来源证明的活Core仍拒绝，不能将所有缺witness改成重试。首启并发、GUI先/CLI先、半完成READY至少有确定性测试。 |
| PH03 / P1 | Go `productIdentity:89` 与JS `installationIdentity:45` 只含source_commit/版本/五个exe hash，不含canonical install_root或完整源/安装清单。witness/binding亦只存该ID；两个同二进制但不同安装位置可共享ID，CLI未验证实际Electron/Core镜像路径属于自己的root。 | ID明确绑定规范安装root和完整生产输入/清单digest；Go/JS/Python同构；witness与binding包含并核对同一root。真实OS进程路径与布局一致，不能用同hash或CoreBuildID代替安装身份。 |
| PH04 / P1 | JS load只验证LOCALAPPDATA为绝对路径，main34随即mkdir userData，可能在ResearchOS祖先junction下先写再拒绝data。Go只EvalSymlinks LOCALAPPDATA，prepareProductData仅Lstat data末级，binding/config/discovery/witness直接读写；ResearchOS父junction、绑定文件别名与config别名没有全面拒绝。 | 所有相关路径（含不存在末级的已有祖先）在第一次读写前检查reparse/alias/边界；建目录后复核实际路径；Go与JS一致。反例必须保证目标无副作用，不是写后再报错。 |
| PH05 / P1 | `productSnapshot:315-318` 只证明两个独立PID当前hash/creation匹配，没有证明Core实际父PID、同SID、实际image路径或Native pipe server属于该Core。`productNativeStatus:323-349` 又重读hostID、丢掉原witness期望值；缓存token有效时不触及Native3，仅HTTP host.status；调用后没有固定snapshot复核。 | 保留不可变expected snapshot，核实真实Core→Electron父链/SID/安装路径；绑定Native pipe server PID与Core实际identity，HTTP/native回复hostID/client/protocol匹配；前后复核同一snapshot。首用bootstrap只在需要时执行并核对回复，缓存token路径不可为测试而反复bootstrap撤销活凭据。 |
| PH06 / P2 | main78-81的before-quit调用productSafeExit不消费拒绝，但safeExit catch会重新throw；与close/tray行为不同。main454-462在Core已确认STOPPED后若witness退休失败，catch留宿主，下一次ownedCoreIdentity又因STOPPED永远失败，用户无法再正常退出。 | 所有入口消费并呈现同一退出结果；显式区分Core已停/元数据异常/仍未确认，不能对STOPPED反复发shutdown或困住仅剩Electron。保留异常见证，不谎称完全成功。busy/失败确认/元数据故障分别测试。 |
| PH07 / P2 | product main222-223仍继承RESEARCHOS_PROJECT_ID/SESSION_ID，510仍允许ROS_DESKTOP_LEGACY_WORKBENCH替换实际React；CLI启动会滤这些变量，但直接Desktop入口不会，两个入口行为不一致。 | 产品模式忽略/拒绝开发上下文和页面覆盖，使用实际绑定路径/用户存储；直接Desktop及CLI所产环境一致。Node/Electron启动前注入仍需由受控启动入口负责，JS事后检测不能证明未预加载。 |
| PH08 / P1（覆盖） | 当前Go仅2个测试、Node仅2个layout测试、Python仅2个builder纯函数测试；没有执行main的singleton/close/before-quit，没有实际ensureProductHost启动状态机，也没有Go/JS同构与真实native绑定反例。 | 将PH01–PH07及scope规定的首启、已有非空数据、身份/路径冲突、busy退出作为负向行为检查。先纯mock/temp，不用未授权native弥补；绿的6个测试不能接受本阶段。 |

PH01已紧急同步Root，作者确认停止构建并保留interruption，未运行安装CLI/Electron/Core（该句是作者报告，不是本审查独立进程观测）。Root报告r1已冻结并计划r2，本报告仍以SNAPSHOT.json实际字节为准；最终应读作者freeze和构建证据，核对delta后再签完整审查。

构建器当前可见正向实现：编译实际CLI/Core/verifier，调用原client-wire构建器，打包runtime/migrations/contracts，生成最终位置的verifier绝对绑定，记录Go与Mu编译输入before/after；这些仅是静态读到的代码行为，本轮没有构建验证，不提前认定产物正确。安装、升级、卸载、C57与formal仍不在本次通过范围。
