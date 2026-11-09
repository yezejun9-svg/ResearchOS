# CP362 独立一致性审查

结论：CP362 canonical 一致性接受，不授予产品接受权限。审查截止点为 ordinal 875；后续运行和 Source 失败属于下一检查点。

checkpoint 原始 SHA-256 为 84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b / 4195882。ownership rev168、step_state、commands rev39 的字节均未变化。canonical 仅在取得审查快照时短暂只读 guard，随即关闭；结束短读仍匹配。

从原子事务 0.before.json 取得确切 CP361，校验其 27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845 / 4147646。全部 845 条旧 failure_counters 的 JSON 对象原始字节片段与解析语义均与 CP362 前 845 条完全相等。833 的 Python NULL、独立观测与 inferred/source-reported=1 的区别保留；835 的精确 FILETIME decimal strings 134359787476336016 / 134359787460741284 与旧不精确值限定保留。

848–875 共 28 条新失败原件各登记一次，origin_ref / SHA / bytes / ordinal / origin_key 及退出值与 facts 对齐；新增 key 彼此唯一且与旧有 key 不冲突。历史记录存在更早 schema，不要求所有历史对象都含 origin_key。总登记数 873，highest875、next876 仅适用于截止点。859–867 精确对应 TRACE bundle indices 1–9 的九个 distinct calls，未按 stderr 行数增计。

原始退出字段与显式 marker 均保留：848/852/857 为 outer0/Python1；873 是工具调度错误，outer/Python/native 全 NULL；874 为 outer1/Python1/nativeNULL；875 为 outer1/Python/nativeNULL。868 的 held outer/Python/Go=1 与 broker source-reported1、independently-heldNULL 分开。871 原实际运行 outer/Python/native=1。

T8 编译和边界单元是限定接受。按原始 test2json 全量重新计数，28 leaf + 2 parents = 30 PASS、0 FAIL、0 SKIP，全部 8 个 owned invocation 收尾且未执行 native migration case。native868 仍失败；既有独立审查证据限定接受 whole 87-table SQL 检查、specific fixture release 和 Job 收尾，不把它签为 native positive。

T9 保持 152 PASS / 5 FAIL 的真实失败套件，限定 actual 审查接受不改变 suite 失败。6 child 的 10 PASS、68 events 及 individual child native PID/exit 未观测的限制保持。BR4 在本截止点只接受 Source；17 actual 标 NOT_RUN。Root 后续真实运行不属于 CP362 快照。

formal 0/42、historical parents 6/22。paid 原业务 OPEN，once-consumed、clock-expired，provider requests 保持 NULL；无 counter reset 或新的模型调用登记。原有 accepted lists/formal status 未升级。

CP362 manifest 实际 pin：9a3f261cddb28387b14b76a8f74ab4c3d31e82028ce72f92b15ecb328ffe8037 / 9573。manifest 生成后的 handoff、postwrite-original-tool-io.json 和 failure-origin.877.json 不倒算为旧 manifest 成员，后两者明确是截止后附加。

本次独立审查有三个已向 Root 领取编号的机械错误，原脚本、输入和结果均保留：880 错读 RESUME.md，outer0/Python/nativeNULL；883 对历史 schema 强取 origin_key，outer1/REVIEW_PYTHON_EXIT1/nativeNULL；884 把28 leaf误当总终态数，outer/Python0/nativeNULL，已用 count-correction.report.json 限定更正。attempt2/report.json 原 false finding 保留，final-review.json 才是最终结论。三者均不在 CP362 截止点内，待 Root 下一检查点登记。

本轮核对 1583 个 exact refs；所有自有 SourceGuard 均关闭、retained_handles=0。未改 Main/canonical/Source，未执行 Go、SQL、native 或模型请求。
