# Workspace projection 独立审查

结论：ACCEPT，范围仅 SOURCE_AND_LOCAL_NATIVE_HTTP_FIXTURE_ONLY。候选 cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8，基线 1004cf9b8414ee4a248301ead447bc4a022f87d7。无新增 actionable findings。

23 项输入绑定通过；记录并复核 642 个执行相关源文件。独立重放作者 2 个投影测试与 1 个实际 Windows Host/SID HTTP 流程，另用仅新增测试的 Go overlay 运行 16 个边界子例，全部通过。覆盖事务内状态、principal/project/grant、远端隔离、READ_ONLY、REVOKED、损坏记录、1000/1001、七字段协议、envelope、fresh/replay 和 DB 失败。

HTTP 快照确认只有 1 个 offline Session，其 principal/project/workspace 与新投影一致，Task/Run/resource_effects 均 0，未资格化发送 REJECTED。实际 Windows Host/SID 与认证 HTTP 已运行；native chooser 是确定性测试回调，没有实际 Root GUI 验收。

作者保留的两个扩展旧回归失败在精确 base 同现；本审查核对证据哈希，未再次复跑或修旧测试。未整套重跑 Go，未重建 Desktop。Source、Canon、Main、Root 真实数据未修改；真实 model/tool 为 0；parent/42 正式验收增量为 0。Root 唯一负责整合和真实界面重试。

自动审批拒绝了本次自有 go-cache/go-tmp/test-tmp 清理，原因 blocked by policy；目录保留并从证据清单排除，没有绕过。首次验证脚本路径层级计算错误在测试前报错，纠正后所有绑定通过。
