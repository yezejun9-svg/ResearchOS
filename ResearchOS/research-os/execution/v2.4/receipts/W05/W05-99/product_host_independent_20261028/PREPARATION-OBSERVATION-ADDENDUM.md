# 准备回执的观察补充

本文件补充 `PREPARATION-SEAL.json`，不改既有源码观察或失败结果。

`FROZEN-REVIEW-MATRIX.md` 实际含 30 个 source/mock/build 项（S01–S05、H01–H11、C01–C05、X01–X05、B01–B04）和 6 个后续 native 项（N01–N06）。先前给实现者的即时消息写成 29 项是计数笔误；`PREP-STATUS.json` 已含完整 36 个 ID。

`prep-probes.cjs` 含严格限制到本 receipt 的 fixture 清理逻辑，Node 返回 0；但事后实读仍发现 `fixture-GeXezr/`。因此 `PREPARATION-REVIEW.md` 中“已删除”的表述不能作为清理证据。该目录已被第一版 seal 收录为复现输入，现明确保留为证据，不重复发起删除，也不声称环境已清理干净。没有观察到工具明确拒绝清理，残留原因未诊断；无需因此扩大到产品/native操作。

新增的 native driver 预审是 Root 要求的只读附加工作；其输入与结论单独记录，不改变 CP558 source acceptance=false 或 native_runs=0。
