实际复核结论：**VERIFIED_LOCAL_COMMAND_FAILED_MXC_CAPABILITY_UNDETERMINED_NO_REPLAY**。

该 scope 的一次固定本地命令退出码为 1，未输出 MXC_OK。Native stdout 为 0 字节，stderr 完整捕获 18 字节，十六进制为 c3fcc1eed3efb7a8b2bbd5fdc8b7a1a30d0a，按 GBK 解码为“命令语法不正确。”及 CRLF。证据没有标明内部报错组件或失败阶段，不能据此判定 MXC available/unavailable、隔离初始化成功或 split-read enforcement。

原 f13 收据为 CHILD_NONZERO_STOPPED：7 个累计进程，root exit 1，Job active zero，stop proved，强制终止次数 0，errors 为空，未超时、未超限、未报告 input drift。wrapper 的两路 progress 与最终收据、原始字节及完整摘要一致。

outer/inner scope 哈希分别为 32ef862e06e3664ab2354ea1508c2ba4885cfd70e63c41d80e97f6fb20c1d466 / 51132f2e7b3ec9a9be82b881b7f5db383ed4f41a70054e6af0bccdf514785810。注册、consumed、launch plan、final result 相互绑定。11 项 outer input 中 10 项 C 文件已独立复核哈希；1 项 D 归档报告未直接读取，仅引用 controller 无漂移结果，并核对同哈希 C 原报告。8 项冻结源文件无变更。

已选择并原样复制 11 项运行收据及 5 项支持文件，共 16 项，逐项记录于 SELECTION.json。注册时的 REGISTERED_NOT_EXECUTED、预启动 consumed 状态均保留；最终结果证明本次已执行失败，不可据旧状态重放。

本次审计仅只读原证据并写新 C 审查归档，没有启动 Echo/Native/模型，没有改原失败、D 读写或模型探测。model/formal/product 增量为 0。实际调用为无模型本地固定命令；未通过独立网络/API 遥测测量内部调用。不得以本结果宣称 READY 或授权模型重试。

