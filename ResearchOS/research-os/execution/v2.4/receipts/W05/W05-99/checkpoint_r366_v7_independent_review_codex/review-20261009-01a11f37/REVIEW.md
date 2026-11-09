CP366/OW170 writer v1：REQUEST_CHANGES。

P1：L79-100整对象替换owner/worker，没有冻结所有非path/ref字段。纯AST内存反例证明，开启formal acceptance/Main adoption/model调用、把五个写根改到Main、让worker与owner工作目录不一致均可通过。L116-126把整块旧对象还原，所以full inverse检测不到这些越权。

基线变换保留旧923条语义和raw数组前缀，完整归档旧worker/owner且未改其他workers；非连续ordinal和错误计数能拒绝。四份Canon哈希未变。

v2需白名单8个owner字段、3个worker字段，其余逐值及key集合保持；核对实际pinned scope正文/六Source路径/五Root路径/Source与review refs。facts及manifest应由验pin且held的同一buffer解析，避免先verify后另读。当前futurefacts/Rootscope/v7Caller未提供，不能完成绑定资格。

只读Source与纯内存transform；未执行main、guard、事务helper或Canonwriter，未声称OS held。新增原始失败0。STOP。
