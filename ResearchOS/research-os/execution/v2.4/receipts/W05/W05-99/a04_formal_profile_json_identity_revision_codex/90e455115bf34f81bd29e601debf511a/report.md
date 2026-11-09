# A04 JSON 类型与当前 Run 绑定修订

SOURCE_PROPOSAL_WITH_OPEN；未采用 Main，待非作者复核。

|请求|改动|纯控结果|
|---|---|---|
|A04-BIND-R01|完整原始 response 递归按 JSON 类型比较；对象键顺序可不同，数组和数值类型严格|1/true/1.0 替换拒绝；完整合法同型记录保留|
|A04-BIND-R02|Task 的非空 active_run_id 必须是所选 Run；原始行和组合入口均校验|独审旧 Run 反例拒绝；当前 Run 与合法 nullable 终态正例保留|

26/26 有限纯 AST 控符合。四个独审误接受输入实际复用；数据库组合控明确使用回调 stub，SQL/产品/SDK 调用为 0。

第一次 AST 抽取遗漏 IDS 依赖，工具9691d9真实 outer/Python1/1、native产品NULL，已封为677一次；旧程序原件保留，无重跑。新 v2控只补依赖，候选 Source 字节未再修改。

55个公开schema定义、SessionEvent与Artifact严格Hash边界不变。四decoder、六selector最终OPEN、实际Rootproducer/原始资格、第五GLOBAL part继续OPEN；源码修订不是正式接受。
