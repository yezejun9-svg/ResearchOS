# Qualification 拒绝的独立只读诊断

结论：原请求 `1b4a119026c64f0347984bbc69862763` 已过期且未消费。当前证据支持 Root 正常重开同一包、保留原数据与已保存配置，然后准备一个新请求；**恢复尝试不以源码修复为前提**。这不是对下一次资格运行成功的承诺，也不能重发原请求。

## 已确认事实

- 两份已固定 observer 与本轮只读 SQLite 快照一致：session revision 4、writer epoch 2、writer `desktop-shell`，原 coding `c671505` 保持 `CODING_CONFIGURED`，model ref 为 `mc-3f9329b391eaca14d82e7c4d3b9b6f34`。本轮没有改动配置。
- 请求消费表无原 request 行；该 runtime 无 qualification Run；Task 为 DRAFT、active_run_id 为 null。全库未结算 Run、最新未决 effect、未决 dispatch、managed qualification 持久化围栏计数均为 0。这个结论不代表所有 Host 行政副作用都没有发生，也不证明 verifier 从未启动。
- 弹窗实际接受时间为 19:31:25.969Z。写租约直到 19:31:51.8266886Z，尚余 **25.8576886 秒**，所以“接受确认前租约已经过期”不符合记录。
- 原请求仅有效至 19:31:28.7383996Z，接受时只剩 **2.7693996 秒**。19:32:13 的 observer 及后续原 STATUS 均显示过期未消费。

## 原因界限

实际 Core `a7ec7ebf` 会在 LoadLocalConfirmation、Host ValidateLocalQualification、beginManagedLocalQualification 及最终 claim 完成后检查原始 deadline。Host 校验身份、启动 verifier 和记录 provenance 位于最终 claim 之前。跨过剩余不足 3 秒的期限，是有依据的优先推断。

但 private ERROR 原帧没有留存。Desktop `c8b7adab` 将非 RESULT 笼统映射为 `CONFIRM_REJECTED_CHECK_STATUS`；Host 原错误消息只存在于 private reply。后续 STATUS 的 EXPIRED 仅证明读取时已过期，不会反推出原拒绝原因。因此不能宣称捕获了 STALE_INPUT、LEASE_EXPIRED、某个 verifier 错误，或精确失败时刻；其他 Host、配置、工作区、verifier、预算门仍是未排除的可能原因。

## 为什么当前页面不能重新准备

Main 在发送 CONFIRM 前把 `confirmSent` 置 true；STATUS 只会把它置 true，不会在 `consumed=false` 时清除。`canRetireExpiredIntent` 必须满足 `!confirmSent`。因此原 STATUS 已明确 EXPIRED 后，当前 Main 仍保留单次发送状态并禁用重新准备。这与本轮观察一致。

新 Main 实例的 `intent` 初始为 null；Core 新 PREPARE 只在当前身份、配置和 DRAFT task 等条件通过后创建新 ID 与新 60 秒期限。过期未消费记录不会自动排队执行。持久化已消费/未决 Run 的围栏仍由 Core 从数据库恢复，不因重启消失。当前只读计数没有这种未决工作，所以正常重开后新准备是合法恢复路径。

## Root 后续范围

正常退出并重开已接受包与原 data location，打开原会话、核对保存的新 model ref，再取得当前写入权；准备一个全新的 qualification request，并在充足有效期内只确认该新请求一次。保留旧请求和失败历史。不要重发 `1b4a119`，不要重复已提交的 coding `c671505`，不要改数据库、旧期限或原消费记录。

源码可以另做 UX 改善：在权威 STATUS 证明 EXPIRED 且未消费时允许明确准备新请求、展示剩余期限或保留受限错误信息；这些不是此次恢复的必要补丁。本轮没有实现或测试这些改动，也未重新验证完整当前 admission 或 provider 可用性。

证据：`live-readonly-observation.json`、`live-readonly-global-idle.json`、`historical-safe-fields.json`、`timeline.json`、`raw/` 和固定版本 `source/`。所有数据库连接使用 URI mode=ro、PRAGMA query_only=ON、BEGIN/ROLLBACK；未输出 owner token/credential。GUI/API/CONFIRM/新请求/模型调用/DB 写入均为 0，正式验收增量 0。源码行号索引见 FINAL-report.json。
