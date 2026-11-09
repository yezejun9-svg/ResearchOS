# Frozen suite selectors and qualified coverage

当前 `whole58_test_suite_qualified=false`。所读证据不存在已经封好的 E2 全suite consumer/资格签署；下面的真实旧计划和有限当前控制不能自行拼成完整资格。

## 已资格：current58 CLI2 actual argv

- case-00: `["D:\\作品集\\ResearchOS\\research-os\\.local\\cli58-export-0e298790cd484ec9ba319a379e7e34ed\\bin\\test2json.exe", "-t", "-p", "researchos.local/research-os/apps/cli", "D:\\作品集\\ResearchOS\\research-os\\.local\\cli58-export-0e298790cd484ec9ba319a379e7e34ed\\.cli43-build\\cli.test.exe", "-test.v", "-test.count=1", "-test.timeout=480s", "-test.failfast", "-test.run", "^TestCLIProtocolInteractiveAuthority$/^real-existing-open-readonly$"]`，cwd `D:\作品集\ResearchOS\research-os\.local\cli58-export-0e298790cd484ec9ba319a379e7e34ed\apps\cli`，actual exit0；原REF {"path": "D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\cli58_fresh_compiler_executor_codex\\0e298790cd484ec9ba319a379e7e34ed\\case-00.invocation.json", "sha256": "6c59f1ede3e8762635b88644b20e042b2580dca4d29ca54e66a19f21494ede97", "bytes": 45547}。
- case-01: `["D:\\作品集\\ResearchOS\\research-os\\.local\\cli58-export-0e298790cd484ec9ba319a379e7e34ed\\bin\\test2json.exe", "-t", "-p", "researchos.local/research-os/apps/cli", "D:\\作品集\\ResearchOS\\research-os\\.local\\cli58-export-0e298790cd484ec9ba319a379e7e34ed\\.cli43-build\\cli.test.exe", "-test.v", "-test.count=1", "-test.timeout=480s", "-test.failfast", "-test.run", "^TestCLIProtocolInteractiveAuthority$/^real-existing-self-send$"]`，cwd `D:\作品集\ResearchOS\research-os\.local\cli58-export-0e298790cd484ec9ba319a379e7e34ed\apps\cli`，actual exit0；原REF {"path": "D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\cli58_fresh_compiler_executor_codex\\0e298790cd484ec9ba319a379e7e34ed\\case-01.invocation.json", "sha256": "ec8e0d8d30bc5ffb54d152e7552b2712a5f2fca2a4ed470140f19f4f060912b1", "bytes": 45392}。

只覆盖 real-existing-open-readonly, real-existing-self-send；原 `TestCLIProtocolInteractiveAuthority` 的其它叶子和 full CLI `^Test` 不在这份资格内，不重跑原两例。

## 原 whole38 A–E（22752旧候选；未授当前E2执行权）

### A ./internal/domain

