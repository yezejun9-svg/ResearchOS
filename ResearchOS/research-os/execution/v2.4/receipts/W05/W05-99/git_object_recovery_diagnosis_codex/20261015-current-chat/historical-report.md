# 历史 Git 对象恢复来源诊断

本轮只读对象库、索引、reflog、现有工作文件及项目 bundle，只在本诊断目录写回执/原字节候选。Main 4354 对象恢复由 Root 执行，本轮固定扣除该集合，避免将并发恢复计作新发现。

## 可恢复范围

- 原历史缺失集合：4924 项，固定来自 `orphan-index-check.json`。
- `historical-recovery-manifest-v2.json`：4702 项，含 1659 tree、2999 blob、44 commit；SHA-256 `548c372ff8fabd7efb5a44ff6f3c572c630cb3c697cf6589ffeaf00d062a2a89`。
- `historical-commit-extra2-manifest.json`：额外 2 commit；SHA-256 `0314cecff037bc3ed1f3f34bce9f36f1e74f807347458cd8f04f0b832642505e`。
- 因而已确认 4704 项原哈希来源，余 220 项进入限时 tree 重建。后续结果另列，不覆盖上述固定清单。

180 个本仓库已注册 linked worktree 的 index 被逐项只读核验，index SHA-256 前后变化 0、文件读取错误 0。tree 使用 index 的 mode/path/object id 生成 Git 原始二进制格式，仅以 SHA1 与原 missing oid 相等作为接受标准。blob 仅接受 existing file 原字节完全匹配，未用相似文本替代。

commit 使用实际 reflog 记录的 parent、committer、时间、subject，加已有 original commit 的 author/full message 及候选 tree oid 生成 bytes；仅精确 SHA1 匹配才保存。普通 commit 候选及 cherry-pick 候选均有记录。所有 46 个已知 missing commit 均已获得 exact-hash bytes；不存在“内容看起来正确”就接受的替代。

## 影响

只读祖先遍历初始发现，Main `c8b7adab9f0c15eb33f235f8d0d9eb205794e376` 和 verifier `c5ea30829800a75badc07cfc25b01c0822e787c9` 分别在 24/25 个可读取提交后遇到同一缺失祖先 `22752a6a41732c8c158d7d7e1b8932ec958f8cb8`。该 commit 已列入 v2 原字节清单，后续历史完整性仍需恢复后检查。

Source builder 自动维护失败涉及的 tree `011adaa9495395d24e8d2596dd1e04c7108ce63b` 已在 v2 清单：路径 `apps/control`，553 bytes，SHA-256 `65b60bc5718357401135e20ed02aee954a73e8318b36f32f59d95f61192d9f44`。此诊断没有执行 gc/repack 或改变 shared config。

## Bundle 证据

- `workspace-projection-cb3646d3.bundle` list-heads/verify 成功；head 为 `cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8`，依赖 prerequisite `1004cf9b8414ee4a248301ead447bc4a022f87d7`。
- `mu-m0-source.bundle` list-heads 成功、verify exit 1：缺 prerequisite commit `8dfebe36508ac0c2508735bb866756dab9283e74`。这不代表 bundle 格式损坏，但证明其不是无需前置历史的完整备份。未解包或写 Git。

## 诊断失败与限制

`historical-bundle-check.json` 保留 verify exit 1。`historical-commit-candidates*.json` 保留不匹配候选计数与未匹配列表；早期两个 cherry-pick 不匹配是 tree 候选集遗漏“已重建但 Root 尚未写回”的 tree，补入后取得 exact-hash。其余无字节来源对象会保留精确 ID 与可确认的类型，不能据此断言永久不可恢复。主仓并发新增对象属于其他执行者，本诊断不计为自身修复。

上述清单是恢复来源证据，不等于对象已恢复、全库 fsck 已通过或正式产品验收已完成。Root 应读取并重新验证每项长度、SHA-256、Git oid 后，逐项将仍缺失的同哈希对象写回；每批保留失败和缺口。

## 本轮最终范围与剩余缺口

最终统一清单 `historical-recovery-manifest-final.json` 包含 4862 项，不与 Main 4354 项重叠；SHA-256 `e095564e1caa648e4a9955446fac8d66b885603c3ed75d6f587f2767f67d4416`。其中 1817 tree、2999 blob、46 commit。它汇总已发送的 v2、extra2 commit、extra48 tree、extra110 tree；Root 若已分批写入，按 oid 去重并跳过已存在且类型/字节校验通过者即可。

两次 tree 候选重建各设 120 秒/60 秒上限，实际 120 秒/22 秒，新增 48/110 项。结果仅接受原 Git SHA1 精确相等；原有 tree bytes、现有条目 mode/name/oid 是候选来源。所有未命中猜测都未写 Git。

剩余 62 个精确 oid 见 `historical-remaining62.json`（类型及引用）和 final manifest `remaining`。32 个已确认 tree，30 个因缺父 tree 尚未可靠分类。不是永久不可恢复结论，也没有证据把这些对象归类为已删除大 zip。有限诊断已覆盖本项目注册 worktree/index、existing object graph、reflog、两个 bundle及 Main receipt 快照；未扫其他项目或全盘。

`historical-ancestor-overlay.json` 以已存在 commit 加 46 个 exact-reconstructed commit 原字节做纯内存祖先遍历：Main 可遍历 1149 个提交，verifier 初始 head 可遍历 1150 个提交，missing commit boundary 均为空。这证明给定候选恢复后的提交父链可闭合；不代表这些对象已经写回，也不代表 62 个历史目录对象已恢复。无内容遍历的提交历史与需要 tree/blob 的历史 diff/checkout/gc 必须区分，后者仍可能遇到缺口。

新增诊断失败记录：首次 worktree 清单终端输出被截断，完整内容已捕获 `historical-worktrees.raw`，后续结论均由文件读取；候选枚举达到预设上限属于边界，不当作验收通过。读取 180 个 index 无变化、无读失败；bundle prerequisite 缺失仍按原失败保留。
