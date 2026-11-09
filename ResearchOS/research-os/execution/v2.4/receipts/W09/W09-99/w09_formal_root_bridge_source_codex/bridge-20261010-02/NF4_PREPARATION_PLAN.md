# NF4 有限准备方案与合同缺口（未实现、未授权）

实际读取的 NF3 基线：
- full_w09_main_native_producer_source_codex/fullw09-20261010-03/root-calling-contract.json：只允许 W09-G01、W09-G02、A06，no_standalone_C19=true。
- full_w09_runtime.source.py / runtime-overrides.source.py：choice() 精确三个 selector；Scope、独立 Source review、Current4、Canonical owner/worker、真实 Root/peer 三行全部必须相互绑定。
- source.choice.json：Source21 中 retrieval_test.go 是旧 518c6dbd.../31296；新的 Main fixture 采用后不能继续以该 Source21 获得当前资格。
- prepare 阶段创建独立 profile/temp/gocache；run 阶段要求 GOCACHE 初始为空，同一请求/环境/Source21，最多一次 go list 与一次 go test。当前 scratch_root 必须严格等于 repo/.local/w09-full-<selector>-<run_id>。
- 实测磁盘快照（工具 ab2e33）：C 可用 31,358,132,224 bytes，D 可用 2,907,148,288 bytes。仅为读取时快照，不是未来开工保证。

最小 NF4 Source 变更建议：
1. 以新命名空间和新 run_id 准备四 selector：W09-G01、W09-G02、C19、A06。新增独立 C19 case_id 入口，沿用现有 Main C19 selected_tests/native IDs 与 FIXTURE 模式；G01 不能代替该入口。三个旧 selector 的语义不改。
2. 由 Root 实际采用 fixture 后重新采集完整 Source21 与 compiler blueprint 的稳定文件/目录 inventory。保留旧 Source、旧 blueprint、旧 exports 和原失败回执；不能把旧 exports 的 hash 重新标成新 Source。
3. 同步调整 Source choice、runtime override、最终 runtime、launcher、prepare/run wrapper、calling contract、独立 Source review schema/binding、Root selector registrar。三个 selector 的硬编码和 no_standalone_C19 必须一致修订，不能只改一个 selector 列表绕过其他门。
4. 本轮只给路径方案：为 NF4 新建 C 盘物理 scratch 根，例如 C:/Users/yqyyds/.codex/researchos-runtime/W09/NF4/<run_id>/<selector>，每 selector 独立 profile/temp/gocache。此路径尚未创建，Root 必须明确批准实际绝对根、owner/lease 与允许创建清单。Source 必须把原 FIXED_PRIVATE_PATHS 的 repo/.local 单根改成新批准根的精确路径公式；继续逐祖先拒绝 symlink/junction/reparse/alias。不能用 junction 或环境变量偷偷绕过原范围。
5. GOCACHE、TEMP、TMP（如显式使用则 GOTMPDIR）应绑定同一 selector 的新 C 盘目录；Go/Git/Python 锁定工具和 Main source_root 维持原契约。GOPATH/module 输入只读保持原 pin，继续 GOENV=off、GOTOOLCHAIN=local、GOPROXY/GOSUMDB=off、CGO_ENABLED=0。不得下载安装或删除旧缓存来制造余量。
6. D 盘保留实际 output/owned evidence 与 receipt 原件，并在每 selector prepare 前做 C/D 分开的余量门。预算需来自此前实际 compiler inventory/export 大小与本次输出上限，由 Root 明确保留余量；当前仅有空闲空间，不能据此承诺四套新缓存够用。任一门不满足就在该次 attempt 前停止。
7. 四 selector 串行各运行有限一次 go list、一次 go test；每个独立 Scope/run/output/lease、完整 stdout/stderr、真实 exit、FILTIME整数、OwnedJob idle/handle closure和SourceGuard closure。失败原件保留，不自动重试、不删/搬任何旧 compiler 证据。
8. 四次实际完成后由独立 Verifier 给出四 selector/六 route 的真实 mode 资格。若任何失败或 Source21 再变化，bridge02 不进入 formal consumer。通过后 Root 为 RUN_CURRENT_CM40 注册新的六条 consumer 计划，完整实际 Final 后才进行后续 capture。

当前 OPEN 合同缺口：
- NF4 Source/审查 schema 与六 route mode/独立 C19 输入尚未产生。
- Root 尚未为新 C 盘 physical scratch 根签发明确创建范围与 owner/lease。
- Root 已报告实际采用新 fixture（b70626）：retrieval_test.go 为 1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141 / 32352。本包封包时将独立核其文件 pin；新 NF4 仍需重新绑定完整 Source21。本任务未采用或改写 Main。
- 每 selector 新缓存/临时峰值预算与 D 盘证据上限尚未从实际 inventory 定量登记。
- 新 Source author 与实际 backend reviewer 的原始 peer 字符串、Root capture 三行、Scope bindings 必须未来实取。

这是有限设计输入，不是 NF4 源码、可执行 Scope、资源证明或通过承诺。本任务未创建上述 C 盘目录，也未运行 Native/Go/list/dispatcher/TP。

