# Desktop15 当前 CLI qualification gate 改造映射

状态：只读映射，未写实现，未授权执行。先保留原 source import proof，再添加两例 qualification。真实 W05 review decision 为 CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED。

基线 builder.main 为 149–419 行，controller.grant_check 为 129–256 行。完整原文锚点与 SHA/bytes 见 source-consumer-anchors.json；逐字段、拒绝条件与实际 schema 见 gate-mapping.json。

1. builder 199–210 行原 byteblock 及原四 cli43 refs 全保留。在 210 行 scope.update 后追加新的纯 IO/JSON/hash consumer；输入仅新增两个明确 refs：cli43_current_qualification_review_ref 与 cli43_current_qualification_review_manifest_ref。消费者验证真实 sealed review、qualification、root closure MF 与跨文件路径/SHA/bytes；派生并保存五个 scope 字段。不得调用候选、helper 或 native。缺字段即拒绝。
2. controller 234–250 行完整原谓词保留；在 250 行之后、desktop_source_review 之前调用同一组机器谓词。验证必须通过现有 document/verify/read，使所有原件进入 READS。这样原 launcher 113 行在 native 前就调用新 gate，原 inner execute 289 行再次核验，guards 350–356 行在 apply/commit 前重核字节。
3. 新 scope 候选更新 controller 精确 ref，并新增五个 mandatory qualification refs。原 scope.v3 和 builder 的固定 source review 无权批准新 controller；须派生新 scope pin、新 controller/source review pin，再取得新完整 scope/metadata 审查。所有旧封存原件不改。
4. metadata builder 91–105 行与 139–160 行已整体序列化 bound scope 并继承 binding.immutable_inputs；metadata engine 按 future_scope_ref 固定完整字节。新 refs 必须随 READS 保留到 immutable_inputs，不能只放到展示字段。此需求自身不要求改 desired/register 业务逻辑。旧 review/hash 不可移用到新范围。
5. launcher 84–114 行现有逻辑可复用全部原字节：它 pin 新 controller，native 前调用其 grant_check，并保存 controller.READS。保持 Job/helper/time/resource limits。

两个 manifest 的实际形状不同：qualification manifest schema researchos.public-review-manifest.v1，count=18，entries；Root closed manifest schema researchos.root-launch-closure-manifest.v2，members=11，无 count。原 builder.seal_members 106–119 行只处理 entries，新增 consumer 必须按真实 Root schema 明确读取 members，不能直接套用 entries 或伪造 count。

Root completion 原 fresh_compile_qualification/caller_OS_lifecycle_qualification/complete_current43_source_validation=false，independent_qualification=PENDING；这些不可写回。独立 qualification 才给 current43_fresh_held2_qualified=true。self-send CLI_exit=3 是预期 BLOCKED，native_test_exit=0；不能改成 0，也不能要求每个 generation exit0。

qualified review 仅允许 NEW scope preparation。未来 Desktop source-only 一次执行仍走新独审→真实 CAS→seal→exclusive Root grant；source_acceptance=false/formal_increment=0、product_tests_HTTP_SQL_models=0、fresh58/GUI/install/NVDA flags=false 都保留。资格 tuple331/159/509 是历史取证点，不能推新 tuple/counter cut。

原 exact15 与 combined58 源路径、原 Node169 作者证据及未来有限 roster/caps 全保留。当前两个 binding 包没有物化 Root combined58 的新 test roster；58 表示源路径并集。原 finite roster 的 159 个新 leaf+7 regressions 与追加3作者证据不能冒充本轮 Root169。它们在后续独立 fresh58/Node scope 中精确绑定，本映射不新编测试或削弱断言。

