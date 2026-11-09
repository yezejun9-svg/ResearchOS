revision-02 的 SUP-P1-001 已在冻结源码与纯 mock 层面修复，足够支持 Root 另立一次 metadata-only D scope 与新 checkpoint。本报告不签发 PASS，不授权当前真实启动；旧 v1 继续拒绝。

process=None、factory赋值和首次wait现在处于同一保护区。独立动态 line128与赋值到首次wait之间全部5个实际opcode（236/238/258/268/270）的取消均未逃逸：同一fake对象、kill1、wait5、UNKNOWN，晚RESULT不读取。15条作者mock、8条独立Dscope/CP/消费顺序测试、1条全部opcode扫描，共24条普通断言及py_compile，实际19b845 exit0。真实Popen/controller/Native backend/模型/GPU/HTTP为0。

全局ATTEMPT仍为原 supervisor/attempt-01，revision不增加次数；R4 exe/scope/run-01/43861不变。预启动核精确D Root scope/current checkpoint project/revision/hash及源pins；exclusive mkdir和fsync后的CONSUMED先于Popen。实际模板无效，Root须在本次审查后另写新授权和新CP，立即核对后才考虑唯一一次调用。

R4-P2-001仍在：日志持锁磁盘Write可令R4 main最后exceeded()和RESULT挂起。wrapper active-child期间不读日志/RESULT、哈希或Sync，独立wait180，异常后只同原始Popen handle kill1+wait5。未知、超时、缺RESULT/receipt或退出未确认均为UNKNOWN/inconclusive，先保留读回，禁止自动重跑。完整reported proof也只待Root review，不是资源资格或正式验收。

新ROOT为revision02源/manifest/scope目录，已有cwd=str(ROOT)也指向该C目录；R4内部native cwd/profile/run未变。掉电、外部摧毁supervisor、cleanup中反复异步中断、不返回native OS调用及postterminal报告I/O仍是明确限制。

首批独立harness因沿用旧v1 line129探针而exit1（该行在v2是except，没有正常路径line事件）；原script/log/checks/pycs保留。其24条普通断言及5个opcode已通过，另存attempt-02动态line探针后得上述终态0，不能称为作者源失败或抹掉。报告装配中一次JS结果包装解析错误发生在任何nested tool之前，276a08读回证实report不存在/manifest未变，随后修正，亦已记录。

最终读回新13/13、旧v1 16/16、R4 22/22、旧76/76全部一致；旧拒绝报告、反例与失败源/日志未变。全局attempt-01、revision本地attempt-01、R4 run-01均不存在。D/Main/CP写入0，正式进度0/42。详见source-review.json、final-pins.json、attempt-02/offline-checks.json与reviewer-diagnostics.json。

