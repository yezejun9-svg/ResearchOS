# Windows nonce barrier：独立安全合同审查

结论：**CONDITIONAL_SOURCE_CONTRACT_ACCEPTED**。可以进入另行授权的源码实现及 fake/RPC conformance 审查；不代表实现完成、实际 MXC 资格成立或可运行模型。Slice A production exec 的 UNVERIFIED 门不变。

审查对象为 d95a/CONTRACT.md，SHA256 633b031167eca2494ff3c012469e109bb2f554a711422ff018bcaea27e987e07。以下限定作为实现合同的必要补充。未修改该冻结文件。

## 冻结选择：无 override 的首个 turn

采用新鲜 Native 进程、独占 stdio、唯一新线程；不使用 resume/fork/reconnect，不启用远程或 owner-provided 环境。仅正常本地 FromThread 环境。Host 只发送固定 initialize/initialized、thread/start、唯一 turn/start 及正常取消/关闭；不转发 renderer 任意 RPC。禁止 settings/update、environment ready/change、注入工具结果和任何额外权限 grant。非预期 server request 不可默认批准。

thread/start 完成后验证实际线程 ID、nonce ID、extends 空、固定 cwd、精确预期 runtime roots、ReadOnly/network=false、approval=never、必要实验字段和完整启动诊断。Host 独占这次接入且只允许一个 prompt；没有通过全部门时 prompt 字节数必须为零。

首个 turn/start 只含 Host 固定 threadId 与本次已授权 input；不含 permissions、sandboxPolicy、cwd、runtimeWorkspaceRoots、environments、model、approvalPolicy、approvalsReviewer、collaborationMode、动态工具或其他配置字段。此处选择保持现有快照，**不选显式 permissions 再解析方案**，避免把旧快照和新配置解析混用。模型参数应在 thread/start 的固定 Host 配置中一次冻结。

## 独立核对后的支持链

1. profile catalog 以精确字符串查找，不用 wildcard，也无隐式父 profile。独立 CSPRNG 128 bit nonce 且不复用，在非恶意同用户并发改配置的边界内排除预存静态同名额外键。概率保证应准确记述，不称数学上零碰撞；RNG 失败停止，不能回退固定名。
2. 正常 Windows loader 无 injected managed_config_path 时忽略 legacy managed_config 的内容；macOS MDM 不适用。memories.use_memories=false 的 SessionFlags scalar 覆盖普通低层值；即使 managed feature pin 把 features.memories 变为 true，memory-root 追加的 AND 条件仍为 false。这不证明所有 Native memory/context 行为关闭。
3. thread/start 的 active ID 来自实际 config_snapshot；named selection fallback 改名、约束 fallback 清 ID 均不能满足 nonce 比较。原生同名 managed profile 冲突报错。还必须核 coarse sandbox/network/approval 字段，不能仅比较字符串。
4. app-server turn_processor 对省略 cwd/roots/environments 返回默认环境 override；省略权限字段不调用 load_permission_config_for_thread。
5. Core PreparedTurnInputSettings 对默认 ThreadSettingsOverrides 记录 None。SessionConfiguration::apply 克隆现状，仅 Some 权限或环境字段才进入变更路径。新 turn 从保存会话状态构造；build_per_turn_config 克隆原 config 并回填保存的 permission_profile_state。正常 FromThread 环境由同一 thread defaults 产生；不采用 Pending/外部 owner 配置分支。
6. 已查 runtime config refresh 克隆原 config，只更新声明的 MCP/plugin 等运行状态，没有重新编译会话 permission_profile_state。此结论限定固定单线程本地路线，不覆盖任意嵌入式扩展或额外 RPC。
7. Native session 启动先 validate_windows_mxc_requirement，并从固定 config 派生本地 Windows sandbox 类型。无 override 路线保持该选择；真实 OS 可用性与执行效果仍需独立资格验证。

这构成可实现的“实际 ID + 固定构造不变量”候选；不以缺少完整图字段为由否定它。它也没有为同用户恶意改配置、源码/二进制不一致或任意未来版本提供隔离证明。

## helper 与输出屏障的必要约束

正常 arg0 在启动 runtime 线程前完成 setup，成功时 prepends fresh tmp/arg0-windows/codex-arg0* 目录并保持 guard。仅此目录的 apply_patch.bat/applypatch.bat 与 lock 的读取例外可纳入明确 Native runtime 最小契约；它是 :minimal 之外的实现追加，不得命名为“整个缓存可读”。

