# CP663：同一 Native 进程权限屏障的定向结论

结论：**当前接入仍 BLOCKED；app-server 是候选，不是已证明不可行。** 本次没有 CLI、模型、echo、probe、配置读取或执行 scope。只审查公开源码和已授权产品源码。

## 已证明的正向事实

- pinned rust-v0.166.0 的 thread/start 响应从创建后的 thread.config_snapshot 取 active_permission_profile；不是请求 ID 回显。Host 可以在同一进程/线程收到该响应后才发送首个 turn。
- 显式 thread/settings/update 或 turn/start.permissions 在重新解析配置后检查 permission_profile disallowed 的 startup warning，并在接受 turn 输入前拒绝。settings/update 的响应只表示排队，必须等实际 settings/updated，不能把空响应当完成。
- managed requirements 定义与普通配置定义同名 profile 时直接报冲突；不能静默同名覆盖。
- 后续 turn 不提供环境/权限/配置重写字段时，已查入口不会主动重载命名 profile。此局部结论不等于整个线程生命周期及全部动态工具授权路径已证明不变。
- 因此“响应不含完整图”本身不足以判定无解。若 Host 能证明命名图唯一、所有扩张均被排除或明确纳入允许契约、所有 fallback 都可由实际身份识别且 turn 不改变权限，实际 ID 可以成为屏障的一部分。

## 当前的具体反例

**B1：普通配置递归合并保留额外 grant。** ConfigLayerStack::effective_config 按层 merge_toml_values；该函数对 table/table 递归合并，只更新 overlay 列出的键。CLI inline table 在 SessionFlags 层内部替换，不会清除低层普通配置的同名表额外键。假设普通配置的 researchos-readonly.filesystem 包含某个额外合成绝对路径的 read/write，Host 固定 root deny/minimal read/workspace read inline table 没列这个键，合并后该键仍存在。workspace_roots 同样可能残留额外根。profile 仍叫 researchos-readonly，extends 可以仍为空，不产生 managed fallback warning。这里是假设的纯配置反例，没有读取或修改实际用户配置。

**B2：Native 追加读取根可保留原 ID。** config/mod.rs 在处理 fallback 后，根据 active arg0 helper 目录及 MemoryTool/use_memories 追加读取根；protocol 的 with_additional_readable_roots 对原不可读路径插入 Read。随后构造 PermissionProfileState 时仍传入 active_permission_profile。故“所有权限变宽都会清 ID”这个不变量不成立。这些 Native 运行时目录是否属于产品已允许的 Native context 需要明确契约，不能误称仅 source+minimal；不能为通过测试新增授权。仅关闭 memory 也不自动排除 arg0 helper。

**B3：profile 继承也用递归合并。** 用户层未被覆盖的 extends 与父 profile 键可残留。仅核对 id/extends 或固定三个子表，没有证明完整有效图与请求相同。

## 候选屏障的最小条件

1. 保持 Host 原生 authority、固定 MXC、原 Job、固定二进制/argv/environment 和独占 stdio 连接。renderer/用户 JSON 不能签发 seal。
2. 在源码层证明如何消除 B1/B3 或取得同线程、只含权限的有效图并做严格 subset 比较；禁止用 broad config/read 获取秘密。随机新 profile ID 只能降低碰撞概率，不能代替不变量证明。强制配置重置技巧若无官方确定语义，不作为修复。
3. 明确 B2 的目录语义及控制路径；若接受既有 Native context 例外，seal 必须准确记载。不能把未确认范围标成 source-only。
4. 新鲜 thread/start，禁止 resume/fork、动态外部客户端与权限重配；核验实际 ID、cwd、runtime workspace roots 和安全相关响应。需继续审查所有配置变更/默认环境/工具额外权限路径，不能把本次局部入口核对当完整证明。
5. 显式 settings 更新如采用，应等实际更新事件再核验；首个 turn 不传任何环境、sandbox、permissions 或 config 重配。把 permissions 塞进首个 turn 会再次加载配置，且模型开始前 Host 未必有检查该次完整结果的停顿点，不能仅凭其拒绝一种 warning 认定足够。
6. 可行路径独立源码审查及无模型协议验证完成前，actual_mode_permission_verified=false。当前 exec --json 没有 Host 可在首个模型 turn 前确认权限的 ACK 闸门，stderr 观察后 kill 不是闸门。

## 固定版本公开证据

下列行号按原始文件物理行计数；web 展示可能折叠空行。tag rust-v0.166.0 经 GitHub ref/tag 元数据指向 commit 6ff1e1ca3b30fc8b914720681fcf5fe62e95f856。版本标签不是可复现二进制构建证明。

- [thread_processor.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/thread_processor.rs#L1667)：创建后 snapshot 与响应。
- [turn_processor.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/turn_processor.rs#L838)：显式权限重载及 warning 拒绝；639 起接受 turn。
- [config_manager.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/config_manager.rs#L622)：保存的 SessionFlags 与当前来源重新加载。
- [state.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/config/src/state.rs#L599)、[merge.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/config/src/merge.rs#L79)、[overrides.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/config/src/overrides.rs#L61)：B1。
- [permissions_toml.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/config/src/permissions_toml.rs#L158)：B3。
- [config/mod.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/mod.rs#L4417)、[protocol/permissions.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/protocol/src/permissions.rs#L1346)：B2。
- [resolved_permission_profile.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/resolved_permission_profile.rs)：有效权限和 active ID 并存，约束校验不等于与原命名图完全相等。

已与资源架构 agent 独立交叉核对 B1/B2，双方结论一致。不增加已有诊断计数；由 Root 统一登记 origin。

