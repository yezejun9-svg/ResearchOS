# Read-lane cbe5404 独立审查

**REQUEST_CHANGES — 1 个 P2 Source 缺陷。** 候选解决了展示轮询使资格读错误失效的问题，但把有副作用的方法也赋予了展示读的并发豁免。作者的覆盖矩阵及全部通过日志不能覆盖此反例。

## R1 / P2：非只读操作不再使旧资格 scope 失效

位置：`apps/desktop/main/lib/ipc.js:102,155,160`。`write` 只包括 `v2.WRITE_METHODS`、host.configure 与获取写权限的 attach；`presentationRead = !write && !authorityRead` 因而把 provider.probe、workspace.register 归为展示读。这些方法不递增 writeSequences，也不建立 write barrier。登记范围要求显式限定只读类别，不能以不在 WRITE_METHODS 中证明无副作用。

独立复现使用冻结候选的真实 Main prepareQualificationScope/Proxy、唯一实际 createTransport 与 bound validator，command ID 各自唯一：挂住资格 host.status → 排入 provider.probe（allow_network=true）或 workspace.register → 释放 status。两次 Main 均成功返回资格 scope，write sequence=0、无 pending barrier。随后两个请求均经实际 validator 到达公共 fixture HTTP，并得到有效 COMPLETED；不是 schema 拒绝或未发送请求。生产中的 provider.probe 可以发出模型探测，workspace.register 可以改变授权工作区，二者均不应获得本次专门为展示轮询增加的豁免。该证明没有执行真实模型或工作区操作。

原始证据：`supplemental-cases.json` 的两个 `non-read` 条目、`supplemental.stdout.raw` 的两条失败断言；provider.probe 原请求/响应位于 `supplemental-raw/47fa441f-0559-450c-9cfe-a1510bdd521a/`，workspace.register 位于 `supplemental-raw/8d84f122-82a5-4236-b876-cd032fdc6955/`。每组有 3 个 HTTP 请求、6 个实际 validator 子进程，副作用方法的 HTTP/response 是序号 2。

修复建议：单独定义明确的展示读取集合/按 payload 判断；对其他有副作用操作保留资格上下文的操作代次或相应 pending 约束。不要为修这个分类把无 session 的创建/注册路径强行套用 session writer/CAS 要求。补验有效 provider.probe/workspace.register，以及相关创建操作与 Main prepare 的交错；保留原 write/ACK/replay/possiblySent 语义。需冻结修正版源码、重新生成完整输入 digest 与 bound validator。

## 本轮独立验证

- 冻结 commit `cbe5404367e2ea1f00e1ea4552d59d5d0d8eedf9`、tree `5f0bde58cfe7a4dff5eb1d8d768ce406043a3ab6`，相对 C381 为 exact3；tracked 工作树干净。3 文件当前字节、HEAD blob、build inputs、包内模块清单匹配；6444 构建输入全部重算无漂移。
- 独立重跑作者资格定向用例 21/21、管理边界 11/11 通过；独立补测 11 例中 9 通过、2 失败，共 43 例，41 通过、2 失败，无 skip/cancel。作者全量 203/203 日志已读取并绑定，本轮没有将其写为独立重跑。
- 补测通过：真实 Main 的同方法展示先完成、单 transport 队列顺序、send/CANCEL ACK、ACK attach 后 events/status/get 与原字节 replay、Main malformed/REJECTED status、CANCEL STALE_REVISION；原 pending command 和原 command bytes 得以保留。
- AUTHORITY_READ 是本地 Symbol，只允许 session.get/host.status；registerV2 只传三参数。Main 仅两个调用点改动。原 Proxy generation、真实上下文/ABA、native currentHost、writer/model/expiry、CANCEL 和私有 consumed/pending 屏障未被删除。管理与 PID 变化测试使用公共 fixture/注入身份，不是本轮真实 Root 进程观测。

## 逆序证据与构建来源

正常 Main 在 main.js:34 只创建一个 validatedV2Transport，所有 v2Deps 共用它；http-wire.js:159–187 的 lane.tail 串行执行完整 REQUEST validator→HTTP→RESPONSE validator。因此，已经排入该单一实例的两个成功 HTTP 响应不能倒序完成。作者补测另建第二个 createTransport，属于额外 IPC 鲁棒性夹具，不能标记为生产单实例的实际逆序。独立补测通过 credential await 阶段确定性地让后起展示调用先完成，仍共用同一个 transport；这是生产异步调用顺序可能出现的窗口。R06 的实际串行完成与最新 ticket 拒绝旧请求也已独立验证。

实际 `go version -m` 表明 validator 为 `vcs.revision=c381cf0d…`、`vcs.modified=true`，不能改称构建于 cbe5404 clean。完整输入 digest `6cb88f51…`、3 个内容哈希与 cbe5404 blob 的相等性允许把现有构建作为该冻结源码字节的开发夹具证据；不会因此接受当前 Source，亦不会接受新正式组合包。修复 R1 后必须产生新的冻结输入/构建，Root 最终包仍需 fresh descriptor/components/source_snapshot，并诚实保留 Core_CB / UI_candidate / Mu8df 来源。

作者 `matrix.json` 的 PARTIAL 与追加 `matrix-02.json` 保留；后者的 20/20 只表示 20 个编号都有本地夹具，不能掩盖本轮发现的新交错缺陷。D 盘满导致的无有效退出状态日志仍是 INVALID，未用于通过判定。

全部独审产物位于 C 盘当前目录，无新 Git worktree、无 D 写入、无产品安装/真实 GUI/SQLite/模型/Source/Canon 修改。正式增量 0，parent acceptance=false。私有 stdout/verifier stderr/独立 numeric Wait 等未持久化证据仍 missing。
