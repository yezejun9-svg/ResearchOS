## Review Summary

**Verdict: REQUEST CHANGES**

R01、R03 已在源码层闭合，R02 仍有一个 terminal tool provenance 残余。实际执行、Root grant 和 A01–A07 继续 OPEN。

### Critical Issues

无已确认 Critical。

### Important Issues

- **R02-T01 — authority_adapter.v2.final.proposed.py:383，outer_completion**：初始 session 与 `tool_completion_session_id` 相等只验证新 envelope 字段；terminal 原回执只核 `exit_code==0`，未读取实际 wait/poll 的原始输入，不能拒绝其他 action 的成功回执。需增加实际 terminal tool invocation/input 的 exact ref，核实际 session、tool/action 与对应 response ref，再与 `tool_result_ref` 及 initial 原件配对。原生退出码没有桥时仍 NULL，不能生成替代事实。最小反例集合见 review.json，均 NOT_RUN。

### Suggestions

- **authority_adapter.v2.final.proposed.py:383**：目前要求 initial 为异步 session。Root 必须使用真实的该形状，或另审真实同步完成分支；不得补造 session ID。

### What's Done Well

R01 的大小写保护与复制后 1899 pristine 检查已具体实现。R02 的完整 18 roster、严格数值类型、完整 prepared closure、原 launcher raw 与完整 manifests 已补齐。R03 绑定当前 scope/draft/四份 canonical/lease 和完整 child、wrapper 参数，预执行 audit 与最终 audit 分开，避免 review 哈希循环。

### Verification Story

- Tests reviewed：15 个新控制均 NOT_RUN；I16 producer/probe、原 driver18 与 I18 regression 字节实际核验，语义复用旧独审。
- Build verified：否。仅三源 Python AST/source IO，未 import/execute；无 Go、SQL、网络、CAS。
- Security checked：静态路径、原件/hash、独审/注册/prepare/tool 数据关系。
- 作者 31 成员、22 原 inputs、a03c 15 原 members 及必要 fixed refs，共 59 unique public refs：0 mismatch、0 drift。
- 三个 selected final 源的每个编辑 forward/inverse 都单次匹配，完整反向字节与原件相同；未改函数 AST 相同。controller 仅新增 post-copy inventory；caps、30 calls、partial17、I16/I18 路径原样。
- 新增失败 0。旧 REQUEST、旧 origin 和 Main/canonical 均未写；I17/full18/SQL24 与完整 callback 仍 OPEN。

