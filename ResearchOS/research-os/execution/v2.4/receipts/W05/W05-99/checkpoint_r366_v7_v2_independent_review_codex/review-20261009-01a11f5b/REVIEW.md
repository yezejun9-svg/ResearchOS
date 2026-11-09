# CP366 writer v2 独立 Source 审查

结论：REQUEST_CHANGES。

P1：L156–159 只按路径匹配四个 Source/Review 引用；owner 与 scope 可以同步填入错误 sha256 或 bytes，仍与已验证 facts.reviews 路径匹配。8 个同路径错摘要/大小反例全部被接受。应成对比较完整 path/sha256/bytes 字典。

v1 的四个攻击、scope 互换、字段注入、权限修改和 scope-owner 引用不一致均被拒绝；合法固定路径 baseline 通过，旧 923 条与其他 worker 保留。四 Canon pins 未变。

仅执行 AST 提取的纯内存 transform；verify 是显式 inert stub，future facts 为合成输入。未执行 main、guard、native、canonical writer。actual facts/scope/Caller 绑定待补审。formal_acceptance=false；execution_grant=false。
