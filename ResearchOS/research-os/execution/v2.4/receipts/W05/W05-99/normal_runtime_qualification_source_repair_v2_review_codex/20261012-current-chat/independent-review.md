结论：ACCEPTED_SOURCE_AND_FIXTURE_ONLY。原 P1 W05-QUALIFICATION-ROOT-REVOCATION-001 在本候选源码与独立本地夹具范围关闭。

累计20源码、7个修复差异、冻结证据及两个实际二进制构建来源匹配；独立测试38个父测试、86个子测试通过，0失败、0跳过。真实Host/Mu/AppContainer及实际verifier仅使用synthetic SSE；旧反例逐字重跑通过。权威事务在acceptance准备/提交、资格发布、purpose和后续admission重查身份链，撤销后不产生新授权或dispatch，不改历史receipt或UNKNOWN/null账目。

尚未进行实际模型资格，未完成普通Desktop producer与生命周期接线。请求文件没有expiry字段，标准JSON解码允许重复键；purpose_seconds不是请求时效。启动仍可调度其它合法READY任务，单Run max_calls=1不是整个进程只调用一次。正式与父任务接受增量均为0，NOT_PUBLISH_READY。详见final-decision.json及raw invocation/stdout/stderr。
