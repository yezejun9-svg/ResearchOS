v9 runner 窄范围独立 Source 审查

结论 READY_SOURCE_ONLY，仅针对 v8 到 v9 的 write_paths 空对象改空数组。完整正逆向字节验证通过，作者 diff 独立重新生成一致，另外 39 个函数完整字节、全部顶层赋值、模板不变。前次 v8 独审 47 项结果复用，未重跑。

当前 Main internal/host/runtime_tools_windows.go:205-219 要求 policy[key].([]any)，空对象拒绝。独立从原始 AST 抽取 policy require 条件，8/8 控制符合预期：合法 policy 通过，空对象、非空 write_paths、其他 read_path、第二个 read_path、max_calls=2、max_read_bytes=4097、max_write_bytes=4097 均拒绝。未导入候选模块，未运行完整 validate_input/main 或作者控制。

18 条输入读取记录封存复核无漂移，详见 audit.json 与原始字节快照。本轮两次工具失败：690 查询不存在的 internal/runtime，shell exit=1、Python/native NULL；691 functions.exec JavaScript 解析失败，执行前失败，shell/Python/native exit 均 NULL，无文件修改。两次完整原始调用和输出分别封存，未当成产品/provider 失败。

整条链保持 OPEN：Controller C4 和 Observer O3 尚待独审，O2 的 literal RUNNER_REF 仍绑定 v8，不能与 v9 拼接成 READY。真实 Job 生命周期、Host、provider trial、qualification、formal acceptance 未执行或批准。所有写入限本审查 namespace，Main/canonical/SQL/WinAPI/产品 native/provider 均未触碰。

