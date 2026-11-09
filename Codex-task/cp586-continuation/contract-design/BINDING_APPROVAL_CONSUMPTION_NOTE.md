# Approval consumption is not inferred from a SQL row

补充此前 BINDING_SCHEMA_REVIEW_EXPECTATIONS.md（SHA f1c728bf…）；该文不改写。

UNIQUE 只证明同一 approval 最多有一条已提交 binding。它不能证明外部/native approval 是否已消费，不能覆盖 SQL 事务回滚之前的外部动作，也不能把 UNKNOWN 结清。没有 row 绝不默认“可重试/可重新授权”。Host 必须核对原始一次性消费/未知 journal 和原 scope，保留原 origin/candidate/NoProgress。fresh fixture 的 rollback 只证明 DB 行/claim 回滚，不证明 native scope 恢复。

整数 JSON 还应校验提取值确为 SQLite integer；json_type 看起来是 integer 的超范围 JSON 数可能被提取成 REAL。不得用 CAST 将 REAL钳位到合法epoch。现协议允许精确int64，不应额外加2^53限制；原Run/lease证明仍未在prototype实现。

建议 consumer/fresh backup 负例加入：未知版本/无row/多row、缺表/trigger/index、跨Host复制、错误canonical hash、原始创建命令缺失、双合同置换、旧Task/Goal/receipt/epoch，以及两个连接同时争用approval只有一个提交。schema/consumer PASS仅是数据不变量；生产backup/restore、Host/SID、当前资格和LIVE接受均未验证。

本补充无DB连接、无D写、无native/model/资源动作。