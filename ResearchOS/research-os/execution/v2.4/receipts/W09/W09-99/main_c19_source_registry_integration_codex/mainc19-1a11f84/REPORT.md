# W09 C19 Main source and registry adoption — Source only

七个业务目标的采用源码已封存，尚未执行；formal delta = 0。

- 六个 Main 源码精确引用原 sealed bytes：三文件当前存在、三文件当前不存在；加 commands.json 共四个 existing、三个 absent。
- 原 v7 report 的 Source21 已逐项核对：六个待采用 pin 完全一致，其余十五个 Main 文件当前一致。
- commands.proposed.json 只改 test.research.fixture 与 test.retrieval 两条 entry 的 executable_tool/argv/allowed_env/selectors/tool_env。全文件字节 inverse 保留所有其他字段与 entry。
- 六环境变量仅加到 allowed_env；required_env 仍为空。router 不加 -I；W08 保留旧程序并通过 locked tool_env 注入 RESEARCHOS_GO；W09-01 原程序、streams 与 exit 转发保持。
- Root caller 只允许七个固定业务路径和本包 actual-adoption 下六个固定回执文件；不复制 producer/report，不改 CP/OW/SS，不跑 dispatcher/Go/Git/SQL/API/Model。
- 采用时持有全部七目标的 Windows shareMode=0 文件句柄，并持有防止父目录改名的目录句柄。正常失败在同句柄下回滚 existing 原字节，仅把本次 CREATE_NEW 的三个新文件标记 delete-on-close。
- durable intent 保存全部 before/after 字节。进程强杀或断电不宣称跨七文件崩溃原子性；异常回滚/cleanup 不完整必须交 Root 明确恢复，不自动重跑。
- Root 先登记独立审查通过的 scope 到后继 CP/OW，再封四文件 vector，最后生成独立 request 引用 scope/vector，避免哈希循环。Source caller 必须绑定 future CP > 366、OW > 170，以及真实的 Source 独审和组件实际独审。
- 组件实际独审使用真实已封 HDF schema researchos.w09-c19-v7-consumer-independent-actual-handoff.v1 / decision ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS；仍 NOT_CURRENT_NOT_REGISTERED。

验证：471 个纯源码/内存控制通过；包含两 entry 的完整 inverse、有限路由矩阵、旧分支 AST 保持、每个 partial-write/open/create/journal 失败点的内存回滚、外来 CAS/新文件不覆盖、回滚设备错误诚实返回、未来 Root/source-review/owner/vector 负例。140 个原输入保持不变，两个 SourceReadGuard 均闭合、零保留句柄。没有执行真实 Windows 七目标事务，也没有产品调用。

后续仍 OPEN：独立 Source 审查；Root 显式采用授权/新 owner-vector；真实七目标采用；新的双路 dispatcher 回执与 CURRENT 适用性；生产 W09 formal profile 及 W09 其余父任务门。现有 C19 组件 PASS 不自动接受 W09-99 或 A06。
