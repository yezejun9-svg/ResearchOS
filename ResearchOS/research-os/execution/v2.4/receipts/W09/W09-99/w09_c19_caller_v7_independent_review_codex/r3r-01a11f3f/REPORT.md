# W09 C19 r3 Caller 独立 Source 复核

结论：**SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_FRESH_VECTOR_AND_ACTUAL**。Source resource gate 有条件通过；actual resource gate 为 NOT_RUN。修正独立静态检查的定位错误后，196 项检查与90个固定输入全部通过。五个 future 路径在检查前后均不存在。复核实际持有 SourceReadGuard，两次调用都关闭全部句柄、无 retained handle；没有读取或锁定当前四个 canonical 文件。

这份复核不授予用户权限，也不是执行 grant。Root 可依据已有目标与自身授权，在登记新范围、封存新的显式 canonical vector 并核对调用条件后决定是否执行。CP366/OW170 是 Root 提供的后续计划，不是本复核宣称已存在的状态。

## 精确差异

r3 的 preparation 和 producer 相对已独审 r2 只替换以下五个固定根的尾部标识：
- candidate：w09c19v7-1a11f30；
- isolation receipt：w09c19v7-isolation-1a11f30；
- producer receipt：w09c19v7-producer-1a11f30；
- preparation environment：w09c19v7-isolation-env-1a11f30；
- producer environment：w09c19v7-producer-env-1a11f30。

按独立指定的五组替换，完整正向字节等于 r3，逆向字节及整个模块 AST 等于 r2；所有函数的 AST 在替换前后直接相等。原 native jobs、时间限制、工具 hash、SourceReadGuard、compiler inventory、候选覆盖、selected tests 顺序、raw archive、清理和终态逻辑完全保留。没有执行这些 Caller。

六份 Source 的目标顺序保持；五份引用与 r2 完全相同，仅 ops/ci/w09_evidence_closure.py 使用独审接受的 v7（1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777 / 42716）。source.integration.choice.json 通过独立完整构造核对语义及字节。允许差异严格限于六来源中的 closure、五根路径、r2 base/review 引用、v7 作者和独审引用、历史 provenance；没有额外选项或行为变更。

v7 独审 HDF/MF 被 choice 和调用合同精确绑定，HDF 的 candidate_ref 指向实际 v7。r2 既有非作者 Source 接受记录也保持原 pin；本轮不把它当新的 actual 结果。

## 向量与凭据隔离

prepare 仍需6个显式参数，producer 仍需10个；锁定 Python 使用 -I -S -B -X utf8。producer 合同准确写入最终 choice 的 SHA256 和字节数。两个 bind_canonical_input_vector 函数与已独审 r2 逐 AST 相同；vector 的路径、4个 canonical refs、大小、SHA、checkpoint revision、CLI 参数一致性校验及有界 vector read 保留。

CP365/OW169 只在历史 Source provenance 内保存，旧 r2 的 CP364 provenance 也完整留存。实际 Caller 不读取该 provenance 作当前锁定值，choice 的 effective source/input/review refs 中没有静态当前 canonical pin。因此 Root 可先登记新 Scope，再封存新向量；prepare 和 producer 必须传同一份向量与同一 CP3 参数，不能采用 implicit latest 或混合两个时期的向量。

producer 固定读取新 isolation receipt 目录的 isolation.ready.json，验证新 worktree root、head、closed jobs、未覆盖 Source 及相同 vector。新 worktree 的 producer base 必须此前不存在，并只接受本次创建的唯一 run 目录；归档原 bytes 在校验 producer/report 成功结果之前。旧 ready、原 v6 packet/report 和新 packet 不能混用。

## Source21 与验收边界

producer 的原21项 SOURCES 清单保持，并包含 closure；version_manifest 仍从新 worktree 的实际字节计算 hash。v7 改变了其中一项，必须产生新 producer packet 和绑定新 run/source 的非作者 ModeDecision。r3 Caller 不运行 consumer、不产生 ModeDecision、不登记正式命令、不增加 formal accepted count；旧 packet 继续原样保留。正式数量仍为0，Main adoption、实际 Go 编译/formatting、SQL/API/model/Native 结果均未在本轮产生。

## Controls 和原始失败

作者最终141项 controls 的来源已经分开核实：原131项中128项未受 binding 修订影响，保留原记录；13项在最终 binding 后新增或重验。前128项与原记录扣除3个受影响检查后的序列完全一致，原记录的精确引用保持。不能把141项描述为最终 binding 后全部重跑。本轮的196项是另一次独立静态/AST/pin 检查。

作者原始失败933、934的精确原文与资格描述保持：933 outer1、Python/Native/model NULL；934 outer1、Source Python1、Native/model NULL。未重编号、拆分或抹除。

本复核自身另有一次原始检查失败（工具 chunk339c9e）：全文件查找首个 assert result[actual_exit]==0 时误匹配 success() helper，导致“归档先于 producer 成功检查”的静态断言误报。候选源码无此回归。原 review.py、失败原始 IO 和真实 cleanup 原样保留；新 review.fixed.py 仅将该定位精确到 report 成功断言，并写独立 cleanup。其成功 chunkc48014 不替代旧失败；Root 分配的 ordinal 和原文 pin 见 failure-disposition.json。两次都是 Source 静态复核，不是 Caller/产品重试。

STOP_FINAL。

