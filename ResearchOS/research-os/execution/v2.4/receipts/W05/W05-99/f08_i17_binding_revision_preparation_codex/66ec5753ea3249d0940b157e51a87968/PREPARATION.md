# I17 R01/R02 最小修订源码准备

新候选只恢复 v4 test 的原 LF，并向原向量清单追加非作者计划中的五个 source 事实反例。28 个旧 Test 和另 17 个 driver Test 的原始字节 body 完全相同；I18 整个 body、v3 生产 source、私有 domain harness、修好的 I17 driver 断言及 DDL34 原样复用。

R02 的五个反例保持 INTEGER mode5、合法 commit.insert/journal.update action 与 source34 mask/key/type 形状。分别删除一条 ADMITTED pin、一条 FINAL member，仅改 control CONFIRMED→RECONCILING、保留 header 内 expected_revision 7→8、保留 journal timestamp。每个坏向量逆向恢复一个事实即复原完整 baseline raw 字节，原因定位见 source-fact-cases.json 及 static-byte-audit.json。预期是真实 callback nil+F08_ORIGINAL_BINDING、SQLite primary1、失败 INSERT 不增行，全部 SOURCE_INFERENCE_NOT_RUN；未执行目标 callback 或 SQL。

原 109 项向量字节前缀及 100 项 dispatch controls 不变，新总数114。四条 pretransition 序列仍24/24/26/26。八组 whole forward/inverse 逐字节闭合；新输出 MF 自排除。

本包是作者的源码准备，未自签接受。独立复审、实际 Go producer/编译、v5 native source 排序与 typeof-before-CAST、sameTxn parent/member/pin/control/solejournal、SQL24/22-23 rollback、初始 auth/current authority、mode3、ordinary native/SDK、完整历史/backup、合法大响应 solejournal completion/replay 均 FATAL_OPEN。需新 Root source/resource lease 和非作者复审后才能做后续真实验证。

实际元数据 prepare/audit Python 与 enclosing 工具均0；seal 退出只由本次外层工具结果证明，sealed handoff 内为 NULL。本轮新出现一次只读 rg 不存在 specs 目录错误，outer1/nativeNULL；元数据检查另出现三次脚本自身失败，均 outer/native1，原脚本与日志保留；修正 root manifest 排除与 LF 分隔后使用新脚本字节、新日志，已写出的准备文件只读逐字节复用。BLOB 次数按实际 valid/corrupt 参数重算，原失败输入未重跑，旧 origins 不重计。所有目标测试 NOT_RUN；Main/canonical/module/cache/旧 sealed receipt/失败计数无写入。封存后 STOPPED。
