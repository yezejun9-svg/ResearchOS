# Review Summary

**Verdict:** REQUEST CHANGES.

**Overview:** current58 source/CLI2/registration/finite Root scope 接口总体可组合，33 包成员+27 原 inputs 重哈希无漂移，6 个既有 pure IO 定义 bytes/AST 与整份 inverse 成立。当前 runtime observation 空列表路径仍可返回完整 authority，因此 source preparation 暂不批准。

### Critical Issues

无。

### Important Issues

- authorization_adapter.final.proposed.py:611，`validate_grant` 直接遍历 `grant['runtime_observation_refs']`。否则完整合法 grant 的该字段为 `[]` 时跳过613–624全部检查，在633返回 `registered_Root_scope_and_grant_verified=True`。至少要求非空 list、唯一 exact refs，并把 Root 冻结的有序 observation paths/roles 或 exact refs 与 grant 精确配对；缺失/重复/陌生项明确拒绝。保留点时语义。新增字段只作提案，需 Root 采用。

### Suggestions

无。

### What's Done Well

6ff source predicate 原字节/AST保留；旧 a510 立即拒绝。scope/lease/review/resource/budget NULL 均不能取得执行资格。原 controller/launcher ABI、once exclusive allocation 和25/5/IO reserves 保留。

### Verification Story

Tests reviewed: 16 项 future controls 全 NOT_RUN；实读旧 r331 qualification/review/result 与3 MF，仅用于 schema witness，未运行或继承旧资格。

Build verified: no；只用 pure IO/AST，无 candidate import/call。

Security checked: same-head/catalog/run/fullscope/copies/registration/lease/limits 与权限边界；R01 是实际空集合缺口。Root 新 producer、resource normalization、fullscope、grant 和资格均 OPEN，不自行采用新 schema。

本轮没有数字非零 metadata/native调用；一次发往已STOPPED Cmd 的通信被 threadlimit 拒绝，outer/native NULL，原 input/result 单独封存，留在固定532cut之后。它与 Root 自己的另一调用不同，不合并计数。产品、Git、canonical writes 均0。
