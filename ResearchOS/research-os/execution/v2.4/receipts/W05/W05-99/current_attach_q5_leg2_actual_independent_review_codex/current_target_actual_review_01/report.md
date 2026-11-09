# A9 限定 actual 独立复核

结论：接受本次限定运行的真实通过、真实失败原件与执行收尾事实；本次目标套件整体仍失败。没有签发产品或正式验收。

本轮逐字节核对 choice 8fee24f844dbb06581ea15b7f8665844ce4335fc93a0532d096433a810cea343 / 5610 和 validation.closed.json 1f5bbf0fd7ac125875059c4e6e516dfd7419548283ab330cc965b21af58f0593 / 39787。共核验 4749 个精确 SHA-256 + bytes 引用。ATT3、Q5、LEG2、EXPIRED 各自 Source HDF/MF 与独立复核 HDF/MF 引用均匹配；dict/list MF 均按实际结构遍历。

父层原始 JSONL 有 54 个父测试、157 个唯一测试，152 PASS / 5 FAIL / 0 SKIP；run 和 terminal 一一对应，包终态 FAIL。5 个失败终态归属 3 个父测试：

- ATT3 settled/unowned：格式化后 client_protocol_attach_contract_windows_test.go:100 的夹具 SQL 写入空 writer，触发 length(writer_client_id) >= 1 CHECK，未到 attach 业务行为。
- ATT3 stale/binding：同文件 :154 的 handlerCommand 调用报告 ATTACKER_CLAIMED_EPOCH。夹具为 claimed-epoch 期待 INVALID_REQUEST 响应，但实际在该调用处失败；后续 wrong-project 等分支不能由该父用例的失败运行宣称已执行或通过。
- LEG2 ordinary：client_session_bootstrap_test.go:95 报 MIGRATION_PREBACKUP_REQUIRED。matching historical20 program、backup、isolated restore 权威未补齐；Source HDF 原本即标 BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE。restore 子用例 PASS 不代表普通升级 PASS。

原 T6 原始 JSONL 独立重数为 25 个父测试、67 个唯一测试，61 PASS / 6 FAIL，包终态 FAIL；旧原件保持不变。本次原 25 个父测试全部 PASS，原 6 个 runtime 失败名字也全部 PASS。

6 组 nested child JSONL 行数依次为 9、9、17、8、8、17，唯一测试终态为 1、1、3、1、1、3，共 10 PASS。每组精确 leaf 集、run/terminal 基数、包起止、stdout/stderr bytes/hash、producer binary/tool pins、parent 名字、结果对象均闭合。父层嵌入的每一条 child JSON event 与独立 child JSONL 完全相等，没有遗漏或增添。全部属于 SYNTHETIC_LOOPBACK_TLS fixture。

child actual_native_child_pid / actual_native_child_exit 保持 null，不能推定成独立测得的 native PID/exit。可确认的是 6 个 frozen official test2json runner exit=0 和完整 JSONL PASS；后代进程收尾仅由 Root 同一独占 Job 的 idle/primary-exit/handles-closed 证据提供。

从原始 go list JSON 流重新提取并逐项比较：352 packages、3731 unique compiler inputs、39 embed records，与发布 inventory 精确一致。58 Source 均进入格式化及 compiler/product inventory；运行时 Node、Mu、Go、test2json 与原始 guard 输入均按 SHA-256 和 bytes 绑定。4 个 Root owned Jobs exit 为 0、0、0、1，所有 Job 均收尾；5 个原始 Source guards 全部关闭且无保留 handle。failure-origin.871 保留 outer=1、ROOT_PYTHON_EXIT=1、native=1。

本独立复核只进行文件读取与证据处理。未修改 Main、canonical 或 Source，未运行测试、模型请求或 native 迁移。CP361 只进行短读并记录当时 pin，没有持续持锁。执行本复核的 SourceReadGuard 及补充读取 guard 均已关闭。

不授予 full domain、formal42、parent22、native migration、original paid business 接受权限。旧 T6 失败、A9 失败及原始退出值均保留。Root 对 CP362 的发布及最终决定由 Root 独立处理。