Frozen selector: `^(TestBackupHostConfigurationFrozenSchemas|TestBackupHostConfigurationCompleteHistoryRefusals|TestBackupHostConfigurationSchemaRefusals|TestBackupHostConfigurationPublicRoundTrip|TestBackupHostConfigurationOtherMethodIdentity|TestHandlerRejectedSessionPublicBackupReplay|TestHandlerRejectedOriginalProofBackupTampering|TestHandlerNewIdentityRequiresOriginalHeader|TestClientConfigurationFreshAndNumberedMigration|TestClientConfigurationConstructorRollbackAndPrebackup|TestClientConfigurationHistoryReplayRestartAndIsolation|TestClientConfigurationCorruptReadFailsClosed|TestClientConfigurationFaultRollbackAndCAS|TestClientConfigurationStrictPayloadAndUnwiredSession|TestClientConfigurationNoOpaqueAuthorityAndOldReleaseGuard|TestClientTypedRejectionRollsBackBusinessWrites|TestHandlerPendingProducerTransaction|TestHandlerScopedConfigurationRetainsOriginalTaskSettlement|TestHandlerOriginalHeaderExactBytesAndCorruption|TestHandlerEndpointLexicalMapping|TestHandlerOfflineTypedSessionAndScopedRebind|TestHandlerStrictScopesAndRaw|TestHandlerGlobalIdentityCASAndFirstRaw|TestHandlerStatusBoundedCompleteHistory|TestHandlerStatusCredentialDedupAndLegacyReplay|TestHandlerUnanchoredLegacyReadAndExplicitRebind|TestHandlerCreateNeverSuppliesImplicitModel|TestHandlerScopedFencesAndNoHistoricalRebind|TestHandlerSQLFaultsRollbackOuterTransaction|TestHandlerConcurrentDefaultCAS|TestHandlerScopedCASFaultRollsBackAllBusiness|TestHandlerConcurrentScopedCAS|TestHandlerGlobalOriginalConflictFields|TestHandlerHistoricalReferenceAndRepeatedRebind|TestHandlerRuntimeStoredProfileExactMapping|TestHandlerRuntimeTaskNeedsExactSession|TestHandlerPendingOriginalTranscript|TestHandlerOriginalTaskProofAfterQueuedInput|TestHandlerPreSDKCancelledQueueCanRebind)$`。

`-test.timeout=480s`；原 outer预算 600s；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。Current immutable config/identity, public backup/restore, new handler, original rollback and profile mapping; no TLS selector in this batch.

### B ./internal/api

Frozen selector: `^(TestW14SessionHTTPCreateSendEventsAndReplay|TestW14SessionHTTPAuthorityAndFrozenRequest|TestW14SessionWriterLeaseHandoff|TestConfigurationActualWindowsHostOfflineHTTP)$`。

`-test.timeout=180s`；原 outer预算 240s；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。Actual authenticated public HTTP typed configuration/session and rejection/replay scope.

### C ./internal/host

Frozen selector: `^TestConfigurationMetadataActualHostWithoutDecrypt$`。

`-test.timeout=120s`；原 outer预算 180s；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。Only test-created temporary Host metadata; no user vault or decryption.

### D ./internal/domain

Frozen selector: `^TestHandlerTLSActualSDKConfiguredSession$`。

`-test.timeout=240s`；原 outer预算 300s；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。Isolated self-child trusted TLS FIXTURE; actual frozen SDK/coordinator; expected fixture two upstream calls, no external/paid provider. Capture child exact binary and raw, not wrapper PASS alone.

### E ./apps/cli

Frozen selector: `^Test`。

`-test.timeout=480s`；原 outer预算 600s；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。One current full CLI including isolated TLS children; no addition of old cohort counts. Unexpected failure/skip stops dependent later batches.

保留原 graph argv suffix：`["list", "-deps", "-test", "-json", "-compiled", "./internal/domain", "./internal/api", "./internal/host", "./apps/control", "./ops/backup", "./apps/cli"]`。固定当前Go/SDK/source/embed/migrations/schema/locks/工具/runtime依赖与before-first-case/after/current vectors；原 plan 本身不是新的参数授权。Full CLI E 必须有完整当前事件/leaf proof，旧282PASS/12FAIL和affected78分别保存。

Held 原范围：["C29 immutable ACK-to-final trigger1811/F08", "provider history5 and held original positives", "historical14 ActiveRecovery", "Q10", "LIVE model/runtime/provider qualification", "parent W05/A04/formal acceptance"]。不运行 `go test ./...` 或新名字重跑held/旧失败。

## 当前 Desktop169+Go3 源冻结命令（实际结果尚待新Rootterminal独审）

