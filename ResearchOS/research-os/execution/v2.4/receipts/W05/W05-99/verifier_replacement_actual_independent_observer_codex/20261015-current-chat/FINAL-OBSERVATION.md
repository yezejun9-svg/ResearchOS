# LIMITED_ACTUAL_REGISTRATION_ACCEPTED

独立接受本次实际 verifier 注册维护操作 `86b256fde9424ebb810537650136ad29`，仅覆盖原 DataRoot 中这一次注册替换。Root 使用已审 plan `8ba3ed5d6a1cc467b2e8539d3c90ff710c3038b913aea8937e3e20989393cefe` 单次显式 commit，实际 control 返回 native exit 0、COMMITTED/APPLIED。本 observer 没有执行 commit、recover、startup gate CLI 或正常 Core，也没有访问私钥/credential 文件内容。

独立 fresh readonly postcommit 观察确认：88 张表全部类型化行摘要和完整 schema 摘要、schema 24、四项 census 全零、Owner/Host/service root/全部 reserved children、旧配置和 idempotency 等所有表均与 baseline/preflight 一致。主 DB/WAL raw bytes 与公开 host_state raw bytes 不变；新的公开注册 885 bytes、SHA256 `d87a7aa4233e4b274842a1430148b0010d1942ead71e333104a74b635313c7fe`，精确等于 plan.new_record_bytes，原 authority 字段保持。

actual-backup.bin 与 baseline 原注册及 plan.old_record_bytes 逐字节相同。journal 精确为七个预期文件，plan 原字节和 old/new snapshots 匹配，没有 stage/temp/orphan。真实事件名是 **PREPARED → PUBLISHING → COMMITTED**，不是 FILE_REPLACED；发布结果由 actual backup 与当前 new bytes 共同证明。三个事件的 sequence、previous、canonical hash、operation、plan digest、old/new digests、合法状态转换全部匹配；history_sequence=1 且前驱为空，与此前不存在维护 journal 一致。

实际注册、journal 根、operation 目录和七个文件均核对 current SID owner、protected single allow ACE、正确目录/文件继承标志和 FullControl mask。所有原生文件身份无 reparse，文件单硬链接，全部父路径无 reparse。fresh native PID 观察无相关 Core/Desktop/verifier，现有 coordinator.lock 独占只读打开及关闭后再次打开成功，观察者全部句柄已关闭。

SHM 严格单列：baseline→preflight 从 SHA256 `c35020473aed1b4642cd726cad727b63fff2824ad68cedd7ffb73c7cbd890479` 变为 `b295c557a95e745c5ed44fd567e712adae5be65fb11f2534d98cce37c141b783`，mtime 同步变化；preflight→postcommit 的 SHM hash/size/mtime/native identity 全部保持。旧 SHM 原字节未存，不推断具体 offset/readmark。该观察遵循原 ARCHITECTURE 第 74 行及 CP493 amendment，未将辅助文件变化隐去。业务文件写入限于注册与新 journal；父 host 目录元数据随新 journal 建立发生预期变化，其他未授权路径没有观察到元数据变化。未读取敏感文件内容，因此没有用元数据替代敏感文件逐字节证明。

此前两次 observer review 失败（发现真实 SHM 差异；Windows 分隔符 KeyError）及其脚本版本、原 scope、补充 scope 的引用均保留。没有 schema 迁移或实际业务数据迁移。此接受不涵盖正常 Desktop/Core 重开、新 qualification、provider/model 或正式用例；formal 增量 0，formal 0/42，22 父任务保持 open。
