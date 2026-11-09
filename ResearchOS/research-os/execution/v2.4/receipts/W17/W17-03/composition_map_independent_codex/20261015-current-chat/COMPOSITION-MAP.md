# 四支 Source 与 Main4f 的精确组合影响图

结论：可形成 **从 Main4f 开始、精确53个文件** 的隔离组合施工范围。按各支真实基底核对，所需文件全部可读取，53文件均满足前置字节匹配，**无文本合并冲突**。唯一跨支同文件是 internal/domain/backup.go，必须先storage25后Native25。没有创建组合候选，也没有运行组合测试；本报告不是组合接受。

## 基线和接受范围

Main `4f4023c956f84d65743f39ce77d6c8899a21ada1`，tree `3db13a15cc52b2b0bd75cae3452c66509a9f55c9`。

| 支路 | 实际base | 接受的HEAD | tree | 范围/接受边界 |
|---|---|---|---|---|
| storage25 | c465d1356480d6e6a90da84656724f9fc02b31c7 | d17acc0e128d8438e530ffafc8d704d15b3dd500 | 0b182d56b6f5c76b3c80f0f4aeea38a384544dba | exact9，R4 SOURCE_FIXTURE_ACCEPTED |
| Native25 | 60f8c81a7529081eb51d525ab913d63102148a46 | f80955594bdd0373ae1c961cd02ab6be96f2c196 | 5bce20214223e8292f16a117a83407f52b4bca4a | cumulative22，6文件修订闭合TEMP问题，Source接受 |
| Core | 60f8c81a7529081eb51d525ab913d63102148a46 | 8f50cb57ff821554aef17e9a9bd5208935489d50 | 361ead86ee812d5e040fe1d2cde2a92297eb639f | cumulative21，限定累计Source接受 |
| Bridge兼容 | a7ec7ebf2d53848ea163b6115667b3e3761a6bd2 | 0f9a870aed72785297a9999396fc8c760b296e13 | fa071c9be7e39628c0b86ad43f77d5c50be63c7c | exact2，SOURCE_ACCEPTED_LIMITED |

任务文本storage hash末尾多了9，已用冻结report与Git确认上表40位hash。storage实际基底是c465；60f8c是a7ec加同一storage9的隔离组合。四支scope/manifest和接受报告已绑定在JSON inputs中。Native旧22文件报告曾NEEDS_REVISION，revision01明确闭合该问题，不能只拿旧报告或末6文件冒充累计范围。

## 给builder的边界

1. 从Main4f建立新的隔离候选，保留其全部现状；先应用storage9的确切delta，再Native22，再Core21，最后Bridge2。Core与Native彼此文件不重合，Bridge与其余支均不重合。
2. internal/domain/backup.go先取得storage的schema25 validator版本，再应用Native的publicPauseUpgradeHandoff/preservePauseUpgradeWorkspaces delta；最终完整字节应等于f809的该文件。禁止用storage版本最后覆盖它。
3. 只允许JSON bounded_builder_scope.source_paths中的53个文件；每文件base/candidate/Main/expected_before的blob、SHA-256和字节数均已列明。新增文件的base=null。若实际前置不再匹配，停止对应支路并回报，不能扩写文件。
4. Main自a7ec以来的10个文件与四支白名单完全不交叉，全部要求原blob不变：其中c8的desktop-management与coding-authorization测试，及c5/4f的control入口、verifier实现/日志/崩溃与参数测试。不得将任何oldbase分支整树覆盖到Main；那会回退profile验证并删除verifier功能。

## 语义交叉与必须保持的门

- **control入口**：Main apps/control/main.go原样保留。runRuntimeVerifierReplacement先分派；其后runPreparedRecoveryMaintenance由Native文件扩展PauseMigrationArgument。普通启动取得DataRootLease后仍先调用runtimeVerifierReplacementStartupGate，再store.Open；不能以新增迁移入口为由删除或挪后gate。Native私有入口仍必须先验证继承authority，不能落入普通启动。
- **verifier只支持schema24**：internal/host/runtime_verifier_replacement_windows.go:285明确要求完整1..24；组合不得擅自放宽到25。startup gate验证replacement历史链/当前安装记录，本身没有schema24检查，二者不能混为一谈。升级到25后再做verifier replacement尚不支持；需要独立范围和证明，或者在另行批准的运行计划中处理操作次序。本图不授权任一操作。
- **新二进制身份**：组合后control/backup/root/enrollment/verifier哈希均须重建核验。此前f809的程序pin、签名release、grant/config只能证明旧候选，不能复制为组合运行授权。
- **Core与Bridge**：Bridge支已独立使两项旧inline回归通过，Core支已独立验证V1两轮暂停；合并后仍需同一候选同时跑两组。Core原报告的旧依赖问题不能凭文件拼接直接宣布关闭。
- **schema25**：storage提供三表及backup validator，Core依赖其receipt/CAS/activation；Native提供受限24→25入口。源码齐备不证明实际迁移或普通安装包兼容，不能对真实data启动试验。