Go3一条testexe调用：`["<FRESH_VALIDATOR_TEST_EXE>", "-test.run", "^(TestWireParserPreservesAdjacentIntegers|TestWireParserRejectsAmbiguousJSONAndWorkExhaustion|TestWirePrivatePacketExactKeysAndTypes)$", "-test.v", "-test.count=1", "-test.failfast", "-test.timeout=120s"]`。三个原test：`["TestWireParserPreservesAdjacentIntegers", "TestWireParserRejectsAmbiguousJSONAndWorkExhaustion", "TestWirePrivatePacketExactKeysAndTypes"]`。

162个Node逐叶：`[PINNED_NODE, --require, PINNED_OBSERVER, --test, --test-reporter=tap, --test-name-pattern, ^re.escape(exact_roster_name)$, tests/ui/desktop/http-wire-boundary.test.mjs]`。全部精确名称存于 [suite-map.json](suite-map.json)，没有用count替代名单。

7原regression（前加pinned observer，完整保留argv[1:]）：

- w14-native: `["<PINNED_NODE>", "apps/desktop/tests/w14-native.js"]`；one legacy program; assertions not invented。
- w14-review: `["<PINNED_NODE>", "apps/desktop/tests/w14-review.js"]`；one legacy program; assertions not invented。
- only published method and path pairs reach the local host: `["<PINNED_NODE>", "--test", "--test-name-pattern", "^only\\ published\\ method\\ and\\ path\\ pairs\\ reach\\ the\\ local\\ host$", "tests/ui/desktop/w13-react.test.js"]`；existing exact node:test leaf。
- bundled SPA route fallback stays inside dist; missing assets fail: `["<PINNED_NODE>", "--test", "--test-name-pattern", "^bundled\\ SPA\\ route\\ fallback\\ stays\\ inside\\ dist;\\ missing\\ assets\\ fail$", "tests/ui/desktop/w13-react.test.js"]`；existing exact node:test leaf。
- proxy never replays a write on 401; explicit retry preserves upload, safe GET renews, redirects fail: `["<PINNED_NODE>", "--test", "--test-name-pattern", "^proxy\\ never\\ replays\\ a\\ write\\ on\\ 401;\\ explicit\\ retry\\ preserves\\ upload,\\ safe\\ GET\\ renews,\\ redirects\\ fail$", "tests/ui/desktop/w13-react.test.js"]`；existing exact node:test leaf。
- SSE response is streamed with original event bytes: `["<PINNED_NODE>", "--test", "--test-name-pattern", "^SSE\\ response\\ is\\ streamed\\ with\\ original\\ event\\ bytes$", "tests/ui/desktop/w13-react.test.js"]`；existing exact node:test leaf。
- first use consumes native choice, registers and bootstraps before saving real IDs: `["<PINNED_NODE>", "--test", "--test-name-pattern", "^first\\ use\\ consumes\\ native\\ choice,\\ registers\\ and\\ bootstraps\\ before\\ saving\\ real\\ IDs$", "tests/ui/desktop/w13-react.test.js"]`；existing exact node:test leaf。

源码位置：controller行88/201/204/205/220–228。Go3确切三原PASS，无FAIL/SKIP；Node逐叶恰一TAP pass/0fail/0skip；两legacy program须保原正文/显式PASS，不发明内部assertion数。Transport/source断言/OS生命周期各自闭合；176是包含Git/builder/buildinfo等的top native cap，172是169+3开发断言单位，不是172个formal或172次native。

## W05正式入口

- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-G01`；expected IDs `["W05-G01"]`。
- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-G02`；expected IDs `["W05-G02"]`。
- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-H08`；expected IDs `["W05-H08"]`。
- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-P01`；expected IDs `["W05-P01"]`。
- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-U02`；expected IDs `["W05-U02"]`。
- `python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --case-id A04`；expected IDs `["A04-01", "A04-02", "A04-03", "A04-04", "A04-05", "A04-06"]`。

必须核实际registered command revision/真实handler及完整required mode；计划argv和零断言不是PASS。A04-01..06分别是完成语义、取消、崩溃/超时恢复、嵌套/版本兼容、自有CLI交互/JSONL、完整真实编码任务。
