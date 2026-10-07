# I2 独立复核：b1877d4

结论：`PASS_IN_REVIEWED_DELTA`。本次发现的公开 close 绕过、零 Task 周期归属缺失、任务上限导致事务反复回滚，以及进展仅按次数或对象 ID 判断的问题均已在冻结源码中修复。没有新增阻塞代码问题。这个结论只覆盖下述源码、已有离线机制证据和新 SQL 约束，不能升级为 I2 全部生产验收通过。

冻结源码 `b1877d4a32f15868d19ed9d32f39fc2b6b563db9`；证据 HEAD `17245722ac6c2a970680b44542b2f668c32ed88f`。本次逐文件比对 16 个源码/测试/migration 文件与冻结 commit，作者 worktree clean。精确 SHA256、逐测试 PASS/FAIL 和原始失败信息见 `source-and-raw-audit.json`。

## 已审边界

- `research.go:365` 的公共 close 与 driver 共用独立 delivery receipt、当前报告正文、Monitor authority 和原始 report Run 进展计数门。不可因无 stage Task 或 monitor 已退役绕过。CANCELLED 仅在所有关联 Run/effect 已对账时保留原结果退出。
- `research_driver.go:117` 与 migration 0020 的永久 cycle→Monitor 关系在创建周期的同一事务登记；已有 manual cycle 接管须 exact profile 且窗口受限。关系不可替换、更新或删除，Monitor 退役不会移除历史归属。
- discovery、verification、review、experiment 新任务均先检查容量，为 delivery 保留一格。未物化的 required experiment 显示 `REQUIRED_EXPERIMENT_NOT_MATERIALIZED`；候选未完成审阅与来源覆盖缺口继续进入报告。
- 实验 broker 使用原有原生 paired execution、注册执行文件、冻结输入、effect reservation、不可重复 execution receipt 与独立 acceptance。当前仅 FIXTURE native experiment 合格；离线测试实际调用 AppContainer baseline/candidate，外层是进程内控制，未证明 native child broker 网络输送或 LIVE provider。
- `research_close.go:8,160` 按已审来源根身份及角色分组的 sealed artifact content hash 判断新进展；cycle/Run/Artifact/Experiment ID、hypothesis 和采样值不会单独产生新改善 key。跨轮计数保留原 Run 记录，达到限制时仍保留正确报告的 ACCEPTED 状态。
- Monitor 仅恢复自己施加的 PAUSE；cancel/drift 保留未决 Run/effect 的所有权和停止请求。历史 plan 只按已密封字节及 hash 读取以安全取消，不能授予新工作权限。
- `store.go:277` 的唯一共享放宽严格限于 exact ResearchCycle `/profile_ref`、同项目 ProjectProfile、revision>1、当前 CANCELLED、ref 与上一版本完全一致；历史存在性和 content_hash 检查照旧。新建周期、RUNNING、其他字段和改换另一历史 ref 不获豁免。作者最新 drift 子例覆盖正常保留、RUNNING stale 拒绝、改换真实历史 ref 拒绝；新建/其他字段边界本次由代码确认，未另跑业务测试。

## 证据范围

只读审阅作者全部列出的失败与成功 raw，未重跑任何业务测试。`bound-close-second`、`cycle-binding-native-pair`、`offline-native-experiment-second`、`lifecycle-migration-third`、`drift-historical-ref-final` 对应检查 PASS；`lifecycle-first` 中跨 cycle no-progress 单例 PASS，其同批 lifecycle 失败仍保留。早期 raw 并不全部来自最终源码，具体时序遵循作者 `FREEZE-b1877d4.md`，没有宣称最终全套重跑。

独立执行仅为 `monitor-cycle-probe.py`：SQLite 3.50.4、内存数据库、recursive_triggers=0，加载真实 0013/0018/0020。新关系的正例及替换/更新/删除、缺对象、跨项目、错误 plan、未接受 plan、退役后新增关系拒绝、退役保留归属共 11 项通过。这是数据层约束证据，人工构造最小数据库记录，不是业务授权通过。此前五项旧约束探针未重复；其旧 0020 SHA 为 `f39537de7c1f4b649fbd9eb742725af3644b96750ad87c0e9d24033b9ecfeb16`，不能当作新 migration 的执行证明。

## 仍未完成

- `native-source-binding.jsonl` 仍为 FAIL：三次 loopback readiness listener 失败发生在业务 I/O 之前，最新 SOURCE 原生网络绑定未验证。旧源码成功、离线 candidate/source 或本次 SQL probe 均不能替代；没有重试耗尽路径。
- LIVE 实验、LIVE 研究准确性、完整真实用户循环、当前源的全套测试与发布未在本次证明。不得升级 production stage。
- `BLOCKED_HYGIENE` 保留：作者删除 `C:/Users/yqyyds/AppData/Local/Temp/TestResearchTaskBoundAndPublicCloseGate1373465950` 被自动 policy 拒绝。作者 handoff 记录拒绝后只读确认仍存在；本次未删除、改名或绕过，也没有重复清理。更早 I1/S2 清理阻塞未触动。

本次只写本报告目录，未改作者源码、spec、canonical ledger 或运行生产服务。
