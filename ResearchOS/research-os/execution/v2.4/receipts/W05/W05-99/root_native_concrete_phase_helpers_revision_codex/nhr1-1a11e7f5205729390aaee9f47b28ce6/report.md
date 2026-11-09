# NHR-001 narrow Source revision

状态：SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW。只修复真实 Root API inspection.database_ref 使用裸64hex、而旧retained错误调用public RawPin plain()的问题。

新增 inspection_database_ref(ref)，严格要求且仅允许 path/sha256/bytes 三个字段；path仍由原canonical()校验，sha256必须是64位小写十六进制且不带前缀，bytes必须为非负int且拒绝bool/float。不读取数据库、不改写哈希、不把普通receipt pin转换成public RawPin。retained唯一变化是该调用替换，后续数据库存在性、TEMP范围、config/snapshot、native IDs、whole-SQL inspection、typed rows和guard条件完全保留。

plain()未改，仍要求public RawPin使用sha256:前缀。archive与calling-contract原字节复制；sign/publish、TTL、完整Source、private separation等其余所有函数/类AST相同。新helper明确单列。删除该新增函数并逆向替换一处调用，即可得到旧helper完整相同字节。

控制：把旧verify-source.py中的完整27控制代码块原样作用到新helper，结果与旧source-controls完全一致；新增13项控制，包括真实历史Root inspection database_ref裸hash接受、错误prefix/extra role/bool/float/negative size/short/uppercase hash/relative path拒绝、public RawPin正确前缀接受而裸hash/双前缀拒绝，以及提取真实API pin_raw函数生成的普通ref接受。合计40项纯Source控制通过。

历史inspection本身已精确校验 SHA 7dfe6d48b8bfb560a31ea7830a22497440e2f62a1a27a3b325b54a37038d3409 / 98591。测试只使用它的公开metadata，不打开旧SQLite。没有运行API main、生成approval、sign/publish或native/Go/SQL/Git/model；不能把Source格式控制称为真实fixture已释放。旧T10终止事实与原生命周期检查保持原义。

35项既有Source/独立审查/receipt输入前后pin一致；本轮无新增机械失败。新immutable revision未覆盖旧Source、未修改Main/canonical。非作者复审后由Root决定是否在未来fresh case实际调用。

