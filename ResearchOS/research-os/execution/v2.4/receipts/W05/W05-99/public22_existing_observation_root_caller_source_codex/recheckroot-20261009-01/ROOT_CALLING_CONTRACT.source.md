# 原 1025 工件的独立只读 Root caller

本包是待非作者审查的 Source，不是 Root scope 或执行授权。原 case request 保持 `df1c909f1675fec2a44ab8dc9285147c181bcfdf629f127305d2f529e1c3a48f` / 241 bytes；原 1025 保持 `FAILED_RETAINED`。新的 Root envelope、scope、owner、worker、lease 和 review receipt 使用独立命名空间。

接口只有 `build`、`check`、`activate`、`readonly-run`。必须使用锁定 Python：`-I -S -B -X utf8`。每个命令依次传入 mode、输入 ref 的绝对 path、sha256、bytes；activate 再传入 activation witness 的三个 ref 字段。

1. Root 在两份独立 Source review 后生成 registration request。leaf v3 和本 caller 的 reviewer 必须真实向同一个固定 Root parent 交付。Root 原始日志中的 `/root/task` 精确对应 canonical actor `codex:/root/task`。审计要求原始 header / metadata / message 三行、相邻 ordinal、同 timestamp、client_authored=false、原日志 offsets / lengths / hashes。交付正文必须包含完整的 HDF/MF/decision ref JSON 对象；仅 SHA 文本不合格。
2. Root 重新读取当前四份 Canon、当前 case request 和新 Source decision，输出完整 ref JSON 并封存原始工具三行。`exec` 与 `functions.exec` 等 qualified 名称均可；原始 call_id 必须与 output 相配。使用这个 postreview live audit 绑定 registration request。revision 由真实四文件及 expected-revision CAS 提供，允许在 Main23 登记后重基，未固定 372。
3. `build` 在新 `integration_codex/public22-recheck-registration-<recheck_id>` 创建 scope、owner、worker、facts 和四份逐字节 before archive、两个 proposed after。scope → owner → worker → facts 为无环引用，Root envelope 不替换原 case request。`check` 重建并验证相同投影；原失败计数、其他 worker/owner 和 SS/CM 保持不变。
4. Root 工具输出 facts 和四个 current before refs 的完整 JSON，封存真实三行 audit 后发行 activation witness。`activate` 复用已审查 TP；SourceReadGuard 显式排除 CP/OW，TP 独占期间的 callback 只比较传入对象并作纯投影，不重新读 Canon 或打开第二个 guard。失败保留 TP 原始 partial journal，无自动 inverse 或重试。
5. Root 完成登记后捕获 activation result、新 scope 和当前四文件的实际工具三行，发行独立 actual request，再调用 `readonly-run`。运行前验证 committed TP journal、当前 owner/worker/lease、Source、runtime 和原始工件。SourceReadGuard 在 leaf 首次读之前持有完整资源，并持续到两次只读数据库观测、最终 pins 复核与新 observation receipt 发布；lease/registration 在前后重核。

未来 Source decision 的精确字段在 JSON 合同中。leaf review 为 `researchos.public22-leaf-v3-independent-source-decision.v1 / ACCEPTED_SOURCE_ONLY`；本 caller review 为 `researchos.public22-existing-root-independent-source-decision.v1 / ACCEPTED_SOURCE_ONLY`。review 必须绑定新的 HDF/MF、caller、inputs、calling contract、补全后的 runtime-resources manifest，并明确 readonly_only=true、execution_grant=false、formal_acceptance=false、original1025_result=FAILED_RETAINED。

`source-inputs.json` 固定九份原始 evidence，原 Root assignment/三行 host capture、原 caller returned-state/case.closed、四个 Native before/result/stdout/stderr、六个 baseline 文件与 readonly 属性，另包含完整 leaf Source 和依赖。文件读取不触碰 `private/owner.json` 或 recovery key；它们只作为历史 argv 中的路径进行比较。原 console 已截断，保留完整实际返回的工具 IO及持久化记录，不能声称 console 完整。

runtime 只使用现有 `runtime_resource_paths()` 枚举、SourceReadGuard 和 TP，没有新增 WinJob 实现。先导入 sqlite3/_sqlite3，再冻结并由非作者审查 Python/SQLite/loaded-module 清单。初始清单遗漏 SourceReadGuard/TP 两个显式模块，原 1043 因严格 subset gate 拒绝；初始清单和完整失败 IO保留。`runtime-resources.complete.json` 明确补入两者，未放宽 gate；实际锁定 Python 的后续 Source 控制通过。Source 控制没有 SQL 查询。

实际只读 leaf 使用 `ro,immutable,query_only` 验证原有 83 张表、受约束 restore trigger 和 credential revocation 变化。Caller 仅调用 `recheck_existing_public22`，不调用 `run_registered_case`、Go 或任何产品子进程。leaf 返回必须保持原 1025 失败且 new_native_children=0。新结果写入 `integration_codex/public22-recheck-observation-<recheck_id>`，等待非作者实际复核，不能自行决定 FormalCaseAccepted。

原始异常与 guard/receipt 二级错误分别保留；无法发布的新回执内容仍完整打印，未知子进程 exit 保持 null。没有自动重试、恢复、删除、旧 case 写入或私钥读取。lease 必须有时区、32hex ID、最长一小时，并在实际入口仍有效。
