# MXC availability Rev03：独立审查候选，未执行
本包仅修复 rev02 的两个输出证据问题。f13/Kernel/execute原文件及rev02所有bytes保持不变。原拓扑 f13 CLI → pinned Node → 单次pinned Codex sandbox → pinned cmd echo不变。官方12项argv、显式native环境、35秒soft/45秒f13hard/5秒cleanup、16进程/2048MiB、无模型/无setup/无fallback全部不变。

新增 bounded-capture.mjs，必须与wrapper一起加入外层f13 inputs；wrapper也固定核验其SHA。Root仍须先独立审查，再生成mxc.scope.json（state=ROOT_REVIEWED_EXACT_COMMAND）并将准确hash写入实际f13登记scope；模板保持PREPARATION_ONLY_NOT_AUTHORIZED，不能直接执行。

## 两项修复
1. 每流在spawn前创建prefix.bin及初始progress。首chunk开始，最多64KiB prefix同步write+fsync；progress记录durable_prefix_bytes、prefix hash、ingested bytes/hash、child_close=false。之后每个已接受chunk更新固定大小progress快照。每次先写progress.json.next、fsync，再rename覆盖；若硬停发生在rename前，Root可检查旧progress或完整.next，结合prefix实际长度，只把有证据的前缀当部分诊断。
2. 每流最多处理/hash 1MiB；跨界chunk只处理剩余额度，记录被丢弃tail的长度；达到限额立即pause对应pipe。之后排队callback不再计数/hash/写prefix。limit后progress明确UNKNOWN、paused、完整stream hash=null。保持await child.close，绝不kill/PID名操作。原f13仍唯一硬停止边界，Node暂停后可能无法close，外层deadline会收尾。

softtimeout立即同步保存两流已收/已处理/持久prefix/digest和live-state。spawn异步错误、同步throw和stream错误发生时写本地快照，保留有界原始message及原message hash；Native stderr/stdout仍以精确byte prefix保留。IO/fsync失败立即failclosed、pause并通知外层stderr；无法写入的磁盘不能保证新错误持久化，因此不得声称该失败时所有诊断已保存，只保留先前成功fsync证据和外层通知。不会因write失败误标成功。

只有stream end + child.close +无limit/IO/error才允许complete_stream_sha256；硬停前的hash始终标INGESTED_BYTES_ONLY，完整hash=null。即使存在完整echo，最终仍须Root f13 stop_proved/job active zero/无漂移确认，包装器不能自证membership或cleanup。

## 准备验证（无Native）
- Node --check只语法检查wrapper。
- capture-pure-check.mjs只使用文件IO、fake stream.pause和Node assert，不创建子进程、不导入wrapper、不调用Codex/cmd/SDK。
- 6项：首chunk/timeout在close前持久；17×64KiB+4KiB限额反例；oversize chunk只hash剩余额度；stream错误即落盘；fsync失败暂停且无durability假证；完整hash需EOF+close。
- PURE-CHECK.json和pure-capture-evidence-*为证据，不是实际MXC运行结果。初版全stream处理阈值问题已改为实际processed/hash字节上限；已交付给Node的跨界chunk仍可能包含被忽略尾部，不能宣称OS pipe从未缓冲额外字节。
- 固定argv/env函数与rev02源码对比；模板预算不变；rev02 manifest每项hash再次核对。

## Exact paths与结果边界
新scope_id=mxc_availability_20261105_d83a；Root外层attempt路径为原f13 runs下该id，内层创建mxc/cwd（fresh empty）及mxc/tmp。此刻attempt不存在、mxc.scope.json未生成、scope未登记。
子层环境仍是Native05必要字段：正常USERPROFILE/HOME/APPDATA/LOCALAPPDATA，SystemDrive由固定SystemRoot派生，owned TEMP/TMP，固定PATH；不复制API/proxy/NODE_OPTIONS/CODEX_HOME，不读取私有认证配置。CLI正常native config/cache副作用不宣称为零。无授权savedconfig/OS/setup变更。

结果仍只表示内置:workspace的MXC echo startup availability，不能证明ResearchOS root-deny/minimal-read/source-read profile的enforcement，不能标READY或增加formal/product计数；旧globalHarnessinvoke1及失败记录保留，不能模型重跑。
官方命令来源：https://learn.chatgpt.com/docs/windows/windows-sandbox （父线程及之前分析已核查）。

