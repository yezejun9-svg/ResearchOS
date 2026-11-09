# B01 有效金额策略只读核验

结论：默认创建语义已核实；指定存量项目的有效 Global/Project/Goal 策略保持 OPEN。

- 默认 `UNLIMITED_AMOUNT`、`cap=null`、`ACCOUNTING_ONLY`、`ALLOW_AND_RECORD`；cap 的 null 不是零金额，默认也没有独立币种。
- 已有 Global 会保留。Project 与 Goal 创建默认子政策，运行仍遵守所有父级及 Experiment 生效限制。读取缺政策返回错误，不自动补默认。
- 控制入口从 `RESEARCHOS_DATA_DIR` 或 `.local/data/researchos.sqlite` 打开业务库。默认库实际存在，2437120 B、WAL 0、无 reparse；当前 Control 是否使用它及项目 UUID 映射未证实。
- 首次只读连接 cf0dd8 返回 `unable to open database file`。原 URI 已用 `Path.as_uri()`；没有可证明的 URI 构成错误，未重试。没有执行 SQL 查询或读取任何业务/授权/密钥行。
- 旧 `$0.50 STRICT` scope 原样保留，不代表全局限额。Root 可另行准备有限 LIVE scope；该 scope 必须如实核有效策略及其他身份、资源、资格门，不以未知费用为零、不降低 C14。

唯一新工具错误已独立保存原输入/返回，outer 1、Python bridge 1、产品 native NULL。产品、source acceptance、business acceptance、42 formal 增量均 0。
