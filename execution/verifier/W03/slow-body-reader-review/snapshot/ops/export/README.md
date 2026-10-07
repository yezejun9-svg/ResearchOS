# 可移植导出

`go run ./ops/backup export --db <existing-db> --out <new-directory> --key-file <separate-key>` 使用相同一致性及加密规则，输出 `portable.json.enc`、逐份封存内容、权威数据库和认证清单。portable JSON 保存完整实体版本、ID、revision、来源引用及 receipt hash；恢复仍以包内 SQLite 权威状态为准，避免仅导出部分对象后丢失费用/幂等/outbox 关系。密钥不进入导出包。
