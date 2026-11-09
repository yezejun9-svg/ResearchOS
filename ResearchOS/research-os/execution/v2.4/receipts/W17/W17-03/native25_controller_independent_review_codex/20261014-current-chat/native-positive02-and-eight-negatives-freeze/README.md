# Native25 隔离原生证据冻结索引

已接受：正例02及nonce replay 1组，隔离负例8/8。正式增量0；未迁移实际原库；22父任务保持open。

固定源：`f80955594bdd0373ae1c961cd02ab6be96f2c196`。重新校验 300 项公开引用与manifest成员，全部匹配。

| case | actual native exit | rejection | outer exit |
|---|---:|---|---:|
| missing-native-channel | 1 | AUTHORITY_PRIVATE_INHERITANCE_REQUIRED | 0 |
| wrong-purpose | 1 | AUTHORITY_ISSUER_SIGNATURE | 0 |
| mismatched-database | 1 | AUTHORITY_MIGRATION_GRANT_NATIVE_ID | 0 |
| release-pin-mismatch | 1 | AUTHORITY_RAW_PIN_MISMATCH | 0 |
| expired-grant | 1 | AUTHORITY_MIGRATION_GRANT | 0 |
| missing-dynamic-pin | 1 | AUTHORITY_MIGRATION_REQUIRED_RAW_PIN_ABSENT | 0 |
| wrong-owner | 1 | FORBIDDEN: current project Owner required | 0 |
| lease-occupied | 1 | The process cannot access the file because it is being used by another process. | 0 |

保留旧失败、停止observer及静态修正记录。inner native Job ID仍未独立观测；Root调用的release基线与独立observer实际terminal/closure在索引中分别标注。
