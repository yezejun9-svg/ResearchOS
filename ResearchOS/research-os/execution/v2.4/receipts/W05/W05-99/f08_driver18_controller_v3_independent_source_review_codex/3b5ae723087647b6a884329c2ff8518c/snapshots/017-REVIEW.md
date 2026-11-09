结论：REQUEST_CHANGES。D18-C01 已在源码层修正；D18-I01 的子调用 timeout 传递已修正，但最后证据收尾仍可能在超过 inner3300 后返回成功。所有判断为只读源码与 Python AST 结果，controller/helper/Go/SQL 均未执行。

Important：D18-I01-TAIL，driver18_controller.v2.proposed.py:250、254、255、258。最后一次 time.monotonic() 检查发生在写 result.json、遍历 u.files(out)、pin() 哈希所有成员并写 manifest.json 之前。可达路径是：:250 检查尚未到期且 first=None；:254/:255 的 IO 成功但跨过 deadline；此后没有时钟检查，:258 只按 first 返回0。即使总时长处于3300至3600之间，未改的 outer3600 helper 也不会按 inner3300 拒绝。原 D18-I01 REQUEST 明确要求证据收尾与最终资格拒绝过期 completion，因此不能 READY_PREPARATION_ONLY。

最小修订应由原作者在新 namespace 完成：在最后一项可能阻塞的结果/manifest 操作之后、成功返回之前，再判断固定 inner_deadline；过期必须返回失败，并保留可归因的原始诊断、actual native NULL 与外层实际退出权威。不得把已经写出的 qualified 文件当作完成，不能通过依赖 outer3600 放宽 inner3300。随后重新封精确 controller/scope ref 并独立复审；本 reviewer 不修改作者包。

已确认：入口只在 try 内计算 exit_code=main()，sys.exit(exit_code) 位于 BaseException catch 外；原 ENTRY traceback/error/actual_native_exit=None/outer_raw_authority 诊断 AST 完整不变。run 的 effective_seconds=min(seconds,remaining_seconds-cleanup5)，request 的 timeout/effective_timeout 和实际 debug.run_owned 第六参数使用同一个值，requested/remaining/cleanup 事实保留；剩余不超过5秒拒绝启动。每例和最终资格之前的 deadline guard 存在，上述缺口在这些 guard 之后。

整体正向/逆向字节核验成立：8个精确替换，实际 unified diff 为5个物理 hunk；不将二者混称。除 main/入口的指定改动外，11个原函数/类 AST 不变。I16 的两个源码分支及三个阶段业务完整不变；I18 原 func_test.go SHA85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54、35317B 保持，TestDriverI18 仍调用原 TestRegisteredFunctions；I17 保持 FATAL_OPEN，仅显式 partial17 可进入17例。32/600/750/3300/3600/cleanup5、image/process caps 以及原 launcher SHAfbf9c52568678e3733a0e50300a53c2044be96afee85672d3d2bf4df78af9086、4996B 均未改。

作者 manifest 的12成员+self与30份所需实际输入重哈希并留原字节副本，前后没有漂移。UNBOUND scope 仅 controller_ref 变化，所有真实 Root registration/authority/resource/prepared/phase refs仍NULL，preparation_only=True；没有执行授权。旧I17包、Main、canonical、旧失败计数和旧cleanup拒绝保持。

本 reviewer 是 codex:/root/f08_i17_binding_impl；本 controller v1/v2 作者是 codex:/root/command_queue_impl。reviewer 曾准备独立 I17 候选，未参与本 controller 创作，I17 包不在本次审查写入范围。实际 Python 静态复核 native exit0；候选/helper native exit不存在、记录NULL。新工具失败 origins 为0，没有 mock/fake target PASS，没有正式增量或source接受。
