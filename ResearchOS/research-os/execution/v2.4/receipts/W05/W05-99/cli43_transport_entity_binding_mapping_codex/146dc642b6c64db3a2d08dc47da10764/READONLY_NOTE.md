已核：captured9/upstream12，含3条 setup，captured index 不能直接用作 HTTP sequence。两个空 raw 的 raw_base64 为 JSON null，空 SHA相同，不能凭它们决定 GET或路径。

Root 最小修正应在原 capture 同一 mutex 同时追加 method、RequestURI 与 raw，显式传 helper，按该 metadata 分类。仅非空 POST /v2/command 继续原全部 CommandResponse/SID/project/readonly/snapshot assertions。仅空 body GET 进入确切本项目 Goal/Task 路径，再用真实实体 schema 校验完整响应并绑定 id/project_id；其他方法、路径、body或未知schema拒绝。

真实已读 validator 为 internal/domain/contracts.go:143 Contracts.Validate、:174 LoadContracts；api/v2.go:52 ClientProtocolDocument 仍用于 CommandResponse，本轮未证明它直接公开 Goal/Task defs。Root 指定 internal/api/contracts.go 当前不存在，仅 Test-Path 得 false（5f232e outer0），没有读取内容，不能捏造 API export。具体函数、字段流、实际路径和来源行见 mapping.json。

三条 reviewer metadata origins：04e374 rg2/2（误列cmd）、1285e0 rg2/2（误列handler.go）、8a5f6a Python1/1（null base64 shape）。原命令/错误每条保留一次，不重跑、不重计旧失败。停止后没有继续诊断，只做已授权路径存在性读取和封存。

源码、Main/canonical、计数无写；Go/SQL/网络/目标执行0，正式增量0。STOPPED。

