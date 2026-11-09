Root并行审查消息（2026-10-15，本作者未复跑）：STOP-r3 fresh overlay发现Everyone FULL_ACCESS祖先/finalimage仍可被Observe/OpenRetained/verify接受，ancestor held时仍可开WRITE handle；尚无恶意替换事实，review拟NEEDS_CHANGES。B private DACL亦有待复现疑点。

本提案不把STOP/B这些未接受helper视为已接受严格原语，不继承其ACL安全结论。未来boot_windows.go必须逐ACE和有效token/ancestor/native identity验证；如复用依赖，先固定其修复后独立接受的版本。复用需要新增路径时停止57路径卡，不暗改范围。具体证据以各独立审查最终清单为准，本注不是接受或新缺陷复现报告。