setup 失败的 warning 在主 runtime 启动前同步 eprintln。把 stdout/stderr 接到**同一个实际 OS pipe 写端**、stdin 独立，可使这些先前写入的字节必经同一顺序解析器后才处理 thread/start 响应。两个独立 pipe 再由 Go reader 合流不满足条件。分块、行拆分、JSON/诊断交织、编码失败、溢出、写盘失败、非预期协议、重复响应都必须 fail closed。不得截断后跳到下一个合法 JSON 再放行。

额外路径条件：arg0 path_env_with_entry 手工以分号串联 PATH，后续用 split_paths。Host 固定正常 home 来源/USERPROFILE，禁止 CODEX_HOME 注入，并要求构成 fresh helper 父路径的 home 不含 PATH 分隔符分号；否则即便 setup 成功，也未证明解析到 fresh entry 而不是继承旧目录。当前标准固定 home 路径满足此形状；本审查未读取私有 home/helper 内容。不得扩展成任意前缀匹配目录都可信。不存在的/非标准路径或不确定来源应阻止准入。

屏障保证的是首个 Host prompt 之前的启动检查。若之后出现异常，立即走已有正常取消/终态流程，不能改 profile、换 ID 或自动重试。原 f13 Job 边界和审计不可被新 transport 替换。

## Native context 与计量

thread/start 可以在响应前做 Responses websocket prewarm；源码注明 generate=false，并构造 base instructions/tools。因此“未发 turn”不等于零外部 API、零上下文传输或零认证活动。保持既有 D03 PLATFORM_POLICY 限制，不能宣称 thread/start 是纯离线 probe。需要任何真实连接/协议验证时，Root 必须按对应范围另行登记；本审查未发任何 RPC。

生产资格还需新独立预算的 synthetic filesystem/network 有限观察与 Host-owned evidence；probe/TTL/renderer receipt 不能自动生成 READY。旧 Echo 2/2 与旧 FAILED Task 不得复用。

## 实现必须证明的测试

- nonce RNG 失败、重复/畸形/外部注入、lower fixed-name grants、managed fallback、非空 extends 和缺字段均不发 prompt。
- 单写端 OS pipe 的 fake 子进程：warning 分片、无换行、与 JSON 交织、超限/编码/IO失败、重复或错 ID；证明失败后的 prompt_bytes=0。单纯伪造两个 reader 回调不能验证 OS pipe 接线。
- 精确同一线程快照通过时只发一次冻结 turn；捕获输出不得丢原诊断。任意 settings/environment/reconnect 注入均失效，不产生另一 Task/Run/ID。
- 保持原 Job cleanup、source/helper/template pins 和真实来源 seal；fake PASS 永远不是生产资格。
- 独立真实固定合成测试另行授权；不得用当前合同直接调用 Native。

## 公开源码定位

均为 OpenAI rust-v0.166.0；行号按原始文件物理行。安装二进制与公开源码是版本/hash关联，不是可复现构建证明。

- [arg0/lib.rs:136](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/arg0/src/lib.rs#L136)、[同文件:341](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/arg0/src/lib.rs#L341)、[同文件:451](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/arg0/src/lib.rs#L451)：同步 setup、guard 和 PATH 串联。
- [layer_io.rs:65](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/config/src/loader/layer_io.rs#L65)：Windows legacy 条件。
- [turn_processor.rs:719](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/turn_processor.rs#L719)：省略 override。
- [turn_input.rs:103](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/turn_input.rs#L103)、[session.rs:411](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/session.rs#L411)：默认更新与克隆。
- [turn_context.rs:949](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/turn_context.rs#L949)、[同文件:1182](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/turn_context.rs#L1182)：下一 turn 保存权限。
- [environment_selection.rs:120](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/environment_selection.rs#L120)、[同文件:224](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/environment_selection.rs#L224)：FromThread 默认。
- [runtime_refresh.rs:127](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/runtime_refresh.rs#L127)：保留原配置的运行刷新。
- [session/mod.rs:607](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/mod.rs#L607)：启动 MXC requirement 检查。
- [startup_prewarm.rs:374](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/startup_prewarm.rs#L374)：generate=false 预热及上下文边界。

formal_increment=0；product_increment=0；native_invocations=0；model_invocations=0；execution_scope_created=false；D_writes=0。

