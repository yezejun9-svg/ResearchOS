# A21 restored21 receipt v2 独立 Source 复核

结论：SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION。原 R21-RECEIPT-01 已在 Source 层修复。本轮没有新增 P1/P2；不构成 runtime、formal 或执行授权。

检查输入为精确v2 HDF/MF、旧v1 Source与原85项独审。五个镜像的完整旧/新opcode字节均可还原；独立重新构造三份变更文件的完整字节并反向还原，backup.go仅新增private Object字段与发布前验证分支，handler仅调整独立阶段证据交付时机并加入已审查验证函数，test仅扩展原测试。backup_upgrade.go和CLI main.go全部字节不变。SQL、旧profiles、session事务和typed-row/schema/recovery primitives不变。

证据流是Migration成功产生sessionEvidence；专用afterRecovery完成workspace、完整target schema、recovery rows、source drift、release、program与ctx检查后，设置policy.restored21SessionEvidence；restore helper将原r.Recovery交给fixed helper。Helper只接受固定Restored21SessionUpgradePlan/localUpgradeFormat，要求完整且仅有10字段，4个string类型小写sha256 hash、4个true bool、1个false bool与Go int类型0 external actions。所有校验通过后才执行唯一一次Recovery字段写入。nil Recovery、错误plan/format、缺多字段及类型不符在写入前失败。旧plan nil字段跳过新分支。

该字段是与Purpose独立的private Object，不是供调用方传入的执行回调。plan/Purpose原始构造字节、backupMAC/readBackupPolicy、完整Purpose hash比较和公共plan dispatch不变；新helper没有Purpose写入或执行外部回调。废弃的Purpose修改草稿只作为作者构造历史封存，不进入实际overlay。

发布前控制流：afterRecovery成功 -> evidence验证/写原Recovery -> unchanged backupWrite(Bytes(r)) -> rename -> return r。原handler的发布后补丁已删除，返回与磁盘报告使用同一Recovery；原测试新增完整Recovery序列化比较。Helper或afterRecovery失败会在backupWrite/rename之前返回，backupWrite失败也在rename之前返回；既有defer backupDiscard覆盖未发布stage。此处说明只适用于这些失败路径，不把所有可能的发布后行为概括为无发布保证。真实public coordinator晚期失败/no-publication控制仍OPEN。

七项invalid hook、old nil、valid证据控制写在原public-success parent内，没有新增t.Run或Test入口；9 parents/4 leaves不变，Actual=0。仅Source检查确认这些测试存在及预期，不宣称执行9项helper控制或13个Go tests。真正returned/disk一致性、故障回滚与公开发布行为待受控actual。

独立控制87项通过，69个有限精确输入在真实SourceReadGuard下保持一致，全部handles已关闭且retained=0。独立Python/outer exit0；Go检查仅词法括号平衡，未使用Go AST/parser/compiler/formatter、SQL/native/Git/API/model或consumer。未读锁写当前四canonical，未改Main/旧Source/SQL/candidate。

作者唯一新原失败4e57d0对应seal-syntax.original-tool-io.json（8072b969d9f6a2402c358555bd867848bcf8ce4716bb9f88a3be81e6b2aad60e，1820 bytes），Root已指派941。旧sealed HDF ordinal=NULL保留原样，本独审建立行政映射而不重写旧seal。本轮没有新工具失败。

真实21/22程序来源、public late failure/no-publication、22到24后续、B分支、Owner及single-writer cutover继续OPEN。formal delta=0。STOP / FINAL。

