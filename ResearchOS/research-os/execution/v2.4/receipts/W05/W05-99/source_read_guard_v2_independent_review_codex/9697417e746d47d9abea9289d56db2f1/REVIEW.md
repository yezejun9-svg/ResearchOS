# SourceReadGuard v2 独立复审

结论：**PASS_SOURCE_ONLY**。旧版 R1 的正斜杠 UNC/device preflight 缺口已关闭，未发现新增源码阻断。此结论仅覆盖独立AST检查和内存替身控制，不是整个controller READY，也不证明实际Windows sharing或cleanup。

目标Source：source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py。
SHA-256 e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85 / 11404 bytes。
Manifest 323244fa61d59d2b6ff04d67705dcc621bb7c317cfe057752761966f704cd07f / 2422 bytes。
非作者审查者：/root/w05_merge_review；作者为live_resource_lookup。

| 检查 | 独立结果 |
|---|---|
| 旧R1三个输入 | //server/share/a.py、//?/C:/guard/one.py、//./C:/guard/one.py全部在preflight拒绝，factory/open均0 |
| 扩展负例 | 共23个路径覆盖正反斜杠UNC/device、非盘符/相对路径、ADS、控制字符、dot段、重复分隔符、尾点空格、DOS设备组件；全部在API前拒绝 |
| 合法路径 | 5种本地盘符、两种分隔符、大小写、中文与空格路径均可由内存API验证，消费原已验证buffer |
| 相同pin别名 | 正反斜杠和大小写别名只打开1个句柄，按unique bytes计算cap |
| 实际句柄路径边界 | 内存返回foreign final path或UNC final path时，read前拒绝并关闭已打开句柄 |
| 差异范围 | 仅_canonical及新增_LOCAL_DRIVE/_DOS_DEVICE常量；其余AST相同，_Win32API和SourceReadGuard两个class源码文本完全相同 |

本次执行31个新增路径控制（23负例、5正例、1去重、2最终句柄路径）。旧版28项独立控制复用其固定证据，没有把它们重新计为新增测试。旧manifest所有成员重新核对，关键生命周期class逐文本相同，因此原samebuffer、per-file/total caps、部分获取失败关闭、失败句柄保留和close重试结论继续适用于未变部分。

尤其保持原结论：历史errors可以非空，但若重试已经成功，当前entries全部closed、retained_handles_count=0且closed=true，应报告当前已释放，不应把历史错误当作仍有活句柄。相反，当前retained>0或closed=false不能称为全部清理。

独立控制加载完整候选AST，但ctypes被proxy替换，默认WinDLL被禁止，所有acquire都使用内存API替身；作者pure_controls.py未执行。real_winapi_calls=0、candidate目标文件读=0、native Job=0、provider=0，Main/canonical未写。审查工具对Source的读取及本回执写入属于元数据/证据I/O。

Root仍需独立实际Windows探针，在其自有临时目标上证明持有期读允许、write/delete/replace因sharing拒绝、关闭后写允许、句柄final路径与期望相同、失败和重试清理可核对。不能向生产Source写入来“测试保护”。本模块只验证并持有文件；Root C4和Host调用方仍须证明完整tuple在任何消费者前获取，并持有到整棵Job cleanup之后。O3是本审查者另行创作并已停止写作的Source，其组合独审由command_queue_impl完成，本回执不自签O3或C4。

附录failure-origin.693.json只保存一次协作路径通知失败的完整input/result；shell/Python/native exit均NULL。它不是本Guard行为失败，也未改变已封O3。除此之外本次控制/封存命令没有新失败。

