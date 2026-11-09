# BR8 实际审查 bundle 构造指南

这是只读配方。v4 Source 仍需非作者审查接受；本包没有运行正式审查、Root stage、dispatcher、Native、Go、SQL、TP 或模型。全部旧成功控制与四组 Native、六份 Mode 均未重放。

实际输入恰好七键，schema 固定为 `researchos.w09-br6-formal-actual-review-input.v1`。Attach 的 `review-input.template.json` 与 v4 字段一致；模板中的 null 仍是 OPEN，不能当作真实结果。它关于 v3 自引用的提示属于历史问题，v4 已准备修订但不能据此自签接受。

| 字段 | Root 必须提供的真实值 |
|---|---|
| context_ref | 最后 assemble result.context_ref；repository-relative POSIX 两键 path/sha256。不是 seed、result_ref 或绝对三键引用。 |
| consumer_result_ref | 实际 consume result.json 的绝对 path/sha256/bytes；六条 current-CM40 route、实际回执和全部 OwnedJob 关闭证据。 |
| root_publication_refs | 精确四键 scope/owner/roles/actual_root_captures；前两者来自 assembly，roles 等于最终 context 的已登记 registry，captures 是非空真实来源引用数组。 |
| current4_refs | 审查入口实际 checkpoint/path_ownership/step_state/commands 四个绝对三键 pin，按此顺序；不是历史 archive，也不固定 CP392。 |
| native_mode_qualification_ref | 已合格 NF6 decision c47344f587ffc63fe28127d1313e25f1be5df67a3e2614b862c38d64c4b094ed/41628；原六 Mode 保持原 pin。 |
| resource_refs | 所有下述公开整文件的绝对三键引用，规范路径唯一、SHA/bytes 精确；不含 bundle 自身。 |
| schema | 固定上述 input schema。 |

Root 先完成 bundle 的最终字节，再在外部计算 input_ref，通过 `--input / --input-sha256 / --input-bytes` 传入。不要把这个 input_ref 放回 resource_refs。v4 单独验证并持有 input_ref，Guard 实际集合为 `[input_ref,*resource_refs]`；自身规范路径、别名或冲突 pin 均拒绝。

资源闭合从实际 assemble result.dependency_snapshot.files 出发，逐个取得真实 bytes 并核对 hash。这个 snapshot 故意排除 Canon，而且先于最后 context.json 落盘，不能独自当作完整 resource_refs。补入最后 context 文件三键 ref、consumer result 与六条进程 stdout/stderr、assembly Scope/owner/roles/真实捕获、实际 current4、NF6 decision、v4 basis、Main/API，以及冻结 K 包 execution.plan.json。

还须覆盖 Main 实际读取的全部依赖：version_vector 五个数组 spec_files/source_files/input_files/lock_files/tool_files；adapter/policy refs；当前 Source coverage 与 Native Source21；六条 registered_commands 的 dispatcher receipt/input_versions/stdout/stderr、Native report/tool-run/Mode；每份 Native 的两条原始流及全部 owned_export.members；Mode 的 independent review/host/junction witnesses；role provenance 的 raw origin、actual-audit 与原始三行副本；C19/A06 八份 GLOBAL 及 assertion raw/refusal refs；Main 所用固定工具文件及可信 router/closure/producer Source。

GLOBAL map 的插入顺序保持 run_receipt、version_manifest、command_receipt、assertion_results。每个 case 四份文件，总共八份；A06-02 必须保留真实 refusal refs。不能把八份汇总 PASS 替代六条真实 route。

`dependency_snapshot.audit_ranges` 是 offset/bytes/范围 SHA，保持其原始类型和 Main 专用范围复核。不能转成 Root 活动日志的整文件 pin，也不要持有或 hash 整个活动 audit。普通整文件资源仍走 SourceReadGuard；最终 Main Reader.read_hashes 中的每一个真实文件都必须在 authorized 中有同规范路径、同 SHA。owned raw 全目录 inventory 也必须未变，Reader.finish 和 Guard finally 关闭通过之后才可出版 review。

后续实际 verifier Python 的 TEMP/TMP 仍须使用已有受控父目录 `C:/Users/yqyyds/.researchos/w09-native-v5`；原 Mode 用 tempfile.gettempdir() 检查包含性。这不要求移动或重跑原 Native。

仍待 Root 提供：v4 非作者接受；六条真实 consumer 闭合结果；已登记角色与 assembly owner/Scope、真实来源；最终 context 与八份 GLOBAL；新 current4、完整资源清单、bundle pin 和全新审查输出目录。审查之后才产生 Backup 真实普通 FINAL、Root 捕获/index、issuance 和 owner 接受，它们不应成为尚未返回的审查入口前提。

精确 Source refs、函数行号、当前固定 pins 与 OPEN 字段见同目录 bundle-guide.json；只读 Source Guard 已关闭，无 live Canon/audit 句柄。
