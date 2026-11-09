v4 独立源码审查：REQUEST_CHANGES，尚不能用于 CP370 后的实际调用。

1. Canon 的实际 Owner/Worker/lease 唯一登记未检查；空登记、冲突登记和过期独立文档均可通过 root_request。
2. 独审决定缺少 schema/actor_role/源 HDF、MF、caller、contract 精确绑定，scope reviewer 与 decision reviewer 也未一致核验；actor_id 合同与 reviewer_id 实现不一致。
3. Scope 禁止未来 vector/request/proof 引用的循环约束仅为合同文字，当前实现接收这些额外字段。

历史 CP369 四档案与 Native 原 hash/bytes 相符；Main source21 与六个已采用源码成员已验证，其他通过项及当前 registry 连续性限制见 source-analysis.json。独立反例只在内存中调用 AST 提取的纯函数，不构造实际授权、不执行 execute，不运行 Native/dispatcher/provider。SourceGuard closed、retained=0。正式验收增量 0；原 Source v1–v4 均未改动。
