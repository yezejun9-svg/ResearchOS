# Mainv2 scope type contract — Source only

修复 CP367-V3-P1-CROSS-CALLER-INT-BOOL：七个布尔开关要求 is False；formal_case_accepted_delta 和 new_Go_SQL_API_model_calls 要求 type(value) is int 且 == 0。

本包仅修改 caller 固定 namespace 与上述谓词；完整字节 inverse 同时保留 caller 以及 change-set/contract 的原、新全文和 spans。七个最终目标 bytes、六个 sealed Source refs、commands.proposed.json、四个完整 before archive 及 commands 完整 inverse 均保持原样。旧 Source 包和其独审结论未修改。

本轮 113 个新纯 Source 控制 PASS，208 个旧输入 exact pin 不变。真实 Root registration facts_scope、validate_live_context、transform 与 Mainv2 完整 validate_scope 通过同一内存 scope/owner/worker/CP/OW/vector 串接；旧谓词 P1 被内存反例复现。计数的 false/true、0.0/-0.0、正负非零整数、字符串、null、缺失均被两端拒绝；非 boolean-false 开关与绑定/角色错误同样拒绝。未来 Root/reviewer 文档仅存在于内存，未落盘。旧 471 控制只是历史结果，不计为本包新通过。

准备、控制、封存各自使用真实 SourceReadGuard 并完整关闭；Main/commands/CP/OW/SS 未写入，七个目标仍为 before，未执行 adoption、dispatcher、Git、Go、SQL、API、model。actual-adoption 目录不存在。无新的原始工具失败。

Root 后续必须绑定本包新的 HDF/MF/contract/caller/change-set 和新的独立 Source 决策，再更新 registration facts/Root scope；旧 scope 或旧 Source reviewer 的接受不能直接作为本包的执行授权。当前 canon 仍是 CP366/OW170。

范围外后续：旧候选 native packet 的 assertion 和嵌套 raw pins 固化候选绝对路径，Source21 相同不能自动证明 Main 原样消费可用。此包不复制或重写旧 packet，不执行 Main producer 或正式消费者。formal_case_accepted_delta = 0，W09 parent acceptance 不变。
