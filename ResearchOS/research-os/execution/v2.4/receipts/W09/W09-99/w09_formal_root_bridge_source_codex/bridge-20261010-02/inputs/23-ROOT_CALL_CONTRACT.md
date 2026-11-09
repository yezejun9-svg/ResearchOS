# Bridge02：C19 当前 Source 与六条 CM40 consumer

本修订继承 bridge01 的阶段和 Root request 合同，但以下内容替换旧合同中“永远复用 C19、固定四次新 consumer”的陈述。bridge01 保持原字节，不作为本版本运行入口。此文件和 Source 都不发行执行授权。

所有涉及 proposal/activate/registered/consume/roles/assemble 的 request 新增 c19_policy，值必须明确选一：

- RUN_CURRENT_CM40：Root 已取得当前 Source21 的四组实际 Native（W09-G01、W09-G02、C19、A06）和对应独立 mode 资格后，六条现有 CM40 route 全部新消费。C19 两条是 test.research.fixture 与 test.retrieval；A06 两条是 test.retrieval 与 test.security。旧 receipt 仍是历史原件，不被改写。
- REUSE_CURRENT_SOURCE21：仅当 Main _native 的当前 Source21/raw/owned/mode 门实际通过，且两条 C19 仍是 Main 固定 CM39 历史白名单，才复用。额外提供 c19_reuse_registry_ref，内容是实际历史 roles.executor 与 route_execution_refs；Main _historical_registry 和 _route_execution_actor 必须接受原 receipt、Scope、owner、原执行时有效的 lease。桥还把旧输出的 report/tool/mode 绑定到同一当前 Native。任何失败直接停止，不自动重跑生产者、不扩展历史例外。

不提供 c19_policy、仅三个 Native、缺 C19 Native、混用不同 selector 的 report、混用两个 C19 route 的 Native bundle、旧 Source21、任意伪造旧 CM39 receipt，均不得产生 consumer 调用。

Source 修改后：原 G01/G02/A06/C19 的实际成功或失败状态保留历史，但不自动获得新 Source 资格。Main._source21 判失配时必须新版本 Native；不能拿 G01 内含 C19 测试代替 case_id=C19 的独立 Native。四个 selector 的 report 路径必须各异，同 selector 的两个 consumer 共享一组实际 report/tool，mode 仍分别绑定各 route。

Root 必须先完成新 Native producer Source 的独立审查、当前 Source21/Current4、逐 selector Root Scope/owner/worker/有限 lease 登记、实际 prepare/run/OwnedJob 与 guards 闭合，以及真实独立 postrun mode review。Bridge02 只消费这些实际证据；不实现 NF4，不替 Root 签 Scope，不制造 Final。native_inputs 始终调用既有 Main _native，不能以输入 JSON 的 status 替代。

proposal.c19_policy 和 planned_routes 是被 Root grant 绑定的登记内容。consume 必须与已登记计划完全相同，禁止登记四路后静默运行六路。RUN_CURRENT_CM40 的 Scope/owner routes 为 Main 要求的命令键字符串；完整 selector 明细保留在 route_bindings。复用模式只登记另外四路，并在最终六路 role registry 中保留两条 C19 原 Scope/owner 引用。CM40 精确 pin 仍固定；不允许 CM41。

未来调用仍为：

    <locked-python> -I -S -B -X utf8 w09_root_bridge.source.py <stage> --request <absolute-json> --sha256 <sha256> --bytes <bytes>

其余内容见已封 bridge01 的 ROOT_CALL_CONTRACT.md。该继承不代表 bridge01 已被独立接受；bridge02 整体仍需独立 Source 审查。 本轮没有执行上述命令。

