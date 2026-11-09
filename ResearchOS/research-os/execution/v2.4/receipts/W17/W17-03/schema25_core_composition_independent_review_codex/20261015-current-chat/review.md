# 四支组合独立 Source 审查

结论：**LIMITED_COMPOSED_SOURCE_ACCEPTANCE_WITH_OPEN_BASELINE_FIXTURE_FAILURE**。候选 `2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02`，tree `ad73440fdc98416687a75a8cb3ff23eff2cb0253`。接受范围为 Main4f 上精确53文件的源码组合及限定夹具证据；历史 source22 fixture 失败保持 OPEN，不能称全部测试通过。

## 范围与保护

独立比对36,201个Git树条目、完整patch、53个文件的Git/工作区字节、四阶段前置blob和接受输入。唯一交叉 backup.go 保持 f809最终字节；storage9→Native22→Core21→Bridge2顺序正确。178个证据引用通过哈希核验，包含29个作者命令回执和20个Host嵌套证据文件。5个二进制记录均绑定本候选且 vcs.modified=false。

Main仍4f、20项tracked dirty、index为空；Main10保护文件与候选一致。原9按preflight-v2冻结的Main工作字节校验，无覆盖；候选不继承Main未提交修改。project_identity未变化。未写Source/Main/shared状态或产品数据。

## 生产边界与新验证

control主入口保持verifier dispatcher优先，其后Native私有入口必须验证继承authority；普通启动lease→verifier历史gate→store.Open顺序不变。backup同时绑定schema25验证和Native pause handoff，未把私有preserve callback扩成普通备份绕行。CheckMigrationSafety继续阻止已有24自动升25。Bridge legacy分支不能由V1降级进入。

作者T5实际12项与此前13项不是同一集合，漏了 TestW12BudgetLeaseTakeover 和 TestCompletedRuntimeLocalLaunchRelease。本审查在同一clean候选新跑两项，2PASS/0FAIL/0SKIP；没有把旧候选PASS当作新证据。

另以只读Go overlay加入两个独立测试，2PASS/0FAIL/0SKIP：schema25下verifier replacement仍以supported schema24 required拒绝、不改DB也不创建plan；在隔离schema24 fixture提交合法replacement后加入schema25标记，合法终态历史可通过startup gate，登记漂移仍被拦截且DB未改。这验证门禁关系，不是完整schema25迁移或安装证明。

新执行共2命令、4顶层PASS；已有T1–T7的29回执作为作者证据复核，不改称独立重跑。Host模型／工具第二暂停证据均为17秒等待、heartbeat推进、2暂停/2激活、同attempt1、live_model_calls=0的native synthetic轨迹，不能推导实际提供商资格。

## 未关闭项

- T3初始37PASS/3FAIL原样保留；两项历史程序资源失败补齐29项pin后各PASS。ActiveQueueRecovery在候选与cleanMain4f同145行因source22缺client_command_identities失败；该23表不属于22 fixture，历史支路保持OPEN，本审查未修改fixture或宣称其接受。
- Queue初始1PASS/2SKIP保留；同候选补资源新attempt为3PASS/0SKIP。
- 未执行T8新候选签名/pin授权、实际原库迁移、package安装或Desktop资格。旧f809授权不能复用为组合授权。Root现有Main4f资格运行MODEL1 HTTP200但TOOLrequest1拒绝、actualTOOL0、RunRUNNING/dispatchUNKNOWN，单独诊断中；本审查未读取或重放现场。
- 审查工具两次诊断失败已保留：patch格式参数不一致、非Go输出JSON标量解析；修正后审计通过，均非产品测试失败。历史清理拒绝、失败次数和62缺树状态未重置。仅清理本审查空scratch目录。

formal_increment=0；0/42；全部22父任务open。审查不签发Main整合、部署或实际迁移授权。