## 必须的组合验证

JSON required_tests给出T1–T8精确目的：53文件与Main10保护检查及组合程序构建；c8 profile/4f verifier参数、因果日志和crash回归；storage+Native旧23→24及新pause备份/restore/staging边界；两个private入口与普通startup gate；Core13 domain+Host8 native（17秒模型/工具、完整rollback、queue/预算）；Bridge legacy+V1和原两项checkpoint回归及普通queue3；fresh fixture schema25启动/restore；另行授权后的新pin Native/package门。

这些测试是待执行要求，不是本报告PASS。没有读取产品数据、运行package、签名、迁移、改Main/Source/shared状态。历史失败/清理拒绝保留；本次所需对象读取没有遇到缺树，不能据此声称历史62缺树已修复。若后续缺对象，仅阻塞对应支路，禁止GC/repack/替换对象。

formal_increment=0；0/42，22父任务open。

## 精确文件表

| 支路 | 文件 | 接受版本SHA-256 | 预期操作 |
|---|---|---|---|
| storage25 | internal/domain/backup.go | `1b4e89d303bf036fd2e2d66d352b72b251ff9365b52c43e5c657acbac9a37076` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_host_configuration.go | `86b150616972ca12fced1f11e7257fb7a08c3c48fa6794af30f241365cc05c52` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_migration.go | `fcfeb94c06028b8e5d78ad536cfc5daaab7ed5be35845fb03b25fc1f2ff4b3c4` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_pause_upgrade.go | `8f51609f829eb6f0d32cbfc430e42dc54e6afa834a506848466b41b0d5757de3` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_pause_upgrade_test.go | `e0ee87cda74f9be7abef0e6523cdc0db3f91152e93338eac2430ba5707f5e99a` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_prepared_abandonment_upgrade.go | `9f20c5e1498b86118ac996d34182348c9116a7d35b23eb29ed99fe33bf0945c6` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/backup_prepared_abandonment_upgrade_test.go | `2cc6f1361b39527016e7a5ac33b3ca423776d810795f9304433a7241492d37ca` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | internal/domain/contracts/runtime_pause_activations.sql | `6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0` | APPLY_EXACT_ACCEPTED_DELTA |
| storage25 | migrations/sqlite/0025_runtime_pause_activations.sql | `6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | apps/control/pause_recovery_windows_test.go | `e3ced6fc8edf4c2db0459469b756400301ea3687e6bc8607d2d577b37ec57fc8` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | apps/control/prepared_recovery_other.go | `b38151a92b3cb923258315870820ae1a3835bdc3fd2dadafd55f3907ba09fad3` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | apps/control/prepared_recovery_windows.go | `dfe9d8779bccb2ea73c3709742f7db0a0c88299c82455b54642588780c0e79b6` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup.go | `83762d8c6b89d7cae18d276da280c4cfa7aa7fd8f2e4af5abdb95f7ea1316935` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_handoff.go | `7a43174328f01d0c180cf9495ecdb6ea8cd41a17d8e5cdefa086a54d134145cf` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_handoff_test.go | `12173833bd9dd9db5ecf69a1a106f8a94960dd22c21465084ca6f50f56fcc24c` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_migration.go | `831af16ee1d9dfa06657bf08c413b49e66bbf0a264f5eca6feedf4763da145f7` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_migration_test.go | `a0fbb98d41c37a5c5558925f63b1168876f5eb17317eff99562157df6ba0e8ab` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_migration_windows.go | `7b68ee02defda090da2341a47faff642e0858a6bc7359fccdde19d8043c63f5e` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/domain/backup_pause_migration_windows_test.go | `d55f947b4ef317ef035cd25ef4a73456b95aa23f5a1a74ecd98492b4530f2000` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/enrollment_windows.go | `9a6c398d39a3fe1f3f322457bc65b3d299be7b0a0267a9588f7d254cd8140641` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/migration.go | `bb105b9b57c8beab3d44e0ded44c74499265ff11cd757a97494b88c798c9644d` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/migration_windows.go | `a48ab5fa964a97c00039d8319fdd4d24e961067a02b2c498e2ff2be4c6dcff32` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/native_other.go | `845eb352a2957011d6009a21380d828961820ff0ffaae5db5841a5f03b43538f` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/pause_migration.go | `46a153caa91fec36de8133fc0f700debdab8c8de405fe93f12b683953891e93a` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/pause_migration_test.go | `d4725ffd3a684fa2c1652d89fd764e1f1cb09b32f8257f931b1fb11fc74b6afd` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | internal/recoveryauthority/pause_migration_windows_test.go | `661b77b0678554655cb58494529afccbb74a179359f08377e1372a49664f45b6` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | ops/backup/main.go | `0304737acebb24ed1b5b065d680aa90d25a33f1e7b0add037b3aefa881a893a9` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | ops/backup/pause_handoff_test.go | `883039ca17d760df6f13da994a492ab9278eeda0e03c92662d3491526e0ddff6` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | ops/supervisor/recovery_enrollment/main_windows.go | `b54f79e9e6127c4df749716d97a6dcbe069c11eeedd4e196a68002d659ef1f0c` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | ops/supervisor/recovery_root/main_windows.go | `fc5ff16ea3d47ec1905d573d48d1e204d0d72a4920f905076afaff3d3373d771` | APPLY_EXACT_ACCEPTED_DELTA |
| native25 | ops/supervisor/recovery_root/pause_migration_windows_test.go | `2167ed668db70afa8b8ff7d2f50df2b049ea612554a07640c2ddca90682d5008` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/budget_scopes.go | `8a342c7803177ee98045d9650535e87d099fc6b5f302114573b6aadee7dd0101` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/client_protocol_queue_control.go | `71844cdf5109ac2e33467e9f5052c21f98a29379e632214efef1bb17d581780b` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/durability.go | `9ea0587ba77b7a69bebbc3b4fede1afa93b0d20395ac7eda0d574712eeaa1fb8` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/http.go | `42467af3f6add0fa679cf90a2b2693b92f7655f1fe765f533f4c17d5f67ba86f` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/operations.go | `b37d3196d6aaf2657c33c9ccb5a6ce2d67ea3055ed4d768cc06d67a58931b195` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/orchestration_controls.go | `c7233f61a692d5fc9d26c846022e9c88cf369197d039d751ef15d88aca642de1` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/orchestration_recovery.go | `2363bc4207d868a7d5415ccdbea76682aa8d41fb3803b4d49d8b8e2bdeadab69` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_broker_windows.go | `c5ab5380d681c4c59c39e8a0c5337f6780cd0039f348ffc5367acdc72d185d53` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_command_queue_windows.go | `1b3a0ca15893b907c3bcae930ff233bcc552fb712f62f34ab0057e5cb9c0ac41` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_coordinator_windows.go | `f39c2fbada791050dd7535f03f394a3400315a84f736f8b0e3e743690499e14a` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_dispatch.go | `dd742fa0e3e131d305ddacd4e3ab947c4eae0d63134ec0b05b6179e83e136811` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_model_stream_windows.go | `76ed8e5bb72be714a25462154620cb694fad32409066e28a1c54c4569a064bc5` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_model_windows.go | `227bb7d8d0becceec995431844f025767967cbcbfad96be7161062df5d020d3f` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_pause.go | `3e2eb7a1eca96df2fd5d2db75e464bccbcc2008f391679acf9bdfee707602878` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_pause_test.go | `fda0b5800710aa7bc77749dc780d2988c8c12e4230e01767d3edb3fdc5ddfa49` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_pause_windows.go | `829ee74f01024df612690c565d725fa2604903695bc33445ce4f2ad6b989cb0c` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_pause_windows_test.go | `f98e89c91d34aa314ab52b84f22c788b5eacf4c40fb67d6fd2ecc09e60919fd4` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_recovery_windows.go | `14ea053c2a36d1d8d9f0f3558c081efabe590c5564a2e1fd93fde9f62cce8a03` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/runtime_tools_windows.go | `7b5c9bf782d18efc17a27287ab4cdf9d4949b8335aaff7c45648a26358138286` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/domain/store.go | `3f08cad1509eb6294711082a8d372711003f8a3aae97bbf179cf6da8431b2315` | APPLY_EXACT_ACCEPTED_DELTA |
| core | internal/host/runtime_pause_windows_test.go | `b20b4b3d1ca9ca282021a1ee48e1bd028250229257c7ab340913775fc1b8f845` | APPLY_EXACT_ACCEPTED_DELTA |
| bridge | adapters/runtime/bridge_legacy_checkpoint_windows_test.go | `c7d8af8bc1e2d7b7cf5e988cce0075cd2ff025fae2b7ec0724392ec13a8cd575` | APPLY_EXACT_ACCEPTED_DELTA |
| bridge | adapters/runtime/bridge_windows.go | `71555893e2f4793acdd2ebc83ef57e98c6a5c84cf1742dbec00b42ea4581c224` | APPLY_EXACT_ACCEPTED_DELTA |
