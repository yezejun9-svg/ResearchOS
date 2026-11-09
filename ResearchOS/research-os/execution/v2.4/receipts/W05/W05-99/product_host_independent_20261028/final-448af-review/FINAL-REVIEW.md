# 产品宿主独立审查

结论：**限定源码、构建和已列明夹具证据接受**。`source_build_accepted=true`，接受 commit `448af57c208a3f29199d10e0fa9d9c7311776fad`、tree `c4c9a19b5dce33a390620cb460e5b1c88d28cfc2`，对应 `product-layout-cp558-20261028-04`。本结论不代表真实产品宿主验收；`productCore_runs=0`、`productElectron_runs=0`、`formal_increment=0`。

当前产物 133 个文件及 Electron 75 项已逐项重算，安装身份、marker、client-wire 和最终 verifier 绑定通过。623 源码、Go 2325、Mu 2156、vendor 5083、public 4、client-wire 6453 的前后记录一致；覆盖 13605 个去重依赖，沿用已核对的未变记录，本轮重算 3 个变化输入。三个作者封存清单的 234 个唯一引用全部匹配。

| 证据 | 接受的事实与边界 |
|---|---|
| Node 产品夹具 | 修复后作者 8/8 PASS。实际运行于提交前修改态，测试及 helper 前后字节与最终 448af 相同；独立读取原始输出和绑定，不重复运行。 |
| Go 产品夹具 | 独立运行于 clean 9361，8 个有效顶层用例及一个子进程 helper 通过，前后源码及工具未变。最终改动只触及独立 Node 测试文件。 |
| Python builder | 独立 2/2 PASS，绑定 clean 9361；同上延用。 |
| Desktop main | 4 个独立 VM mock 通过；捕获的 main/helper 与最终源码一致。没有启动 Electron。 |
| CLI metadata | 原 selected-session status 失败已由 exact2 修复；作者 3 个顶层用例及 2 个 metadata 子项通过，实际运行字节等于最终源码。 |
| ModelStream | 5ee 上 7 个顶层用例、5 个 semantic 子项通过；独立重算 122 个文件，复核 11 个 TLS child 及只读 SQLite 的持久化、END、前缀哈希和隔离结果。后续 metadata 与测试专属改动不影响其调用路径，未声称在新提交重跑。 |
| 非宿主消费者 | build03 的 bundled Node loader、CLI version/help/commands 均 exit0，隔离用户根写入 0。build04 只核新产物完整性，不冒称在其上重跑。 |

原 Node 7/8 失败、`rmSync` 返回后 marker 仍存在的探针、215 项边界缺环境失败、早期 ModelStream 缺环境失败、原 status 失败全部保留。修复后的 Node 用例改用 `unlinkSync` 并先断言文件确实消失。W18 pagination 的 `CONTINUATION_HTTP_403` 仍未解决，本报告不把整个 CLI 或 HTTP/renderer 套件判为通过。

ModelStream 仅为本地 TLS、进程内 host/Native3 和开发 CLI 夹具：2 支 CLI 正常结束，9 支异常路径在验证 UNKNOWN/无 END 后由测试主动结束并等待。环境值是事后重建，没有完整历史 PID 链；零残留进程只是记录时刻的观察。

真实 CLI/GUI 竞争、非空历史重开、busy-close、installer/升级/回滚/卸载、C57、隔夜与 provider/业务，以及全部 22 父任务和 42 正式用例仍未接受。冻结审查矩阵是判据索引，不代表其中每行都已动态执行。

自动审批两次拒绝清理本审查的缓存及临时用户根，原因原文为 `blocked by policy`，命令未执行。第二次窄化尝试发生在 Root 停止指令送达前，此后没有再尝试；目录保留，详见 `focused-9361-review/TEMP-CLEANUP-DETAIL.json`。此项不改变上述源码与构建结论。

机器可读判定、证据哈希和未覆盖范围以同目录 `FINAL-REVIEW.json` 为准；其 SHA256 为 `be8584e90b2f49057d5253571701bf9ba502cffb6036505cf71a1ebd84a8fac2`。
