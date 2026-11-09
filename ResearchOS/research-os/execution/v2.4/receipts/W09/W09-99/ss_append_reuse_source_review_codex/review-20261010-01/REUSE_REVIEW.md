# SS 单行追加：现有函数复用审查

状态：SOURCE_REUSE_RECOMMENDATION_PENDING_ROOT_REVIEW。未调用原 register 模块、CLI、writer_lock 或 atomic_state；未读取或修改当前 SS、Main、Canon、密钥，未执行 Go/Native 或重跑测试。

只需复用 Refusal、need、sha、exclusive、path_in、atomic_state、writer_lock 七个定义，加 hashlib/os/uuid、Path/PureWindowsPath、contextmanager 和 BASE/SCOPE_DIR/STATE 三个常量。精确源码片段和行号见 dependency-contract.json 与 minimal-reuse-source.py.txt。writer_lock 的 @contextmanager 装饰器在1193行，不能只抄1194起而遗漏装饰器。片段只做AST语法解析，未执行。

## 锁路径与 Windows 语义

必须使用原路径：
execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/transition-writer.lock

原函数仅在文件不存在时用 xb 创建 b"0"；已有时沿用。它以 r+b 打开，检查首字节为 b"0"，seek(0)，用 msvcrt.LK_NBLCK 锁偏移0的一字节。busy直接抛异常，函数没有自动等待/重试。yield期间保留句柄，finally再seek(0)并LK_UNLCK，随后关闭句柄。它只检查首字节，不要求总长度恰好1；不要把实现描述成全文件格式校验。

这个锁串行化遵守同一锁文件的writer。它不锁SS文件本身，不能阻止不遵守协议的写入，也没有调用方身份认证。另建W09锁会失去与原writer的串行关系。不要删除/recreate锁文件。

## 原子替换边界

atomic_state 987–993本身不获取锁：创建并fsync临时payload→读取SS计算full SHA比较expected→os.replace→读取完整SS验证desired SHA。Root必须在同一writer_lock作用域内调用。out必须在SS同一volume、属于Root本次独占可写且link-free目录，repo须预先resolve到真实canonical根。路径检查复用path_in的穿越/drive/symlink/junction拒绝；这不代替Root身份和scope检查。

这是全文件哈希检查加cooperating writer lock，不是内核提供的hash条件替换。exclusive fsync了临时内容，但atomic_state没有目录fsync，因此不能宣称掉电持久化事务。保留归档和pending intent以供明确恢复。若有deny-delete的SS读句柄，调用方须先关闭，否则replace可能失败。

## 归档、追加与CAS

append-cas-sequence.json给出九阶段顺序。先取得共同锁，再读取并校验最新full SS raw SHA，严格JSON解析并确认W09-99尚不存在。构造desired.steps=old.steps+[new_row]；全部旧行嵌套内容、顺序与其他顶层字段保持，长度只增加1。不能调用硬编码W04-99替换的full_state_cas/apply/recover，也不能upsert已有W09行。

将原始SS bytes、desired bytes、new row bytes及绑定这些文件的pending intent用exclusive归档并核验后，才调用atomic_state。原始bytes归档保持逐字节；JSON重新序列化只能保证旧行语义相同，不能宣称旧文本格式不变。替换后重复完整bytes、行前缀和顶层字段检查，再执行另行授权的当前正式derive与依赖recheck。真实postderive结果、最终SS hash及接受判断必须来自未来实际调用，此处均留空。

## 替换后失败

postderive失败不会使已发生的SS写入消失。保持实际SS、原始/desired归档、pending intent、真实错误与结果，不自动调用recover或写回original。失败回执区分MATCHES_ORIGINAL、MATCHES_DESIRED、FOREIGN_HASH、UNREADABLE_UNKNOWN；不要因replace抛错而推定未改动。只有后续另行授权的显式Root恢复能在当前own-write full-hash CAS成立时进行。原W04 main1261–1269也明确禁止静默postcommit rollback。

这份审查只确认最小函数复用与新增append合同所需边界，不授予W09追加执行或独立接受。
