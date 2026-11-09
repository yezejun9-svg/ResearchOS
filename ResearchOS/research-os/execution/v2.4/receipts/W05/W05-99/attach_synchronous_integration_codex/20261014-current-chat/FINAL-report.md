# Core attach exact6 独立复核

结论：**APPROVE_LIMITED_SCOPE**。限定候选 `b955c8665281193d5cbf90a146f936c9212c7940`、tree `00d44e133662227b115eb3b16bef3d4edcc35630`，基线 `91218bdd3901bae94a2c1c90521a4d133c59026d`。P1=0，P2=0，不需要扩大修复范围。模型按主 Agent 确认的实际调度配置记录为 gpt-6-astra / high。

项目授权删除或收窄到 Task 后，global OWNER/token 仍有效时，旧 COMPLETED 与 ACK 的四种 HTTP 重放均返回 403 FORBIDDEN，writer 和不可变 journal 字节不变。有效授权下重复请求仍为原字节。Execute 提前 replay 是继承且受保护的实现；实际 HTTP 入口的当前 project grant guard 已拦截本次待决情景。直接进程内 Execute 没有因此获得独立权限边界资格。

独立原 native 运行 exit=0，15 个顶层测试通过。新增 overlay 复核 exit=0，3 个顶层、15 个叶子子例通过。首次稀疏缺 evaluation 的 exit=1、补测首轮夹具错误的 exit=1 全部保留；夹具错误分别为 revision=0 不符合 schema 和 ACK 私有头规范顺序不符，修复仅发生在新增证据文件。

六文件逐字节匹配作者 manifest、candidate 和 commit；34 个原测试/辅助函数及受保护生产函数保持不变，包含 control、rollback、session.list、Execute 和通用读取。实际 -work -x 记录了 367 次 compile.exe、2363 个唯一 Go 输入，缺失 0，六文件均出现在真实编译命令中。author 的 go list 3854 仅为潜在依赖清单。compiler、importcfg、embedcfg 及嵌入文件另有 hash 清单。

新命令同步 attach 完成返回 COMPLETED；普通同 client 续约不增加 epoch/revision/event；过期异 client 授权为 epoch+1、revision+2、一个 handoff；旧 ACK 永久保持原响应。失败回滚、未结算历史 Run、active Run 下同 writer 续约、恢复 fence 等边界已复核。

此结论只授予有限 source/local-native/fixture-HTTP 复核通过。当前原 Desktop 会话、新干净包激活、live provider、完整 B22 和全部 22/42 正式接受均不由本报告完成。formal_increment=0，all22_42_remain_open=true。Root 可以依原授权串行整合精确六文件并继续真实主流程。本复核没有修改 Root Canon 或接受任务。

关键证据：`resume-source-audit.json`、`resume-protected-production-functions.json`、`resume-actual-compiler-census.json`、`resume-compiler-config-embed.json`、`independent-native.*`、`resume-attempt02-independent.*`。全部原始命令、环境、native exit 和新旧失败均纳入 FINAL-manifest.json。
