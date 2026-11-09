# Git 对象只读诊断与原哈希恢复方案

结论：Main 当前 HEAD/index 闭包缺失 4354 个对象（3164 blob、1190 tree），全部已找到严格哈希一致的可恢复字节。没有执行 Git 对象写入、索引写入、工作文件替换或 checkpoint 修改。

## 当前证据

- HEAD `c8b7adab9f0c15eb33f235f8d0d9eb205794e376`；HEAD tree `cd951533206a6a4545a6e55fec374e62289d2dd4`。
- Main index 有 36172 条；unique blob/tree/commit 对象批量检查 28171 个。缺 blob 影响 4421 条路径。
- Main index SHA-256：`108db9e12c8234f77ecc1d1ddd4f22ca34ab50fc731c46c6dd76e4a22a6a31e7`，初始读取前后相同。
- 从 index 的 mode/path/oid 纯内存序列化 Git tree，根 hash 与 HEAD tree 完全一致。缺失 1190 tree 的原始 bytes 均写到本报告目录 `<oid>.tree.raw`，未写 Git objects。
- `.git/objects/pack/pack-6907b33dc2b1550308e0abc818657fd6f7a0eacd.idx` 和 `.rev` 存在，对应 `.pack` 不存在。孤立 idx 中 9278 个对象批量检查均缺失，包含当前需要的全部 4354 个；4924 个不属于当前 Main HEAD/index 闭包。此证据不确定文件缺失原因或责任人。
- 当前 repo 无 configured remote。未联网 fetch/push；未查询或复制其他项目。

## Blob 原字节来源

3162 个 unique blob 与其当前 Main 文件的原始字节 Git hash 完全一致。剩余 2 个来自既有历史快照：

| Git blob | 原字节来源 | 长度 |
|---|---|---:|
| `6140a5b5ead748e28487b78a777bf9c8d07192e8` | `execution/v2.4/receipts/W05/W05-99/integration_codex/handler-interface-decisions-r286/checkpoint.original.json` | 715675 |
| `f777b35c666919612b86f98e6768d9c80d9bfb01` | `execution/v2.4/receipts/W05/W05-99/integration_codex/handler-interface-decisions-r286/path_ownership.original.json` | 118768 |

checkpoint 候选检查 773 个、ownership 候选检查 460 个，均无读文件失败。没有把当前 dirty checkpoint 或 ownership 当作旧版本。各来源 SHA-256、Git oid、长度都见完整 manifest。

阻碍 builder commit 的 `5bdaca382611ce033c9aaece2230be91ae3ed537` 已与 Main 现有 16-byte 文件严格匹配：`execution/v2.4/receipts/W04/W04-99/independent_revalidation_codex/3fcbab3f-7e2e-498f-8de4-6dd3b6c035ae/SYNTHETIC_HELPER_SOURCE/g-ab29eaf8/execution/v2.4/receipts/W04/W04-99/integration_codex/step_state_before_acceptance.json`。

## Root 可执行的最小恢复

使用 `recovery-manifest-complete.json` 的 4354 entries。逐项读取来源 bytes，验证长度、SHA-256 与 `SHA1(type + " " + byte_length + NUL + bytes)` 全部等于 manifest，之后才对仍缺失对象执行 `git hash-object -w -t <type> --stdin`，输入这些完全相同的 bytes，并断言返回 oid 精确一致。该过程仅新增原哈希对象；不改 refs/index/worktree。无需 write-tree/mktree、不需要checkout/reset、不需覆盖当前checkpoint。Root 串行组织恢复并与 builder 协调，避免与当前提交重叠；读取前后再次记录 Main HEAD/index/dirty 基线，失败逐项记录。

恢复后：批量 cat-file 检查 manifest 全部可读；读取 `HEAD:execution/v2.4/checkpoint.json` 验证旧 blob；执行原本失败的 `git diff --check`、Main staged diff 检查，并让 builder 保留原 staging 继续自己的提交。当前对象恢复成功不应表述为历史 Git 全库修复。

## 边界与失败保留

孤立 idx 中另外 4924 个历史对象仍需单独恢复诊断；它们可能影响旧 commit 遍历、历史diff、全库fsck。本文不声称所有 commit/历史资源已恢复，也不认定存在不可恢复的大 zip。若某条旧资源缺原字节，保留该路径缺口，不伪造内容或修改历史。

诊断命令、原始对象映射、候选匹配与失败见 `commands.json`、`initial-diagnosis.json`、`blob-candidates.json`、`checkpoint-candidates.json`、`ownership-candidates.json`、`orphan-index-check.json`、`diagnostic-failures.json`。本报告目录的新增文件是唯一写入范围。共享对象可能被其他 builder/Root 并发新增；本报告统计是诊断时的观察，并非全仓锁定快照。

## Pack 与 bundle 本地查找

仓库内含隐藏路径的 `.pack`/`.bundle` 文件名盘点完成，见 `pack-bundle-inventory.json`。没有发现缺失的 `pack-6907b33dc2b1550308e0abc818657fd6f7a0eacd.pack` 同名副本。找到 5 个现有 Main pack 和 2 个 ResearchOS 功能 bundle，以及嵌套工具/qualification checkout 的独立 pack；未将这些独立第三方对象库混入 Main、未解包或修改任何 pack。此搜索不能证明工作区外没有备份。
