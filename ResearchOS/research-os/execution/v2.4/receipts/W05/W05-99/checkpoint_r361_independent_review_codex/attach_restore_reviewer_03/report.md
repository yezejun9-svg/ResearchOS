独立结论：CP361_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY。CP361 当前 checkpoint 的结构、累计失败记录和证据限定一致；CP360-EXIT-833-001 已在新 CP361 中修复。旧 CP360 拒绝结论、原始失败来源和原始输入输出继续保留。

833 的原始 ae5082 命令和输出没有 ROOT_PYTHON_EXIT 标记，只直接观察到 outer=1。当前记录 actual_python_exit=null，source_reported_previous_actual_python_exit=1 与 inferred_python_exit=1 分开保存；旧 diagnostic 全文保存在 previous_diagnostic_reported_by_CP360。原 failure-origin.833.json 未改，自报 Python1 仍仅作为历史来源。

835 的两个 FILETIME 从原始 invocation 使用 Python 整数读出，再转换为十进制字符串：harness=134359787460741284，rehearsal=134359787476336016。原来源中的 134359787460741280 和 134359787476336020 保持原样，当前记录明确标注原来源字段失真，并链接 evidence-accuracy.qualification.json。两个 native actual_exit=1 及各自 Job 关闭事实保留。审查没有重新执行 native。

独立比较 CP360 的事务前快照和当前 CP361：仅 revision、expected_previous_revision、updated_at、note、failure_counters、work_in_progress 六个顶层键发生变化。原 836 条累计记录全部保持原外层字段、origin key、evidence 引用、counted_once 和 reset 状态；其中 834 条原始 JSON 文本逐字节相同。只有 833、835 的 original_payload 增加或修正限定字段。新增 839 至 847 共 9 条原始失败各计一次，registered=845、highest=847、next=848；原计数不重置。9 条退出码分别与原始工具输出或未启动进程的事实独立核对，没有把 843 的成功诊断查询当作失败进程退出。

847 的第一次 writer 1118ee outer=1、ROOT_PYTHON_EXIT=1 与 KeyError 原件保留。受固定 SHA256 约束的事务模块在 transform 返回后才创建 journal 或写 canonical；失败 namespace 未发现 activate.transaction 目录。新 namespace 中 a599f8 prepare 和 40a83d writer 均为 outer=0、ROOT_PYTHON_EXIT=0，事务 proposed bytes 与当前 canonical 相同。失败与成功尝试相互独立。

主包 manifest 的 6 个成员全部核验。后写的 original-root-tool-io/original-tool-io.json 不在原 manifest 中，已单独 pin、读取和复制。事务 journal、旧失败 namespace 文件、qualification、反证、原 native invocation、4 份独立 review 与其全部 manifest 成员也已保护、校验和复制。Root source guard 的成功、失败、T8 两组 cleanup 均 closed=true、retained_handles_count=0、errors=[]。

4 份 review 的范围保持不变：CP360 仍为历史拒绝；ATT3 是 Source-only，fresh positive/shared TEXT 仍受阻；Legacy2 是 Source 修复通过，ordinary historical20 release/backup/restore/authorized-upgrade 仍受阻；TEMP 是 Source 通过且要求新 controller proof-key、环境资源和 Root 实测。没有将 Source 通过提升为编译、组件、native positive、Owner、业务或正式验收。

T8 的 5 个固定 Git invocation 均 actual_exit=0，primary exited、Job idle、handles closed，Source overlay=false；这里只复核已有回执。旧 T7 三个 native Job 的 failed/closed 结论完整保留。主库实时只读 Git 检查确认 HEAD=adc460c2138528f163f7fdab5e8d81dde157b7fb，13 个 tracked dirty（11 D + 2 M），index 为空；永久 UUID=aede0678-7308-43dc-b9f2-cfe3d90cfdfb。OW revision168、SS、commands revision39 的精确 SHA256/字节数不变。

6 个历史父任务、0 个 current formal、22/42 门禁均保持；Original trial once consumed/clock expired、业务与财务 OPEN、provider requests=null，没有新的 model trial 或整体完成声明。

本审查实际 Python 工具回执 6a5561 outer=0、ROOT_PYTHON_EXIT=0。685 个真实 SourceReadGuard 输入全部关闭，所有结束 pin 与开始 pin 相同；本轮无新机械错误。只写本独立 review namespace，Go/SQL/native/model 均未执行，Main/canonical/Source 包未写。产品 authority=NONE、formal_acceptance=false；交付后 STOP。

