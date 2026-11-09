本回执是 Desktop HTTP 第一支路的作者修订提案，尚待 Cmd 非作者范围审查与 Root 登记，不是源码接受。

优先阅读 proposal.final.json、source_scope.final.json、finite_roster.expanded.json 和 implementation_order.final.json。最初 proposal.json、source_scope.json 与中途补充全部保留；final 文件明确采用 REQUEST/RESPONSE 六字段子协议。容量笔记中的初稿五字段文字由 protocol_preflight_supplement.json 及 final 版本取代，数值上限没有变。

拟修改15路径：原14路径加 v2.js 的默认配置/项目 goal.start 前置规则；不修改 API、公开 schema、SDK、锁文件、native frame、WebContinuity、preload 或用户凭据。纯 helper 复用现有完整 SchemaDoc，原始数字通过 UseNumber 与精确数学保留，不走 domain.Decode/Hash/JCS。

未来159个具名新用例覆盖原93场景，另7个原回归执行单位；全部 NOT_RUN。两个真实离屏 Electron renderer 用例验证后续精确序列化，不代表安装、真实桌面 GUI 或 NVDA 正式通过。helper 支持8MiB请求/16MiB响应，当前公开 Host 仍1MiB；合法大请求的 Host拒绝不能改写为成功。

本次106项公开输入 before/after/current 无漂移；只是静态输入快照，不是尚未产生的编译闭包。未来必须冻结完整编译器、Go包/平台变体/embed/generated/importcfg/archives、Node/Electron、React资产、实际发布目录及childexe。新工具非零次数0；历史失败及旧提案未改。
