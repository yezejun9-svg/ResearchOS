# W09 v7 fragment parser 独立 Source 复核

结论：**SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS**。本次未发现 v7 差异中的阻断缺陷。1505 项独立检查通过；130 个固定输入在复核前、真实持有 SourceReadGuard 期间及复核后保持一致。guard 的实际关闭记录见 source-guard.cleanup.json；本报告不把模拟 guard 当真实 OS 持有。

本结论只接受 v7 的 Source 改动。没有运行完整 verify_native、consumer/router、Native/Go/Git/SQL/API/model，也没有改动 Main、canonical、原 packet 或原 report；正式验收数量不变。CP365/OW169 与另外两个 canonical 输入保持原 pin。

## 差异与保留的校验

候选 w09_evidence_closure.v7.proposed.py：1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777 / 42716 bytes。基线 v6：2989eb2c89a0647cf9bf9fb99841dcb8e943d64c6dd84d0a0fe7bca4b9568eec / 42128 bytes。

独立读取 AST 定位 v6 assertions 初始化与输出循环，提取其原始字节；删除 v7 新 helper 并把唯一新调用恢复为旧块后，整个文件逐字节等于原 v6。独立完整模块 AST 逆变换同样相等；所有其它函数 AST 相等。作者 provenance 的全部 opcode 拼接也分别精确重建原/新文件。由此确认差异仅为新增 _go_assertions 和 verify_native 中的一次调用替换。

原生测试 pass 名单、fail/skip/foreign terminal 拒绝、assertion 顺序和值/数量/ID/run/status、Go lock 与 actual invocation、Source hash closure、owned exports、C19/A06 与 ModeDecision 检查均保留。没有执行这些函数的 I/O/产品流程来假装完整消费；实际执行仅为内存提取的纯 parser 与 events-to-assertions 原样前缀。

## 原始失败数据的独立验证

原 stdout：dedec7ea37a965791be5f11b9984e21cf779f8486b784fbae4c07ca062bf4930 / 10560 bytes，共29个 JSONL events。原 report：1595d62b4e5f3f1395a8882243e878996eb43f71fa557bdb5baf330cd2bf439a / 149654 bytes。

重组得到5条断言，与原 report：
- Python 对象相等；
- 独立递归核对值与实际类型相等；
- 排序键、完整精度、禁止 NaN 的 canonical JSON 相等。

原 C19-05 横跨 events[22]/events[23]；独立遍历该完整行全部1303个切分位置，每种重组都精确恢复原5条断言。v6 对原分片的 JSONDecodeError 只作为捕获的纯函数负对照，不是新 consumer 失败或新实际试跑。已有失败927保留原文，未改号或覆盖。

## 边界检查

| 情形 | 结果 |
|---|---|
| 同 owner 任意切分、逐字符、空/缺失 Output、多完整行 | 保真 |
| 不同 Test 交错，后开始行先完成 | 按完整行实际完成顺序返回 |
| Package/Test 分片混接 | 因未完成 owner tail 拒绝，未跨 owner 拼接 |
| 原 Test 与 JSON test_name 不符、未选 Test、非文本 owner/output | 拒绝 |
| 部分 marker/JSON、完整 JSON 无 LF、普通日志尾段、CR-only、Unicode separator 代替 LF | 拒绝 |
| malformed JSON、截断后 LF、JSON 字符串内裸 CR、同一行两个 JSON | 拒绝 |
| CRLF（包括 CR/LF 分在两个 fragment）、Unicode separator 在 JSON 字符串内 | 保真 |
| 正负大整数超出 2^53 | 保持 Python 整数精度，无浮点往返 |
| report 顺序或 ID/status/run_id 改动、重复 pass、fail/skip/foreign terminal | 原校验拒绝 |

helper 以精确 (Package, Test) 缓存，只处理 LF 完整行，所有非空尾段一律拒绝。不会使用 splitlines 把 JSON 字符串中的 Unicode separator 当作逻辑输出行分隔符。verify_native 对外层 JSONL 的旧解析方式未改变；本结论不新增对任意非标准外层 JSONL 的兼容承诺。

两个既有边界需明确：完整 assertion 行的 Package 值没有白名单校验，v6/v7 都如此；新增隔离只保证不跨 Package/Test 组装。独立对照已证实它不是新放宽，现有真实 native packet、不可变 report 和来源 pin 仍是外围信任依据。其次，原 verify_native 使用 Python ==，不是对任意 bool/int/float 的类型严格判等；本轮对实际五条记录额外做了类型敏感核对，但没有声称产品新增该类型门。

## 后续约束

闭包 Source 变更属于 producer Source21/version_manifest 的一部分。Root 后续必须使用新的 producer packet、独立 consumer namespace 与绑定新 run/来源的非作者 ModeDecision；旧 v6 packet/report 保持历史原样。不得仅替换 closure 文件后用旧 packet 承诺完整 current Source 验收。本复核不创设新调用、注册、Main adoption 或 formal authority。

作者 MF 的14个确切成员、114个准备输入及新增复核输入全部核验。作者181项 controls 和两份实际 guard cleanup 的 closed/verified/final-path/retained 状态检查通过。独立实际 SourceReadGuard 使用既有固定 hash e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85；仅取得只读文件句柄，复核结束全部释放。无新增原始失败。STOP_FINAL。

