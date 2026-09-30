# W18 验证

`RESEARCHOS_TASK_ID=W18` 且恰好一个 `RESEARCHOS_CHECK_ID=W18-G01|W18-G02` 或 `RESEARCHOS_CASE_ID=A12`，执行 `python ops/ci/backup.py`。G01 是失败注入夹具；G02/A12 是 Windows 原生 SQLite/WAL、独立 CLI 子进程和真实文件隔离恢复。所有业务任务/来源页/运行器输入仍为明确夹具；不把 W05 真实模型阻塞改写为通过。

`expected.json` 固定逐例非零断言集合。未知或双重选择器、平台错误、缺失/重复断言、命令失败、源文件漂移均非零退出。保留 stdout/stderr、逐条 expected/actual、原始行 hash、版本 hash、命令、manifest 和加密包。恢复密钥不进入证据。包的独立重放使用相同命令新建密钥，旧包仍可核对 ciphertext hash。

原生恢复覆盖双项目、ContextBundle、非零费用预留、SourceCursor/source_pages、验收、待处理通知、事件与产物；W13 通知生产行为不是本任务接受范围，使用符合 schema 的持久化通知输入。恢复后用现有接受依赖门重新判断 receipt，继续原 task/run/checkpoint，先对账 UNKNOWN 副作用和原进程，内部事件重复消费不增加逻辑数。

当前原生演练并未进行 Windows 重启/隔夜（W19），未运行外部模型（W05/W12），未取得 W17 受限产物备份资格。自动启动迁移拦截器需根 owner 合入 `ops/restore/guard-proposal.patch` 才覆盖现有 Service.New。执行者只提供 `GLOBAL_EVIDENCE_V1_CANDIDATE`，独立 Verifier 签发最终门。
