## Review Summary

**Verdict:** REQUEST CHANGES。

**Overview:** 模板保留了 HEAD 前进、关闭旧 lease、追加原始失败与保护 ST/CM、正式状态的边界。合法 prepare 路径目前必然失败；runtime catalog 还缺同源绑定。

### Critical Issues
- [forward_head_engine.selected.proposed.py:434] 裸子串 `MODE = 'register'` 在真实 assignment:17 和源码中的 bytes 字面量:164/:434/:443 共出现4次，count==1 永远失败，尚未到 mkdir:437。统一使用含实际换行的完整 assignment 锚点进行计数、三 mode 派生及 setup 校验。

### Important Issues
- [forward_head_engine.selected.proposed.py:372] runtime 只核1212条，在:375–378批准外部路径；closure:281–282绑定旧 scope 的 status/toolchain/helper，却没有绑定 runtime_resources_ref。加入 same(scope['runtime_resources_ref'], q['runtime_resources_ref'])，保留数量与 loaded 检查。实际 scope 的旧 catalog 为 c75ee385bdca56de3582f78695af8fc1b31fb67da0ecffa22cd1e4b4aca4b9b5 /282833B。

### Suggestions
无。

### What's Done Well
每次 replace 前在 source_guard 后再检查全部4份 canonical，结束也再查4份。grant 模式与 active scope materialization 已删除，旧失败前缀、formal、ST/CM 保持。

### Verification Story
- Tests reviewed: 12 条声明用例均 NOT_RUN；实际源码裸锚点计数4、完整行计数1仅为纯IO字面量事实。
- Build verified: 否；未 import 或执行候选。完整662行 engine 与25行 builder 已读。
- 29 hunk 原字节逆变换恢复冻结 r332 原稿；14 个既有函数 AST 保持。30 包成员与12原输入无 SHA/bytes 漂移。
- Root final request ref 尚未给出；旧模板合法正向 prepare 仍被 Critical 阻断。
- 唯一新 origin 是 V8 解析截断输出失败，数值 outer/native NULL/NULL；底层 af2be6 为0/0，不另计。原09b17d已在固定8cut，不重计。
- source acceptance、fresh58、GUI、NVDA、SQL24、正式增量均未提升；无 canonical 写入。

