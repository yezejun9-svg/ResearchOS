# 资格准备上下文干扰诊断

根因是 Desktop IPC 的只读呈现请求互相覆盖。后台 `session.events` 每 1200 ms 递增与 `host.status`、`session.get` 共用的序号；即使主机、会话、写入权和配置未变，较早请求也会在 `ipc.js:175` 返回 `STALE_RESPONSE`。资格准备在 `main.js:216-221` 将主机状态未完成统一映射为 `HOST_OR_CONTEXT_CHANGED`。

实际原始 SQLite 日志中，13:56:09.573 的 `session.get` 和 13:56:10.985 的 `host.status` 都是 `COMPLETED`。会话 revision 1、writer epoch 1、model ref、host instance 和 Core build 保持一致；私有资格操作、Run、dispatch、resource effect 均为 0。实际 main 内存中的 ticket 没有采集，不能冒充直接内存观测。机制由未改动的实际发布源码与绑定 validator 的独立公共夹具确定复现：单独 prepare 成功；仅加入一个无关后台事件读取，ticket 2 被 ticket 3 覆盖，prepare 报同一错误。

最小建议范围是 `apps/desktop/main/lib/ipc.js` 与 `tests/ui/desktop/http-wire-boundary.test.mjs`：给互不相关的只读呈现分配独立竞争域，保留同域旧读取抑制、真实上下文和 native origin 校验；写命令生命周期、重放屏障、原请求终态恢复不得改变。主机/会话/写入权的 ABA 变化仍必须失败。只调整错误文案或停止后台轮询不能作为修复接受。

诊断 1、2 的 vm 跨 realm 夹具错误，及诊断 3 的 eventSequence 断言错误全部保留；诊断 4 两场景完成。全程未点击生产 GUI、未向生产主机新增请求、未调用模型或产品工具、未改 Source/Canon、未重置任何计数。正式用例增量 0。
