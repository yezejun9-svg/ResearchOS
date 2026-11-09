两个旧 P1 已在冻结源码层面修复；本审查没有签发 PASS，也没有授权执行 controller。Root 可以另行建立一次 metadata-only 真实启动 scope，前提是使用独立审核的有界外层 wrapper，持有创建时返回的 controller 原始 handle，并将缺失、阻塞或不确定 RESULT 保留为 UNKNOWN/inconclusive，禁止自动重跑。

revision-04 的 PREPARED15 项与 SOURCE7 项共22条 pins 全部一致；旧76条 pins、旧scope与 v1 拒绝报告均保持一致。独立纯 mock fixtures 7个顶层测试和5个子用例通过；compile-only 与 vet 都为 exit0。独立重建的10442240字节 executable SHA256 与冻结 controller 完全相同：
`332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297`。
两个 executable 都没有运行。完整记录见 [source-review.json](source-review.json)、[offline-checks.json](offline-checks.json) 和 [pure-fixtures-01.jsonl](pure-fixtures-01.jsonl)。

P1-001 的修复在 connection.go:26-90：唯一 DialContext 取得实际连接的 local/remote 四元组，要求唯一的反向服务器 ESTABLISHED PID，再由 kernel_windows.go:191-204 验证 held/live/private Job。未通过时关闭连接，HTTP transport 无法获得该连接。实际查询在 kernel_windows.go:296-326，监听端口快照不再授权请求。未知、外来、歧义、listener-only、错误 client port、query error 或取消均在 HTTP Write 前失败。

P1-002 的资源关闭路径在 lifecycle.go:75-164：唯一 owner 顺序调用 Terminate、State、限时 Poll，随后无条件 Close。kernel_windows.go:261-267 首先关闭唯一不继承的 Job handle，然后才处理其他句柄和发布 out/done。无 watchdog 持有旧 raw Job handle，无 tracker join，无 hash、日志、Sync 或 io.Copy 阻挡该资源关闭路径。此为在 Windows kernel API 正常返回假设下的策略；本次未验证原生时序。

仍有 R4-P2-001：整个 controller 的最终 cleanup/RESULT 返回不保证有界。具体路径为：

- assets_windows.go:212 锁住 boundedLog.mu，217 持锁调用磁盘 f.Write，213 的 deferred unlock 要等 Write 返回。
- assets_windows.go:241 的 io.Copy 通过该 Write 写日志，随后 Sync/Close 才发送 stream.done。
- main_windows.go:196-201 先等 owner.out，Job Close 已先于该 outcome。211-225 等两个 stream.done 到共享 cleanup deadline。
- main_windows.go:227 随后调用 stdout.exceeded()/stderr.exceeded()；assets_windows.go:234 再拿同一把 mu。若磁盘 Write 停滞，这一步可无限等待，139-145 的 RESULT deferred write 无法执行。
- startup 的 main_windows.go:264-268 has/exceeded 也可能等待该 mu；独立 owner 仍会处理自己的 native timer 并关闭私有 Job。

现有 stalled-diagnostic fixture 只阻塞一个与真实 boundedLog 无连接的 goroutine，不能证明整个 main cleanup 有界。以后若要去掉这个限制，小修应让 has/exceeded 读取不依赖持有磁盘 Write 的锁，例如把 I/O 移出状态锁或发布 atomic/immutable 状态；不得放宽 stream/drain 失败判断。源码更改后须重新冻结审查。

Root 的新 scope 必须独立于日志和 RESULT 限时等待 controller，保留 exact returned process handle 与创建身份；超时只终止该 handle 指向的本 scope controller，并在另一个明确界限内等待其退出。controller 退出会关闭其私有不继承 Job handle，触发 kill-on-close。禁止按名称、PID、端口查找后杀进程，禁止触碰预存服务。超时、未知工具结果、缺 RESULT 或无法证明退出都保留 UNKNOWN，先读回，不能自动重跑。若要声称整个 controller cleanup 自身有界，应先修 R4-P2-001。

child image hash 的删除已明确写入新 scope；本审查只接受 held identity/FILETIME/image path/private Job/live handle 的归属证明，不把它称作 child 内容资格。StageA981份资产的前置校验和证明停止后的校验仍是硬门槛。metadata、mock fixtures、构建都不代表模型/GPU 就绪或业务验收，正式进度保持0/42。

本次真实 controller、Native backend、Ollama/模型/GPU、HTTP、网络、D/Main/CP 写入均为0。run-01 未建立。仅在本独立 reviews 子目录生成报告、离线日志和 compile-only binary；临时 Go cache/tmp 已清理。审查自身的 PATH Python alias 读取失败与旧 manifest 字段误用已保存在 [reviewer-diagnostics.json](reviewer-diagnostics.json)，没有被当作成功证据；随后读回与修正核验分别完成。

