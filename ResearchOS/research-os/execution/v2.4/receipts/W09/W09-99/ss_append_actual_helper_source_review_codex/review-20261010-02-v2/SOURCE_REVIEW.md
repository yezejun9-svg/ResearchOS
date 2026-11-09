# W09 SS append v2 增量独立审查

结论：APPROVED_SOURCE_FOR_ROOT_SS_APPEND，仅绑定 wrapper SHA 7a0faabb9dd87fb158c7520f7f44c1f629ec24821b8662ba8a958d9039f03d0d（3107 bytes）。Root可在既有授权范围内以该版本执行SS单行追加；本审查没有执行追加，也不代表正式接受完成。

v1 bf391 保持原字节。八处替换均唯一命中，逆变完整还原v1；解析得到effective Source SHA 3dc45492e15dcb82e3725002719e05144224e3a86d4b5294505580a08ceeebb1（7802 bytes）。没有执行wrapper末尾exec或任何main。

两项旧阻断已修复：

- 非SS依赖闭合：纳入precheck snapshot.files全部非SS项、owner evidence、actual_audit返回的immutable capture refs，以及v2/v1自身Source。合并保留原expected SHA，冲突拒绝，SourceGuard取得后再核批准/owner/precheck和实际audit；串行writer lock内再核current4与snapshot CAS。每文件256MB、总2GB上限按实声明。
- 原始路径语义：从固定a7cc W04 Source提取Refusal、need、sha、exclusive、path_in、atomic_state、writer_lock七个定义，包含装饰器及PureWindowsPath/hashlib依赖。env不再注入较弱同名替代函数，共用原transition-writer.lock。

只执行十项新增纯metadata控制：依赖分组闭合、精确SS排除、一致重复折叠、冲突hash拒绝、其他分组SS拒绝、expected SHA保留、容量参数、自身Source refs、guard后重核顺序和原始函数绑定。控制仅执行新增normalization片段，输入为内存构造数据；不调用文件读取、SourceGuard、writer lock、atomic_state、formal API或helper main。模拟拒绝是预期控制结果，不是实际执行失败。

沿用已通过且未重跑的v1组件：exact批准/owner/precheck绑定、真实peer原始audit、全SS CAS、旧行完整结构逆操作、原始/desired/intent归档先于替换、不自动回滚。当前SS实际内容未读取。

Root后续必须保存实际调用结果并执行真实postcommit derive/recheck。若失败，已发生的SS改变应原样记录；不得自动回写original。helper committed仍明确formal_derivation_pending，不能用Source批准替代正式结果。
