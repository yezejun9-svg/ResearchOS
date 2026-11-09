# 合同样例与施工模板

这些文件帮助实现协议和准备测试，全部是开发夹具或空模板，不是产品已通过的证据。

| 文件 | 用法 |
|---|---|
| contract_fixtures.json | 8个正反例，检查预算、并发、证据和未运行验收回执的格式 |
| evaluation_contract_fixtures.json | 5个评测报告正反例，覆盖失败候选仍可完整报告、留出权限、硬门与零样本 |
| evaluation_smoke_cases.json | 12条有冻结标签的开发协议夹具及额外故障；不是正式Jev资格集 |
| bootstrap_ledger.template.json | W00施工台账模板；外部Verifier维护施工接受记录 |
| execution_receipt.template.json | 每任务实际执行回执起点；按任务合同补齐命令、证据和独立验证 |

带examples数组的文件中，每项value按schema_definition指向的domain.schema.json中$defs检查；外层目录不是API请求体。expected_valid=false表示必须拒绝的输入。measurement_mode=FIXTURE仅说明数据来源，不能冒充LIVE。

smoke中的expected_decision是人工预先定义的公开开发标签。expected_handling是协议对故障或结果的处理：正确识别ERROR/ABSTAIN/INVALID/MISSING可让协议断言通过，但不能计成模型判对或获得自动资格。模拟输出不构成真实provider调用。正式A08仍须独立留出、真实模型、完整资格键和规定的样本数、阈值。

固定时间和重复字符hash是明显的样例值，不能当真实摘要。实现必须重算hash、核验关联记录、权限、输入版本及身份，并验证跨字段计数等业务不变量。正例AcceptanceReceipt刻意保留BLOCKED/NOT_RUN。

两个施工模板不是domain实体，不能直接POST为产品状态。空数组和null必须由实际观测补齐；状态由真实执行和外部验证产生，原始规格目录保持只读。PACKAGE_VALIDATION仅报告规格检查，产品用例仍保持NOT_RUN。
