# UI recovery C26 只读源码预审

状态：PRELIMINARY，等待作者最终 source/raw freeze，不签正式 C26 PASS。没有执行 browser、测试、native、provider、private 或任何已有 helper，也没有修改产品源码、canonical、spec 或旧证据。

预审 checkout：`.local/worktrees/ui-recovery-c26`，当前 HEAD `11501378b116663a9652c82058809a7fba76553d`。`apps/web/src/api.js` / `hooks.js` 相对 `4d3654b27d0e5e8c0b33537daf626179eafe68b0` 无差异；当前 SHA-256 分别是 `f133e1817696d0a873e705a19bd42fe504793343a2e1b48a9ae651511ad0d145` / `0e564a17369cf659d65d3dfffe85db759c53cf2d60d45103c9eb1124a415ef5c`。五次注册回执中的这两个产品文件 hash 均相同；最终提交与完整源清单待冻结后核对。

## 源码追踪

全部产品调用者为 App (`main.jsx:96-99`) → `useProjectEvents` (`hooks.js:36`) → `api.stream` (`api.js:64`)。项目 route 或 token 改变会清理旧 effect；`useQueries` 接受 refresh 变化，使用独立 abort，旧 scope 数据不向新项目暴露。`screens.jsx` 的各查询调用和 App 的共享查询接收同一 `events.refresh`；页面连接提示与 lastSync 来自该 hook。

| 边界 | 源码观察 | 预审结论 |
| --- | --- | --- |
| 45 秒无字节 | api 在 fetch 前创建 watchdog，每秒比较 wall clock，任何收到的 chunk 更新 lastActivity；原 signal 与 stale signal 合并，支持无 response headers 的挂起 | 逻辑成立；45 秒阈值加调度延迟，不是浏览器暂停期间仍可强制执行的实时保证 |
| heartbeat/lastSync | 注释帧只续传输 activity，不发业务 event；onOpen 不再更新 lastSync；仅 snapshot 和按序 event 更新时间 | 逻辑成立；重连 onOpen 可触发一次刷新，但每个 heartbeat 不会触发查询 |
| 恢复入口 | 每 5 秒 tick 的间隔 >20 秒、visibility=visible、pageshow.persisted、document resume 都使 sequence=null 并 abort 当前 transport | 下次 loop 先重新取 snapshot；源码未发现新增阻断缺陷，实际停顿尚缺有效运行证据 |
| snapshot 与迟到 callback | reset 使用当前 transport signal，await 返回后再检查；event/onOpen 闭包捕获 connection 而非易变 transport；read 后先检查 streamSignal.aborted 再解析 bytes | 中止旧 snapshot/reader 后的结果不会提升新连接 sequence/lastSync |
| 水位 | 外项目、空 ID、重复、非安全整数、旧 sequence 拒绝；非连续 sequence 触发 EVENT_GAP；410/gap/stale 归零后 snapshot | 正常重连保留旧水位，明确过期或恢复才归零；与原策略一致 |
| 取消与卸载 | effect controller 中止当前 transport；finally 去掉 abort listener；api finally 清 interval、cancel reader、releaseLock；恢复 timer 与 DOM listeners 在 cleanup 移除 | 正常浏览器 fetch/reader 取消链成立；此预审未实际运行卸载测试 |

没有新增阻断产品缺陷的源码证据。上述是静态检查结论，不代替运行证明。

## 现有公开运行记录

三个 whole-recovery run 均为 FAIL / exit 1：`2cb59b38-ea80-4964-b29a-147d5f29ea3e`、`809d1cb5-0dd6-4865-9ed5-be67c58a5718`、`2796e4df-dd2d-43a3-ba60-2989d2e605d4`。第二个 run 的 child `78b668c25d2c41d599c1cca1d8541eb2` 记录前 8 项完成；其中 idle 47.009 秒期间 opens=1、queries=28 不变，heartbeat 增加 3，业务进度不变。event recovery 记录 Last-Event-ID 95→96→96，reader opened=2/cancelled=1/released=1。只能按最终相同产品字节逐项复用，不能把整例改为 PASS。

特别限制：前 8 项中的第 5 项名称包含 actual Chromium freeze，但 `tests/ui/contract_cases.py:223-234` 只请求 frozen/active 并检查服务水位 94→95。没有证明 timer 停止或 freeze/resume 事件发生，因此只可记为“CDP 请求后水位追平”，不能证明浏览器确实冻结，更不能证明物理 OS sleep。

两个 freshness run 均为 FAIL / exit 1：`27792778-5369-41da-91a4-268decbe3530` 与 `6f7aa1e2-eb3b-4555-b727-6e60045c5a7d`。已完成的静默流检查各记录 45,009 ms 后 abort，lastSync 年龄分别 46,220 / 46,229 ms，真实服务水位 1→2，aborted=1/lateBytes=1。该分支是显式注入 silent ReadableStream；不是 OS 网络故障证据。它的迟到帧是外项目，无法单独隔离证明 abort fence；源码提供额外 fence 依据，同项目迟到帧的后续恢复场景尚未完成。

第二次 freshness child `a1cf4f7592fe4cf387c46c929de845a1` 保存了 resume_observation。22 秒 frozen 请求期间新增约每 5 秒一个 tick，lifecycle 数组仍为空且 visible；恢复请求后再等 15 秒，aborted 仍为 1。总观察约 37 秒尚未达到 45 秒无字节阈值，又没有 >20 秒 tick 停顿。因此该 timeout 证明此次 fixture 未建立目标 freeze 前提，不证明产品恢复缺陷。不能把 CDP 命令成功当实际 freeze，也不能把失败整例提升为 PASS。

待最终 source/raw freeze 后，仅做字节、原始回执与逐项范围映射核对，输出 final review 和 SHA 清单；不额外运行测试。
