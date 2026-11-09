# Retained fixture cleanup context

状态：SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL。仅修改新 namespace 下一个 candidate harness test 文件。

原 T10 在 20 分钟主 context 到期后进入 cleanup，仍用该过期 context 等待 Root 的 specific fixture release，导致 retained.ready 写出后立即失败并进入 TempDir 清理。本次把 cleanup 等待改为从 Background 派生、最长 4 分钟的独立 context；在 t.Cleanup 开始时创建，defer cancel 保证退出时取消。调用处仍传主 context，但小 helper 使用明确忽略参数的签名，确保不继承它的 deadline/cancellation/value；测试直接覆盖这条边界。

保留主执行 20 分钟和 grant 4 分钟。当前 Go -test.timeout=25m，owned controller 上限30m；20+4小于25并留约1分钟缓冲。实际Go启动开销、主执行不响应context、hard timeout、外部termination等仍可能提前中断cleanup，不能将这4分钟视为无条件保证。清理等待本身超时仍由原 nativeHarnessWait 报失败；本次不生成 release approval，不把超时当作已检查/已释放，也不添加任何删除动作。既有TempDir最终清理行为没有被改成持久保留机制。

原九cases、程序调用、模板、SQL、主context、grantTTL、Root显式06-release-fixture.approval.json要求全部保留。原始文件为N8实际formatted Source，SHA 972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9，35845 bytes。相对于它只替换一个cleanup块、在文件尾添加一个小helper和一个纯Go Test；imports无需修改。按替换记录逆向恢复可得到整个原始文件相同字节。

纯Go测试 TestNativeHarnessCleanupReviewContext 包含四个子用例：expired-main-deadline、main-cancel-does-not-end-cleanup、cleanup-cancel-does-not-cancel-main、fresh-four-minute-deadline。它们用同步取消与deadline检查，不sleep分钟，不启动native child，不访问SQL或伪造fixture成功。

本次只运行Source Python构造、字节逆恢复、旧断言及case保留检查、词法格式预检。没有调用Go AST、gofmt、compiler或go test；不能据此称Go测试通过。后续由Root在fresh sparse worktree的43 Source组合中替换这一文件，再运行真实tagged编译和units。

断言计数事实：N8基准整体90个 t.Fatal/Error/Fail系列调用，在temp-environment helper前为85个；历史84口径并不对应这个已格式化的新基准切分。第一次构造错误地断言84，产生唯一机械失败899（outer1/SourcePython1/nativeNULL），在candidate写入前停止。失败脚本和原始完整IO保留；更正后的构造96863e exit0并保留全部90个原调用，failure计数不重置。

